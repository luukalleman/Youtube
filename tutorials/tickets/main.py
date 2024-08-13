# ----------------------------------------
# Do imports
# ----------------------------------------
from llama_index.core.workflow import (
    Event, StartEvent, StopEvent, Workflow, step
)
from llama_index.llms.openai import OpenAI
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
import os
from dotenv import load_dotenv
import re
import requests
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

# ----------------------------------------
# Load environment variables
# ----------------------------------------
load_dotenv()

class Config:
    FRESHDESK_DOMAIN = os.getenv('FRESHDESK_DOMAIN')
    FRESHDESK_API_KEY = os.getenv('FRESHDESK_API_KEY')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    GENERAL_DATA_PATH = 'path/to/general/company/data'
    DELIVERY_DATA_PATH = 'path/to/custom/delivery/time/data'

# ----------------------------------------
# Define Custom Events
# ----------------------------------------
class QueryEvent(Event):
    query: str
    category: str

class ResponseEvent(Event):
    response: str

class OrderLookupEvent(Event):
    order_id: str

class RequestOrderIDEvent(Event):
    pass

# ----------------------------------------
# Freshdesk Client
# ----------------------------------------
class FreshdeskClient:
    def __init__(self, domain: str, api_key: str):
        self.base_url = f"https://{domain}.freshdesk.com/api/v2"
        self.api_key = api_key

    def get_ticket(self, ticket_id: int):
        url = f"{self.base_url}/tickets/{ticket_id}"
        response = requests.get(url, auth=(self.api_key, 'X'))
        if response.status_code == 200:
            return json.loads(response.content)
        else:
            raise Exception(f"Failed to fetch ticket. Status code: {response.status_code}")

    def create_note(self, ticket_id: int, body: str, private: bool = True):
        url = f"{self.base_url}/tickets/{ticket_id}/notes"
        data = {
            "body": body,
            "private": private
        }
        response = requests.post(url, auth=(self.api_key, 'X'), json=data)
        if response.status_code == 201:
            return json.loads(response.content)
        else:
            raise Exception(f"Failed to create note. Status code: {response.status_code}")

# ----------------------------------------
# Define the Workflow: CustomerServiceBot
# ----------------------------------------
class CustomerServiceBot(Workflow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.llm = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.freshdesk_client = FreshdeskClient(Config.FRESHDESK_DOMAIN, Config.FRESHDESK_API_KEY)
        
        general_documents = SimpleDirectoryReader(Config.GENERAL_DATA_PATH).load_data()
        self.general_index = VectorStoreIndex.from_documents(general_documents)
        self.general_retriever = VectorIndexRetriever(index=self.general_index)
        self.general_query_engine = RetrieverQueryEngine(retriever=self.general_retriever)
        
        delivery_documents = SimpleDirectoryReader(Config.DELIVERY_DATA_PATH).load_data()
        self.delivery_index = VectorStoreIndex.from_documents(delivery_documents)
        self.delivery_retriever = VectorIndexRetriever(index=self.delivery_index)
        self.delivery_query_engine = RetrieverQueryEngine(retriever=self.delivery_retriever)

    # ----------------------------------------
    # Step: Classify Query
    # ----------------------------------------
    @step()
    async def classify_query(self, ev: StartEvent) -> QueryEvent | OrderLookupEvent | RequestOrderIDEvent:
        user_query = ev.get('data')
        classification_prompt = f"Classify the following customer query into one of these categories: Product Information, Order Status, Return Policy, Technical Support, or Other: '{user_query}'"
        classification_response = await self.llm.acomplete(classification_prompt)
        category = classification_response.content.strip()
        
        order_id_match = re.search(r'\b(ORD\d{3})\b', user_query)
        if order_id_match:
            return OrderLookupEvent(order_id=order_id_match.group(1))
        elif category == 'Order Status':
            return RequestOrderIDEvent()
        else:
            return QueryEvent(query=user_query, category=category)

    # ----------------------------------------
    # Step: Request Order ID
    # ----------------------------------------
    @step()
    async def request_order_id(self, ev: RequestOrderIDEvent) -> ResponseEvent:
        response = "To check the status of your order, please provide your order ID."
        return ResponseEvent(response=response)

    # ----------------------------------------
    # Step: Lookup Order Information
    # ----------------------------------------
    @step()
    async def lookup_order(self, ev: OrderLookupEvent) -> ResponseEvent:
        order_id = ev.order_id
        response = self.delivery_query_engine.query(f"What is the delivery time for order {order_id}?")
        return ResponseEvent(response=str(response))

    # ----------------------------------------
    # Step: Retrieve Information
    # ----------------------------------------
    @step()
    async def retrieve_information(self, ev: QueryEvent) -> ResponseEvent:
        response = self.general_query_engine.query(ev.query)
        return ResponseEvent(response=str(response))

    # ----------------------------------------
    # Step: Generate Response
    # ----------------------------------------
    @step()
    async def generate_response(self, ev: ResponseEvent) -> ResponseEvent:
        prompt = f"Based on this information: '{ev.response}', generate a friendly and helpful customer service response:"
        response = await self.llm.acomplete(prompt)
        return ResponseEvent(response=response.content.strip())

    # ----------------------------------------
    # Step: Format Response
    # ----------------------------------------
    @step()
    async def format_response(self, ev: ResponseEvent) -> StopEvent:
        formatted_response = f"Customer Service Bot: {ev.response}"
        return StopEvent(result=formatted_response)

# ----------------------------------------
# FastAPI Setup
# ----------------------------------------
app = FastAPI()

class WebhookPayload(BaseModel):
    ticket: Dict[str, Any]

@app.post("/webhook")
async def webhook(payload: WebhookPayload):
    try:
        bot = CustomerServiceBot(timeout=120, verbose=True)
        ticket_data = payload.ticket
        query = f"Subject: {ticket_data['subject']}\nDescription: {ticket_data['description']}"
        
        result = await bot.run(data=query)
        
        # Create a note in Freshdesk with the bot's response
        bot.freshdesk_client.create_note(ticket_data['id'], body=str(result))
        
        return {"message": "Response drafted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ----------------------------------------
# Main Entry Point (for testing)
# ----------------------------------------
async def main():
    bot = CustomerServiceBot(timeout=120, verbose=True)
    while True:
        user_query = input("Customer: ")
        if user_query.lower() in ['exit', 'quit', 'bye']:
            print("Thank you for using our customer service bot. Have a great day!")
            break
        result = await bot.run(data=user_query)
        print(result)

# Running the workflow
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
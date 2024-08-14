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
import os
from tutorials.tickets.data.order_data import get_data
from bs4 import BeautifulSoup 

# Load environment variables from a .env file
load_dotenv()

FRESHDESK_DOMAIN = os.getenv('FRESHDESK_DOMAIN')
FRESHDESK_API_KEY = os.getenv('FRESHDESK_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GENERAL_DATA_PATH_TICKETS = '/Users/luukalleman/Documents/youtube/tutorials/tickets/data'

# ----------------------------------------
# Define Custom Events
# ----------------------------------------
class QueryEvent(Event):
    query: str
    category: str
    
class ResponseEvent(Event):
    response: str
    original_query: str

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
        self.llm = OpenAI(api_key=OPENAI_API_KEY)
        self.freshdesk_client = FreshdeskClient(FRESHDESK_DOMAIN, FRESHDESK_API_KEY)
        
        # Load the documents for querying
        general_documents = SimpleDirectoryReader(GENERAL_DATA_PATH_TICKETS).load_data()
        self.general_index = VectorStoreIndex.from_documents(general_documents)
        self.general_retriever = VectorIndexRetriever(index=self.general_index)
        self.general_query_engine = RetrieverQueryEngine(retriever=self.general_retriever)
        
    # ----------------------------------------
    # Step: Classify Query
    # ----------------------------------------
    @step()
    async def classify_query(self, ev: StartEvent) -> QueryEvent | OrderLookupEvent | RequestOrderIDEvent:
        user_query = ev.get('data')
        classification_prompt = f"Classify the following customer query into one of these categories: Product Information, Order Status, or Other: '{user_query}'"
        classification_response = await self.llm.acomplete(classification_prompt)
        category = str(classification_response)
        
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
        response = """Hi,

            Thank you for reaching out to us. We understand that you’re eager to know the status of your order, and we are here to assist you.

            To help us locate your order and provide you with accurate updates, could you please provide your Order ID? This will allow us to quickly retrieve the relevant details and get back to you with the latest information regarding your order.

            We appreciate your cooperation and look forward to your reply.

            Best regards,
            Luuk Alleman
            Founder
            TechWave Electronics"""
        
        # Ensure original_query is passed along
        original_query = ev.query if hasattr(ev, 'query') else "Original query missing"
        
        return ResponseEvent(response=response, original_query=original_query)
    
    # ----------------------------------------
    # Step: Lookup Order Information
    # ----------------------------------------
    @step()
    async def lookup_order(self, ev: OrderLookupEvent) -> ResponseEvent:
        order_id = ev.order_id
        df = get_data()
        order_info = df[df['order_id'] == order_id]
        if not order_info.empty:
            delivery_time = order_info.iloc[0]['delivery_time']
            response = f"""Hi,

                Thank you for your inquiry regarding your recent order with us. I’m pleased to inform you that the delivery time for your order {order_id} is currently scheduled for {delivery_time}.

                We understand how important it is for you to receive your order promptly, and we’re committed to ensuring it arrives on time. Should you have any further questions or need additional assistance, please don’t hesitate to reach out. We’re here to help!

                Thank you for choosing TechWave Electronics. We appreciate your business and look forward to serving you again in the future.

                Best regards,
                Luuk Alleman
                Founder
                TechWave Electronics"""
        else:
            response = f"""Hi,

                Thank you for your inquiry. Unfortunately, we couldn’t find any information for the order ID {order_id}. Please verify the order ID and try again.

                If you need further assistance, feel free to reach out, and we’ll be happy to help.

                Best regards,
                Luuk Alleman
                Founder
                TechWave Electronics"""
        
        # Ensure original_query is passed along
        original_query = ev.query if hasattr(ev, 'query') else "Original query missing"
        
        return ResponseEvent(response=response, original_query=original_query)
    
    # ----------------------------------------
    # Step: Retrieve Information
    # ----------------------------------------
    @step()
    async def retrieve_information(self, ev: QueryEvent) -> ResponseEvent:
        response = self.general_query_engine.query(ev.query)
        return ResponseEvent(response=str(response), original_query=ev.query)

    # ----------------------------------------
    # Step: Generate Response
    # ----------------------------------------
    @step()
    async def generate_response(self, ev: ResponseEvent) -> ResponseEvent:
        original_query = ev.original_query
        
        # Extract the customer name from the original query
        customer_name_match = re.search(r"Customer Name: ([\w\s]+)", original_query)
        customer_name = customer_name_match.group(1).strip() if customer_name_match else "Customer"

        prompt = f"""
        You are a customer service representative. Based on this original query: '{original_query}', and the following information: '{ev.response}', generate a friendly and helpful customer service response in the format of an email:
        
        Address the customer by their name: {customer_name}.
        
        Sign off the email with the following details:
        Best regards,
        Luuk Alleman
        Founder
        TechWave Electronics
        """

        response = await self.llm.acomplete(prompt)
        return ResponseEvent(response=response.content.strip(), original_query=original_query)
    
    # ----------------------------------------
    # Step: End State
    # ----------------------------------------
    @step()
    async def end_state(self, ev: ResponseEvent) -> StopEvent:
        return StopEvent(result=ev.response)
    

    # ----------------------------------------
    # Run Workflow for a Ticket
    # ----------------------------------------
    async def process_ticket(self, ticket_data: Dict[str, Any]):
        subject = ticket_data.get('subject', '')
        description = ticket_data.get('description', '')

        # Clean the description to remove HTML tags and extract text
        soup = BeautifulSoup(description, "html.parser")
        cleaned_description = soup.get_text(separator="\n").strip()

        # Attempt to extract the name using a regex
        name_match = re.search(r"(Kind regards,|Best regards,|Sincerely,|Thanks,)\s*([\w\s]+)", cleaned_description, re.IGNORECASE)
        customer_name = name_match.group(2).strip() if name_match else "Customer"

        # Combine subject and cleaned description into a single query string
        query = f"Subject: {subject}\nDescription: {cleaned_description}\nCustomer Name: {customer_name}"
        
        # Pass the cleaned original query and extracted name to the workflow
        result = await self.run(data=query)
        print(result)
        # Create a note in Freshdesk with the bot's response
        self.freshdesk_client.create_note(ticket_data['id'], body=str(result))
        
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
        await bot.process_ticket(payload.ticket)
        return {"message": "Response drafted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
                                         
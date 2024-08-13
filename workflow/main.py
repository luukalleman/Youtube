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
from data.data import get_data

# ----------------------------------------
# Load OpenAI API Key
# ----------------------------------------
load_dotenv(dotenv_path='/Users/luukalleman/Library/CloudStorage/GoogleDrive-luuk@alleman.nl/My Drive/Everyman/EverymanAI/.env')
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

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
# Define the Workflow: CustomerServiceBot
# ----------------------------------------
class CustomerServiceBot(Workflow):
    llm = OpenAI(api_key=OPENAI_API_KEY)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        documents = SimpleDirectoryReader('/Users/luukalleman/Library/CloudStorage/GoogleDrive-luuk@alleman.nl/My Drive/Everyman/EverymanAI/youtube/workflow/data').load_data()
        self.index = VectorStoreIndex.from_documents(documents)
        self.retriever = VectorIndexRetriever(index=self.index)
        self.query_engine = RetrieverQueryEngine(retriever=self.retriever)
        
    # ----------------------------------------
    # Step: Classify Query
    # ----------------------------------------
    @step()
    async def classify_query(self, ev: StartEvent) -> QueryEvent | OrderLookupEvent | RequestOrderIDEvent:
        user_query = ev.get('data')
        classification_prompt = f"Classify the following customer query into one of these categories: Product Information, Order Status, Return Policy, Technical Support, or Other: '{user_query}'"
        classification_response = str(await self.llm.acomplete(classification_prompt))
        
        # Check if the query contains an order ID
        order_id_match = re.search(r'\b(ORD\d{3})\b', user_query)
        if order_id_match:
            return OrderLookupEvent(order_id=order_id_match.group(1))
        elif 'Order Status' in classification_response:
            return RequestOrderIDEvent()
        else:
            return QueryEvent(query=user_query, category=classification_response)
        
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
        df = get_data()
        order_info = df[df['order_id'] == order_id]
        if not order_info.empty:
            delivery_time = order_info.iloc[0]['delivery_time']
            response = f"The delivery time for order {order_id} is {delivery_time}."
        else:
            response = f"I'm sorry, I couldn't find any information for order {order_id}."
        return ResponseEvent(response=response)
    
    # ----------------------------------------
    # Step: Retrieve Information
    # ----------------------------------------
    @step()
    async def retrieve_information(self, ev: QueryEvent) -> ResponseEvent:
        response = self.query_engine.query(ev.query)
        return ResponseEvent(response=str(response))
    
    # ----------------------------------------
    # Step: Format Response
    # ----------------------------------------
    @step()
    async def format_response(self, ev: ResponseEvent) -> StopEvent:
        formatted_response = f"Customer Service Bot: {ev.response}"
        return StopEvent(result=formatted_response)

    # ----------------------------------------
    # Step: Generate Response
    # ----------------------------------------
    @step()
    async def generate_response(self, ev: ResponseEvent) -> ResponseEvent:
        prompt = f"Based on this information: '{ev.response}', generate a friendly and helpful customer service response:"
        response = await self.llm.acomplete(prompt)
        response_text = response.get('choices', [{}])[0].get('text', '').strip()
        return ResponseEvent(response=response_text)
    
# ----------------------------------------
# Main Entry Point
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
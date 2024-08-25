from notion_client import Client
from models.calendar_event import CalendarEvent
from models.email_output import EmailOutput
from config.settings import CALENDAR_DATABASE_ID, EMAIL_DATABASE_ID
import os 
from datetime import datetime

notion = Client(auth=os.getenv("NOTION_API_KEY"))

def clear_notion_database(database_id: str):
    # Query all pages in the database
    query_payload = {"page_size": 100}  # Adjust page size as needed
    response = notion.databases.query(database_id=database_id, **query_payload)

    pages = response.get("results", [])
    
    # Iterate over each page and delete it
    for page in pages:
        try:
            notion.pages.update(page["id"], archived=True)
        except Exception as e:
            print(f"Failed to delete page {page['id']} from database {database_id}: {e}")
            
def add_calendar_event_to_notion(event: CalendarEvent):    
    new_page = {
        "parent": {"database_id": CALENDAR_DATABASE_ID},
        "properties": {
            "Name": {"title": [{"text": {"content": event.description}}]},  # Use 'description' here
            "Start Date": {"date": {"start": event.start_date}},
            "End Date": {"date": {"start": event.end_date}},
            "Preparation": {"rich_text": [{"text": {"content": event.preparation}}]},
            "Priority": {"select": {"name": event.priority}},  # Only save Priority
        }
    }
    try:
        notion.pages.create(**new_page)
    except Exception as e:
        print(f"Failed to add calendar event to Notion: {e}")

def add_email_to_notion(email: EmailOutput):
    try:
        # Ensure received_date is a datetime object
        if isinstance(email.received_date, str):
            email.received_date = datetime.fromisoformat(email.received_date)
    except ValueError as e:
        print(f"Error parsing received_date: {email.received_date}. Error: {e}")
        # Handle the error, for example, by using the current date and time
        email.received_date = datetime.now()
    
    new_page = {
        "parent": {"database_id": EMAIL_DATABASE_ID},
        "properties": {
            "Subject": {"title": [{"text": {"content": email.subject}}]},
            "Received Date": {"date": {"start": email.received_date.isoformat()}},
            "Labels": {"multi_select": [{"name": label} for label in email.labels]},
            "Drafted Answers": {"rich_text": [{"text": {"content": email.drafted_answer}}]},
            "Priority": {"select": {"name": email.priority}},
            "Sender": {"rich_text": [{"text": {"content": email.sender}}]},  # Add the sender's email address
            "Original Email": {"rich_text": [{"text": {"content": email.original_email}}]},  # Add the sender's email address
        }
    }
    try:
        notion.pages.create(**new_page)
    except Exception as e:
        print(f"Failed to add email to Notion: {e}")
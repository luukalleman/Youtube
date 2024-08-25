from notion_client import Client
from models.calendar_event import CalendarStructure
from models.email_output import EmailStructure
from models.generatedContent import ContentStructure

from config.settings import CALENDAR_DATABASE_ID, EMAIL_DATABASE_ID, GENERATED_CONTENT_DATABASE_ID, PAGE_ID
import os 
from datetime import datetime
import requests
from config.settings import NOTION_API_KEY

notion = Client(auth=os.getenv("NOTION_API_KEY"))

class NotionDB():
    def clear_notion_database(self, database_id: str):
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
                
    def add_calendar_event_to_notion(self, event: CalendarStructure):    
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

    def add_email_to_notion(self, email: EmailStructure):
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
            
    def add_generated_content_to_notion(self, content: ContentStructure):
        print(f"Generated content: {content.content}")
        new_page = {
            "parent": {"database_id": GENERATED_CONTENT_DATABASE_ID},
            "properties": {
                "Title": {"title": [{"text": {"content": content.title}}]},
                "Content": {"rich_text": [{"text": {"content": content.content}}]},
                "Date": {"date": {"start": content.date}},
            }
        }
        #print(f"Adding generated content like: {new_page}")
        try:
            notion.pages.create(**new_page)
            print(f"Generated content '{content.title}' added to Notion successfully.")
        except Exception as e:
            print(f"Failed to add generated content to Notion: {e}")



    def delete_callout_blocks(self, page_id: str):
        notion_api_url = f"https://api.notion.com/v1/blocks/{page_id}/children"
        headers = {
            "Authorization": f"Bearer {NOTION_API_KEY}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }

        # Fetch all blocks in the page
        response = requests.get(notion_api_url, headers=headers)
        
        if response.status_code != 200:
            print(f"Failed to retrieve blocks: {response.text}")
            return
        
        blocks = response.json().get('results', [])

        # Delete each callout block that matches the specified texts
        for block in blocks:
            if block['type'] == 'callout':
                # block_text = block['callout']['rich_text'][0]['text']['content']
                # if block_text in callout_texts:
                delete_block_url = f"https://api.notion.com/v1/blocks/{block['id']}"
                delete_response = requests.delete(delete_block_url, headers=headers)
                
                if delete_response.status_code != 200:
                    print(f"Failed to delete block {block['id']}: {delete_response.text}")


    def update_callout_with_count(self,database_id: str, page_id: str, title: str, emoji: str):
        notion_api_url = f"https://api.notion.com/v1/blocks/{page_id}/children"
        headers = {
            "Authorization": f"Bearer {NOTION_API_KEY}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"  # Ensure you use the correct API version
        }

        # Fetch the number of rows in the database
        response = requests.post(
            f"https://api.notion.com/v1/databases/{database_id}/query",  # Correct URL
            headers=headers,
            json={}  # The empty JSON will query all rows
        )
        
        if response.status_code != 200:
            print(f"Failed to query the database: {response.text}")
            return
        
        data = response.json()
        row_count = len(data.get('results', []))

        # Create the rich_text object with the count
        rich_text_content = {
            "object": "block",
            "type": "callout",
            "callout": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": f"{title}: {row_count}"
                        }
                    }
                ],
                "icon": {
                    "type": "emoji",
                    "emoji": emoji
                },
                "color": "default"
            }
        }

        # Update the callout block in Notion
        update_response = requests.patch(notion_api_url, headers=headers, json={"children": [rich_text_content]})
        
        if update_response.status_code != 200:
            print(f"Failed to update callout block in Notion: {update_response.text}")


    def update_callout_with_post(self, database_id: str, page_id: str):
        notion_api_url = f"https://api.notion.com/v1/blocks/{page_id}/children"
        headers = {
            "Authorization": f"Bearer {NOTION_API_KEY}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"  # Ensure you use the correct API version
        }

        # Fetch the rows in the database
        response = requests.post(
            f"https://api.notion.com/v1/databases/{database_id}/query",  # Correct URL
            headers=headers,
            json={}  # The empty JSON will query all rows
        )
        
        if response.status_code != 200:
            print(f"Failed to query the database: {response.text}")
            return
        
        data = response.json()
        row_count = len(data.get('results', []))

        if row_count > 0:
            # Loop through the rows and extract the content
            for row in data.get('results', []):
                content_text = row.get('properties', {}).get('Content', {}).get('rich_text', [{}])[0].get('text', {}).get('content', '')
                if content_text:
                    # Create the callout block for the content
                    callout_content = {
                        "object": "block",
                        "type": "callout",
                        "callout": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": content_text
                                    }
                                }
                            ],
                            "icon": {
                                "type": "emoji",
                                "emoji": "✍️"  # Example emoji, can be customized
                            },
                            "color": "default"
                        }
                    }

                    # Update the callout block in Notion
                    update_response = requests.patch(notion_api_url, headers=headers, json={"children": [callout_content]})
                    
                    if update_response.status_code != 200:
                        print(f"Failed to update callout block in Notion: {update_response.text}")
                    else:
                        print(f"Successfully added content callout to the page.")
        else:
            print("No content found in the Generated Content database.")
    def clear(self):
        self.clear_notion_database(CALENDAR_DATABASE_ID)
        self.clear_notion_database(EMAIL_DATABASE_ID)
        self.clear_notion_database(GENERATED_CONTENT_DATABASE_ID)
        self.delete_callout_blocks(PAGE_ID)

    def update(self):
        self.update_callout_with_count(CALENDAR_DATABASE_ID, PAGE_ID, "Today's Calendar Events", "🗓️")
        self.update_callout_with_count(EMAIL_DATABASE_ID, PAGE_ID, "Emails in Inbox", "📧")
        self.update_callout_with_post(GENERATED_CONTENT_DATABASE_ID, PAGE_ID)
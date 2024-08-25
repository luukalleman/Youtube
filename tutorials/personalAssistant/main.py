# run.py

from models.calendar_event import CalendarEvent
from models.email_output import EmailOutput
from services.notion_service import (
    add_calendar_event_to_notion, 
    add_email_to_notion, 
    clear_notion_database
)
from pipelines.google_calendar_integration import GoogleCalendarTool
from pipelines.gmail_integration import GmailTool
from openai import OpenAI
from services.count_service import update_callout_with_count, delete_specific_callout_blocks
from config.settings import CALENDAR_DATABASE_ID, EMAIL_DATABASE_ID, PAGE_ID
from services.email_service import process_email
from services.calendar_service import process_calendar

def main():
    # Clear the Notion databases before adding new entries
    clear_notion_database(CALENDAR_DATABASE_ID)
    clear_notion_database(EMAIL_DATABASE_ID)

    # Delete specific callout blocks from the page
    delete_specific_callout_blocks(PAGE_ID)

    # Process and add calendar events and emails
    process_calendar()
    process_email()

    # Create nice callout blocks with counts
    update_callout_with_count(CALENDAR_DATABASE_ID, PAGE_ID, "Today's Calendar Events", "🗓️")
    update_callout_with_count(EMAIL_DATABASE_ID, PAGE_ID, "Emails in Inbox", "📧")

if __name__ == "__main__":
    main()
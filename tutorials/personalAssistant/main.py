# run.py
import asyncio
from integrations.notion import NotionDB
from services.count_service import update_callout_with_count, delete_callout_blocks, update_callout_with_post
from config.settings import CALENDAR_DATABASE_ID, EMAIL_DATABASE_ID, GENERATED_CONTENT_DATABASE_ID, PAGE_ID
from services.email_service import process_email
from services.calendar_service import process_calendar

async def main():
    notion = NotionDB()
    notion.clear()

    # Process and add calendar events and emails
    await process_calendar()
    process_email()
    
    notion.update()


if __name__ == "__main__":
    asyncio.run(main())
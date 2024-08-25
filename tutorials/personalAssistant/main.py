# run.py
import asyncio
from services.notion_service import clear_notion_database
from services.count_service import update_callout_with_count, delete_specific_callout_blocks, update_callout_with_post
from config.settings import CALENDAR_DATABASE_ID, EMAIL_DATABASE_ID, GENERATED_CONTENT_DATABASE_ID, PAGE_ID
from services.email_service import process_email
from services.calendar_service import process_calendar

async def main():
    clear_notion_database(CALENDAR_DATABASE_ID)
    clear_notion_database(EMAIL_DATABASE_ID)
    clear_notion_database(GENERATED_CONTENT_DATABASE_ID)

    # Delete specific callout blocks from the page
    delete_specific_callout_blocks(PAGE_ID)

    # Process and add calendar events and emails
    await process_calendar()
    process_email()

    # Create nice callout blocks with counts
    update_callout_with_count(CALENDAR_DATABASE_ID, PAGE_ID, "Today's Calendar Events", "🗓️")
    update_callout_with_count(EMAIL_DATABASE_ID, PAGE_ID, "Emails in Inbox", "📧")
    update_callout_with_post(GENERATED_CONTENT_DATABASE_ID, PAGE_ID)


if __name__ == "__main__":
    asyncio.run(main())
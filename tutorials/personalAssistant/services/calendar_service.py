from models.calendar_event import CalendarEvent
from config.settings import client
from pipelines.google_calendar_integration import GoogleCalendarTool
from datetime import datetime
from services.notion_service import add_calendar_event_to_notion

personal_info = """
Luuk Alleman is an AI engineer and entrepreneur running his own company, Everyman AI. 
He focuses on client projects, content creation, product development, and networking. 
Luuk values efficiency and prefers concise, direct communication. He is open to scheduling meetings, 
especially those related to new business opportunities, product development, or content creation.
"""

def format_date(date_str):
    return datetime.fromisoformat(date_str).isoformat()

def process_calendar():
    calendar_tool = GoogleCalendarTool()
    calendar_data = calendar_tool.run()
    for event in calendar_data['today'] + calendar_data['tomorrow']:
        start_date = event['start'].get('dateTime', event['start'].get('date'))
        end_date = event['end'].get('dateTime', event['end'].get('date'))

        completion = client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": f"""You are my assistant, this is who i am {personal_info}. Extract the event information and make steps on how to achieve this."""},
                {"role": "user", "content": f"{event['summary']} starts at {start_date} and ends at {end_date}"},
            ],
            response_format=CalendarEvent,
        )
        parsed_event = completion.choices[0].message.parsed
        parsed_event.start_date = format_date(start_date)
        parsed_event.end_date = format_date(end_date)
        add_calendar_event_to_notion(parsed_event)


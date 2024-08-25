from models.calendar_event import CalendarStructure
from models.generatedContent import ContentStructure
from config.settings import client
from integrations.calendar import GoogleCalendarTool
from datetime import datetime
from integrations.notion import NotionDB
from agents.contentWriter import ContentWritingAgent

personal_info = """
Luuk Alleman is an AI engineer and entrepreneur running his own company, Everyman AI. 
He focuses on client projects, content creation, product development, and networking. 
Luuk values efficiency and prefers concise, direct communication. He is open to scheduling meetings, 
especially those related to new business opportunities, product development, or content creation.
"""

def format_date(date_str):
    return datetime.fromisoformat(date_str).isoformat()

async def process_calendar():
    calendar_tool = GoogleCalendarTool()
    calendar_data = calendar_tool.run()
    content_agent = ContentWritingAgent(timeout=120, verbose=True)  # Instantiate the content-writing agent
    notion = NotionDB()
    
    for event in calendar_data['today'] + calendar_data['tomorrow']:
        start_date = event['start'].get('dateTime', event['start'].get('date'))
        end_date = event['end'].get('dateTime', event['end'].get('date'))

        event_summary = event['summary'].lower()
        event_description = event.get('description', '').strip()
        
        # Check if the event is related to content creation
        if any(keyword in event_summary for keyword in ["post", "article", "blog", "linkedin", "medium", "content"]):
            print(f"Processing content creation event: {event['summary']}")
            print(event_description)
            
            # Use event description for content generation
            result = await content_agent.run(data=event_description)

            # Handle the agent's output correctly
            if isinstance(result, dict) and 'StopEvent' in result:
                generated_content = result['StopEvent']['result']
            else:
                generated_content = result  # If it's a plain string, use it directly
            # Modify the original calendar event
            parsed_event = CalendarStructure(
                description="Check drafted post",
                start_date=format_date(start_date),
                end_date=format_date(end_date),
                preparation="PA already drafted a version of the content that you need to post todat, please check.",
                priority="High"
            )
            notion.add_calendar_event_to_notion(parsed_event)  # Save modified event in the calendar table

            # Save the generated content to the new content table
            generated_content_entry = ContentStructure(
                title=event['summary'],
                content=generated_content,
                date=format_date(start_date)
            )
            notion.add_generated_content_to_notion(generated_content_entry)

        else:
            # Process other events normally
            completion = client.beta.chat.completions.parse(
                model="gpt-4o-2024-08-06",
                messages=[
                    {"role": "system", "content": f"""You are my assistant, this is who I am: {personal_info}. Extract the event information and make steps on how to achieve this."""},
                    {"role": "user", "content": f"{event['summary']} starts at {start_date} and ends at {end_date}"},
                ],
                response_format=CalendarStructure,
            )
            parsed_event = completion.choices[0].message.parsed
            parsed_event.start_date = format_date(start_date)
            parsed_event.end_date = format_date(end_date)
            notion.add_calendar_event_to_notion(parsed_event)
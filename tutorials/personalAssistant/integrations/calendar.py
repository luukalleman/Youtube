from googleapiclient.discovery import build
import datetime
from integrations.authenticate import authenticate_google_calendar

class GoogleCalendarTool:
    def run(self) -> dict:
        creds = authenticate_google_calendar()
        service = build('calendar', 'v3', credentials=creds)

        # List all calendars
        calendar_list = service.calendarList().list().execute()
        calendar_ids = []

        # You can specify which calendars to include
        calendar_names = ["Luuk Alleman", "Work"]

        for calendar in calendar_list['items']:
            if calendar['summary'] in calendar_names:
                calendar_ids.append(calendar['id'])

        now = datetime.datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + 'Z'
        tomorrow_start = (now + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + 'Z'
        day_after_tomorrow_start = (now + datetime.timedelta(days=2)).replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + 'Z'

        today_events = []
        tomorrow_events = []

        for calendar_id in calendar_ids:
            events_result_today = service.events().list(calendarId=calendar_id, timeMin=today_start, timeMax=tomorrow_start,
                                                        maxResults=10, singleEvents=True, orderBy='startTime').execute()
            events_result_tomorrow = service.events().list(calendarId=calendar_id, timeMin=tomorrow_start, timeMax=day_after_tomorrow_start,
                                                           maxResults=10, singleEvents=True, orderBy='startTime').execute()

            today_events.extend([{
                "summary": event.get('summary'),
                "description": event.get('description', ''),  # Fetch event description
                "start": event['start'],
                "end": event['end'],
                "calendar": calendar_id
            } for event in events_result_today.get('items', [])])

            tomorrow_events.extend([{
                "summary": event.get('summary'),
                "description": event.get('description', ''),  # Fetch event description
                "start": event['start'],
                "end": event['end'],
                "calendar": calendar_id
            } for event in events_result_tomorrow.get('items', [])])

        return {
            "today": today_events,
            "tomorrow": tomorrow_events
        }
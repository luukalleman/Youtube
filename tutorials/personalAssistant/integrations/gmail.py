from integrations.authenticate import authenticate_gmail
from googleapiclient.discovery import build
import datetime
import time

class GmailTool:
    def run(self) -> list:
        creds = authenticate_gmail()
        service = build('gmail', 'v1', credentials=creds)

        now = int(time.time() * 1000)
        one_day_ago = now - (24 * 60 * 60 * 1000)

        results = service.users().messages().list(userId='me', maxResults=10).execute()
        messages = results.get('messages', [])
        emails = []

        profile = service.users().getProfile(userId='me').execute()
        user_email = profile.get('emailAddress')

        for message in messages:
            msg = service.users().messages().get(userId='me', id=message['id']).execute()
            if 'INBOX' in msg['labelIds'] and 'CATEGORY_PROMOTIONS' not in msg['labelIds'] \
                    and 'CATEGORY_UPDATES' not in msg['labelIds'] and int(msg['internalDate']) > one_day_ago:
                headers = msg.get('payload', {}).get('headers', [])
                to_addresses = [header['value'] for header in headers if header['name'] == 'To']
                from_address = next((header['value'] for header in headers if header['name'] == 'From'), None)

                # Skip emails from "noreply" addresses
                if 'no-reply' in from_address.lower() or 'noreply' in from_address.lower():
                    continue

                if any(user_email in addr for addr in to_addresses) and from_address != user_email:
                    emails.append({
                        'snippet': msg['snippet'],
                        'labels': msg['labelIds'],
                        'date': datetime.datetime.fromtimestamp(int(msg['internalDate']) / 1000).strftime('%Y-%m-%d %H:%M:%S'),
                        'from_address': from_address
                    })
        return emails
    
tool = GmailTool()
tool.run()
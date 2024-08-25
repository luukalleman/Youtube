import os
import json
import tempfile
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

def get_google_credentials(credential_env_var):
    credentials_json = os.getenv(credential_env_var)

    if not credentials_json:
        raise ValueError(f"{credential_env_var} is not set in the environment variables.")
    
    # Parse the JSON string
    credentials_data = json.loads(credentials_json)
    
    # Write to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as temp_file:
        temp_file.write(json.dumps(credentials_data).encode('utf-8'))
        temp_file_path = temp_file.name
    
    return temp_file_path

def authenticate_google_calendar():
    SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
    creds = None

    creds_path = get_google_credentials("GOOGLE_CALENDAR_CREDENTIALS")

    if os.path.exists('calendar_token.json'):
        creds = Credentials.from_authorized_user_file('calendar_token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open('calendar_token.json', 'w') as token:
            token.write(creds.to_json())
    
    os.remove(creds_path)
    
    return creds

def authenticate_gmail():
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    creds = None

    creds_path = get_google_credentials("GOOGLE_GMAIL_CREDENTIALS")

    if os.path.exists('gmail_token.json'):
        creds = Credentials.from_authorized_user_file('gmail_token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open('gmail_token.json', 'w') as token:
            token.write(creds.to_json())

    os.remove(creds_path)
    
    return creds
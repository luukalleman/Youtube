import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

FRESHDESK_DOMAIN = os.getenv('FRESHDESK_DOMAIN')
FRESHDESK_API_KEY = os.getenv('FRESHDESK_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
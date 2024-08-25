import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Notion API setup
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
CALENDAR_DATABASE_ID = os.getenv("NOTION_CALENDAR_DATABASE_ID")
EMAIL_DATABASE_ID = os.getenv("NOTION_EMAIL_DATABASE_ID")
PAGE_ID = os.getenv("PAGE_ID")

# OpenAI client setup
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


from pydantic import BaseModel
from typing import List

class EmailOutput(BaseModel):
    subject: str
    original_email: str
    sender: str
    received_date: str
    labels: List[str]  # Allow any string for labels to avoid validation issues
    drafted_answer: str
    priority: str  # Also allow any string to ensure flexibility
from pydantic import BaseModel
from typing import List

class EmailStructure(BaseModel):
    subject: str
    original_email: str
    sender: str
    received_date: str
    labels: List[str]
    drafted_answer: str
    priority: str
from pydantic import BaseModel
from datetime import datetime
from typing import List, Literal

class CalendarEvent(BaseModel):
    description: str
    start_date: str 
    end_date: str 
    preparation: str
    priority: Literal["Low", "Medium", "High"]
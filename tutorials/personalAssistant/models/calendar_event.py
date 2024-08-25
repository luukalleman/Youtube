from pydantic import BaseModel
from typing import Literal

class CalendarStructure(BaseModel):
    description: str
    start_date: str 
    end_date: str 
    preparation: str
    priority: Literal["Low", "Medium", "High"]
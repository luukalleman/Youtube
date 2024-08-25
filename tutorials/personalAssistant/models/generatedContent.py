from pydantic import BaseModel

class ContentStructure(BaseModel):
    title: str
    content: str
    date: str 
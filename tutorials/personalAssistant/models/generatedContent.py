from pydantic import BaseModel

class GeneratedContent(BaseModel):
    title: str
    content: str
    date: str 
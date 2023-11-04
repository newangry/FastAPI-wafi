from pydantic import BaseModel
from typing import Optional
from datetime import date, time

class Chats(BaseModel):
    ID: Optional[int] = None
    Title: Optional[str] = None
    DateCreated: Optional[date] = None
    UserID: Optional[int] = None
    ChatLocation: Optional[str] = None
    Token: Optional[str] = None
    ChatId: Optional[int] = None
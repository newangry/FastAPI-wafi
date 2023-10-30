from pydantic import BaseModel
from typing import Optional
from datetime import date, time

class Bots(BaseModel):
    ID: Optional[int] = None
    UserID: Optional[int] = None
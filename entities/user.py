from pydantic import BaseModel
from typing import Optional
from datetime import date, time

class Users(BaseModel):
    ID: Optional[int] = None
    Email: Optional[str] = None
    UserType: Optional[str] = None
    Password: Optional[str] = None
    AccessToken: Optional[str] = None
    AccessTokenCounter: Optional[int] = None
    IsSuperUser: Optional[bool] = None
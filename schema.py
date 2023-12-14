from pydantic import BaseModel
from typing import List


class UserBase(BaseModel):
    username: str
    email: str
    password: str

class ClientBase(BaseModel):
    email: str
    password: str


class UserBase2(BaseModel):
    username: str
    email: str

class FileDisplay(BaseModel):
    filename: str
    content_type : str


class UserDisplay(BaseModel):
    username: str
    email: str

    class Config():
        from_attributes = True


class User(BaseModel):
    id: int
    username: str

    class Config():
        from_attributes = True





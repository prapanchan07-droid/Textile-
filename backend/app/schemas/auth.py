from typing import List
from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: str
    username: str
    full_name: str
    role: str
    role_label: str
    sections: List[str]  # weaving sections this user may open; first is the landing page


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut


class DemoAccount(BaseModel):
    username: str
    role: str
    role_label: str
    full_name: str

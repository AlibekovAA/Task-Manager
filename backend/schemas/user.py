from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from .task import TaskResponse


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100)
    secret_word: str = Field(..., min_length=3, max_length=50)
    group_id: int = Field(default=0)


class UserUpdate(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None


class UserResponse(UserBase):
    id: int
    created_at: datetime
    role: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class User(UserResponse):
    tasks: List[TaskResponse] = []
    created_tasks: List[TaskResponse] = []


class UserBlockUpdate(BaseModel):
    is_active: bool


class UserRoleUpdate(BaseModel):
    role: str

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        if value not in {"default", "admin", "pm"}:
            raise ValueError("Role must be either default, admin or pm")
        return value


class PasswordResetRequest(BaseModel):
    email: EmailStr
    secret_word: str


class PasswordReset(PasswordResetRequest):
    new_password: str = Field(..., min_length=6, max_length=100)

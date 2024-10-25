from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from typing import List


class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=1000)
    completed: bool = False
    due_date: datetime | None = None


class TaskCreate(TaskBase):
    @field_validator('due_date')
    @classmethod
    def validate_due_date(cls, v: datetime | None) -> datetime | None:
        if v is not None and v < datetime.now():
            raise ValueError('Дата и время выполнения не могут быть в прошлом')
        return v


class TaskUpdate(TaskBase):
    title: str | None = None
    description: str | None = None
    completed: bool | None = None
    due_date: datetime | None = None


class TaskStatusUpdate(BaseModel):
    completed: bool


class TaskResponse(TaskBase):
    id: int
    created_at: datetime
    user_id: int

    class Config:
        from_attributes = True


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100)


class UserUpdate(BaseModel):
    email: str | None = None
    password: str | None = None


class User(UserBase):
    id: int
    created_at: datetime
    tasks: List["TaskResponse"] = []

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str | None = None

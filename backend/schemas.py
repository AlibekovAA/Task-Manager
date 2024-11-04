from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from .logger import setup_logger

logger = setup_logger(__name__)


class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    completed: bool = False
    due_date: Optional[datetime] = None


class TaskCreate(TaskBase):
    @field_validator('due_date')
    @classmethod
    def validate_due_date(cls, v: datetime | None) -> datetime | None:
        if v is not None and v < datetime.now():
            logger.warning(f"Invalid due date: {v} is in the past")
            raise ValueError('Дата и время выполнения не могут быть в прошлом')
        logger.debug(f"Due date validation successful: {v}")
        return v


class TaskUpdate(TaskBase):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None
    due_date: Optional[datetime] = None


class TaskStatusUpdate(BaseModel):
    completed: bool


class TaskResponse(TaskBase):
    id: int
    created_at: datetime
    user_id: int
    created_by_id: int

    class Config:
        from_attributes = True


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100)
    secret_word: str = Field(..., min_length=3, max_length=50)


class UserUpdate(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None


class User(BaseModel):
    email: str
    id: int
    created_at: datetime
    role: str
    tasks: List[TaskResponse] = []
    created_tasks: List[TaskResponse] = []

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class UserBlockUpdate(BaseModel):
    is_active: bool


class UserResponse(UserBase):
    id: int
    email: str
    created_at: datetime
    role: str
    is_active: bool

    class Config:
        from_attributes = True


class UserRoleUpdate(BaseModel):
    role: str

    @field_validator('role')
    @classmethod
    def validate_role(cls, value: str) -> str:
        if value not in ['user', 'admin', 'pm']:
            raise ValueError('Role must be either user, admin or pm')
        return value


class PasswordResetRequest(BaseModel):
    email: EmailStr
    secret_word: str


class PasswordReset(BaseModel):
    email: EmailStr
    secret_word: str
    new_password: str = Field(..., min_length=6, max_length=100)

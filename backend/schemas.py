from datetime import datetime
from typing import List, Optional
from enum import IntEnum

from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict

from .logger import setup_logger

logger = setup_logger(__name__)


class TaskStatus(IntEnum):
    PROPOSED = 0
    IN_PROGRESS = 1
    COMPLETE = 2


class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    status: int = Field(default=TaskStatus.PROPOSED)
    due_date: Optional[datetime] = None
    priority: int = Field(default=3, ge=1, le=4)

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: int) -> int:
        if v not in [status.value for status in TaskStatus]:
            raise ValueError('Статус должен быть 0 (Proposed), 1 (In Progress) или 2 (Complete)')
        return v


class UserBase(BaseModel):
    email: EmailStr


class TaskCreate(TaskBase):
    user_id: Optional[int] = None

    @field_validator('due_date')
    @classmethod
    def validate_due_date(cls, v: datetime | None) -> datetime | None:
        if v and v < datetime.now():
            logger.warning(f"Invalid due date: {v} is in the past")
            raise ValueError('Дата и время выполнения не могут быть в прошлом')
        logger.debug(f"Due date validation successful: {v}")
        return v


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100)
    secret_word: str = Field(..., min_length=3, max_length=50)
    group_id: int = Field(default=0)


class TaskUpdate(TaskBase):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None
    due_date: Optional[datetime] = None


class UserUpdate(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None


class TaskStatusUpdate(BaseModel):
    completed: bool


class UserBlockUpdate(BaseModel):
    is_active: bool


class UserRoleUpdate(BaseModel):
    role: str

    @field_validator('role')
    @classmethod
    def validate_role(cls, value: str) -> str:
        if value not in {'default', 'admin', 'pm'}:
            raise ValueError('Role must be either default, admin or pm')
        return value


class TaskFileBase(BaseModel):
    filename: str
    content_type: str
    size: int


class TaskFileCreate(TaskFileBase):
    task_id: int
    data: bytes


class TaskFileResponse(TaskFileBase):
    id: int
    created_at: datetime
    task_id: int

    class Config(ConfigDict):
        from_attributes = True


class TaskResponse(TaskBase):
    id: int
    created_at: datetime
    user_id: int
    created_by_id: int
    files: List[TaskFileResponse] = []

    class Config(ConfigDict):
        from_attributes = True


class UserResponse(UserBase):
    id: int
    created_at: datetime
    role: str
    is_active: bool

    class Config(ConfigDict):
        from_attributes = True


class User(UserResponse):
    tasks: List[TaskResponse] = []
    created_tasks: List[TaskResponse] = []


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class PasswordResetRequest(BaseModel):
    email: EmailStr
    secret_word: str


class PasswordReset(PasswordResetRequest):
    new_password: str = Field(..., min_length=6, max_length=100)

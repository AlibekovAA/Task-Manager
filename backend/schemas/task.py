from datetime import datetime
from enum import IntEnum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..utils.logger import setup_logger
from .task_file import TaskFileResponse

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

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: int) -> int:
        if v not in [status.value for status in TaskStatus]:
            raise ValueError("Статус должен быть 0 (Proposed), 1 (In Progress) или 2 (Complete)")
        return v


class TaskCreate(TaskBase):
    user_id: Optional[int] = None

    @field_validator("due_date")
    @classmethod
    def validate_due_date(cls, v: datetime | None) -> datetime | None:
        if v and v < datetime.now():
            logger.warning(f"Invalid due date: {v} is in the past")
            raise ValueError("Дата и время выполнения не могут быть в прошлом")
        logger.debug(f"Due date validation successful: {v}")
        return v


class TaskUpdate(TaskBase):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[int] = None
    due_date: Optional[datetime] = None
    priority: Optional[int] = None


class TaskResponse(TaskBase):
    id: int
    created_at: datetime
    user_id: int
    created_by_id: int
    files: List[TaskFileResponse] = []

    model_config = ConfigDict(from_attributes=True)


class TaskStatusUpdate(BaseModel):
    completed: bool

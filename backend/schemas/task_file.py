from datetime import datetime

from pydantic import BaseModel, ConfigDict


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

    model_config = ConfigDict(from_attributes=True)

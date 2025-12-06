from __future__ import annotations

from sqlalchemy.orm import Session

from .. import models
from ..utils.file_utils import get_content_type, get_file_size
from .base import handle_db_operation


@handle_db_operation("create task file")
def create_task_file(db: Session, task_id: int, filename: str, file_data: bytes) -> "models.TaskFile":
    content_type = get_content_type(filename)
    file_size = get_file_size(file_data)

    db_file = models.TaskFile(
        filename=filename, content_type=content_type, data=file_data, size=file_size, task_id=task_id
    )

    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file


@handle_db_operation("get task file")
def get_task_file(db: Session, file_id: int) -> "models.TaskFile | None":
    return db.query(models.TaskFile).filter(models.TaskFile.id == file_id).first()


@handle_db_operation("get task files")
def get_task_files(db: Session, task_id: int) -> "list[models.TaskFile]":
    return db.query(models.TaskFile).filter(models.TaskFile.task_id == task_id).all()


@handle_db_operation("delete task file")
def delete_task_file(db: Session, file_id: int) -> "models.TaskFile | None":
    db_file = db.query(models.TaskFile).filter(models.TaskFile.id == file_id).first()
    if db_file:
        db.delete(db_file)
        db.commit()
    return db_file

from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from .. import models, schemas
from .base import handle_db_operation


@handle_db_operation("retrieve task")
def get_task(db: Session, task_id: int, user_id: int):
    task = (
        db.query(models.Task)
        .options(joinedload(models.Task.user), joinedload(models.Task.created_by), joinedload(models.Task.files))
        .filter(models.Task.id == task_id)
        .first()
    )

    if not task:
        return None

    user = task.user if task.user_id == user_id else db.query(models.User).filter(models.User.id == user_id).first()

    if not user:
        return None

    return task if (task.user_id == user_id or (user.role == "pm" and task.created_by_id == user_id)) else None


def get_filtered_tasks(
    db: Session, filter_field: str, filter_value: int, skip: int = 0, limit: int = 10, status: int | None = None
):
    query = (
        db.query(models.Task)
        .options(joinedload(models.Task.user), joinedload(models.Task.created_by), joinedload(models.Task.files))
        .filter(getattr(models.Task, filter_field) == filter_value)
    )

    if status is not None:
        query = query.filter(models.Task.status == status)

    return query.order_by(desc(models.Task.created_at)).offset(skip).limit(limit).all()


def get_assigned_tasks(db: Session, created_by_id: int, **kwargs):
    return get_filtered_tasks(db, "created_by_id", created_by_id, **kwargs)


def get_user_tasks(db: Session, user_id: int, **kwargs):
    return get_filtered_tasks(db, "user_id", user_id, **kwargs)


@handle_db_operation("create task")
def create_task(db: Session, task: schemas.TaskCreate, user_id: int, created_by_id: int):
    db_task = models.Task(
        title=task.title,
        description=task.description,
        priority=task.priority,
        due_date=task.due_date,
        user_id=user_id,
        created_by_id=created_by_id,
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


@handle_db_operation("update task")
def update_task(db: Session, task_id: int, user_id: int, task_update: dict):
    db_task = get_task(db, task_id, user_id)
    if db_task:
        for key, value in task_update.items():
            setattr(db_task, key, value)
        db.commit()
        db.refresh(db_task)
    return db_task


@handle_db_operation("reassign task")
def reassign_task(db: Session, task_id: int, new_user_id: int, created_by_id: int):
    db_task = (
        db.query(models.Task).filter(models.Task.id == task_id, models.Task.created_by_id == created_by_id).first()
    )

    if db_task:
        db_task.user_id = new_user_id
        db.commit()
        db.refresh(db_task)
    return db_task


def delete_assigned_task(db: Session, task_id: int, created_by_id: int):
    return delete_task_base(db, task_id, created_by_id, "created_by_id")


def delete_task(db: Session, task_id: int, user_id: int):
    task = get_task(db, task_id, user_id)
    return delete_task_base(db, task_id, user_id, "user_id") if task else None


@handle_db_operation("delete task")
def delete_task_base(db: Session, task_id: int, user_id: int, id_field: str):
    db_task = db.query(models.Task).filter(models.Task.id == task_id, getattr(models.Task, id_field) == user_id).first()

    if db_task:
        db.delete(db_task)
        db.commit()
    return db_task

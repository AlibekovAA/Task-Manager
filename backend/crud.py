from functools import wraps

from sqlalchemy.orm import Session
from sqlalchemy import desc

from . import models, schemas
from .auth import get_password_hash
from .logger import setup_logger
from backend.utils import get_file_size, get_content_type

logger = setup_logger(__name__)


def handle_db_operation(operation_name):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                if result is not None:
                    logger.info(f"Successfully {operation_name}")
                else:
                    logger.warning(f"Failed to {operation_name} - not found")
                return result
            except Exception as e:
                logger.error(f"Error during {operation_name}: {e}")
                if 'db' in kwargs:
                    kwargs['db'].rollback()
                raise
        return wrapper
    return decorator


@handle_db_operation("retrieve user")
def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


@handle_db_operation("retrieve user by email")
def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


@handle_db_operation("retrieve users")
def get_users(db: Session, skip: int = 0, limit: int = 10):
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users


@handle_db_operation("create user")
def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    db_user = models.User(
        email=user.email,
        password_hash=get_password_hash(user.password),
        secret_word=get_password_hash(user.secret_word)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@handle_db_operation("delete user")
def delete_user(db: Session, user_id: int):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user:
        db.delete(db_user)
        db.commit()
    return db_user


@handle_db_operation("update user")
def update_user(db: Session, user_id: int, user_update: schemas.UserUpdate):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user:
        update_data = user_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if key == "password":
                db_user.password_hash = get_password_hash(value)
            else:
                setattr(db_user, key, value)
        db.commit()
        db.refresh(db_user)
    return db_user


@handle_db_operation("retrieve task")
def get_task(db: Session, task_id: int, user_id: int):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    user = db.query(models.User).filter(models.User.id == user_id).first()

    if not (task and user):
        return None

    return task if (task.user_id == user_id or
                   (user.role == 'pm' and task.created_by_id == user_id)) else None


def get_filtered_tasks(db: Session, filter_field: str, filter_value: int, skip: int = 0, limit: int = 10,
                       completed: bool | None = None):
    query = db.query(models.Task).filter(getattr(models.Task, filter_field) == filter_value)

    if completed is not None:
        query = query.filter(models.Task.completed == completed)

    return query.order_by(desc(models.Task.created_at)).offset(skip).limit(limit).all()


def get_assigned_tasks(db: Session, created_by_id: int, **kwargs):
    return get_filtered_tasks(db, 'created_by_id', created_by_id, **kwargs)


def get_user_tasks(db: Session, user_id: int, **kwargs):
    return get_filtered_tasks(db, 'user_id', user_id, **kwargs)


@handle_db_operation("create task")
def create_task(db: Session, task: schemas.TaskCreate, user_id: int, created_by_id: int):
    db_task = models.Task(
        title=task.title,
        description=task.description,
        priority=task.priority,
        due_date=task.due_date,
        user_id=user_id,
        created_by_id=created_by_id
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
    db_task = db.query(models.Task).filter(
        models.Task.id == task_id,
        models.Task.created_by_id == created_by_id
    ).first()

    if db_task:
        db_task.user_id = new_user_id
        db.commit()
        db.refresh(db_task)
    return db_task


def delete_assigned_task(db: Session, task_id: int, created_by_id: int):
    return delete_task_base(db, task_id, created_by_id, 'created_by_id')


def delete_task(db: Session, task_id: int, user_id: int):
    task = get_task(db, task_id, user_id)
    return delete_task_base(db, task_id, user_id, 'user_id') if task else None


@handle_db_operation("delete task")
def delete_task_base(db: Session, task_id: int, user_id: int, id_field: str):
    db_task = db.query(models.Task).filter(
        models.Task.id == task_id,
        getattr(models.Task, id_field) == user_id
    ).first()

    if db_task:
        db.delete(db_task)
        db.commit()
    return db_task


@handle_db_operation("update user role")
def update_user_role(db: Session, user_id: int, new_role: str):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user:
        db_user.role = new_role
        db.commit()
        db.refresh(db_user)
    return db_user


@handle_db_operation("create task file")
def create_task_file(db: Session, task_id: int, filename: str, file_data: bytes) -> models.TaskFile:
    content_type = get_content_type(filename)
    file_size = get_file_size(file_data)

    db_file = models.TaskFile(
        filename=filename,
        content_type=content_type,
        data=file_data,
        size=file_size,
        task_id=task_id
    )

    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file


@handle_db_operation("get task file")
def get_task_file(db: Session, file_id: int) -> models.TaskFile:
    return db.query(models.TaskFile).filter(models.TaskFile.id == file_id).first()


@handle_db_operation("get task files")
def get_task_files(db: Session, task_id: int) -> list[models.TaskFile]:
    return db.query(models.TaskFile).filter(models.TaskFile.task_id == task_id).all()


@handle_db_operation("delete task file")
def delete_task_file(db: Session, file_id: int) -> models.TaskFile:
    db_file = db.query(models.TaskFile).filter(models.TaskFile.id == file_id).first()
    if db_file:
        db.delete(db_file)
        db.commit()
    return db_file

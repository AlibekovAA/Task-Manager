from sqlalchemy.orm import Session
from sqlalchemy import desc

from . import models
from . import schemas
from .auth import get_password_hash
from .logger import setup_logger

logger = setup_logger(__name__)


def get_user(db: Session, user_id: int):
    try:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if user:
            logger.info(f"Retrieved user with id: {user_id}")
        else:
            logger.warning(f"User not found with id: {user_id}")
        return user
    except Exception as e:
        logger.error(f"Error retrieving user {user_id}: {e}")
        raise


def get_user_by_email(db: Session, email: str):
    try:
        user = db.query(models.User).filter(models.User.email == email).first()
        if user:
            logger.info(f"Retrieved user with email: {email}")
        else:
            logger.warning(f"User not found with email: {email}")
        return user
    except Exception as e:
        logger.error(f"Error retrieving user by email {email}: {e}")
        raise


def get_users(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate):
    try:
        hashed_password = get_password_hash(user.password)
        db_user = models.User(
            email=user.email,
            password_hash=hashed_password
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        logger.info(f"Created new user with email: {user.email}")
        return db_user
    except Exception as e:
        logger.error(f"Error creating user {user.email}: {e}")
        db.rollback()
        raise


def delete_user(db: Session, user_id: int):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user:
        db.delete(db_user)
        db.commit()
        return db_user
    return None


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
    return None


def get_task(db: Session, task_id: int, user_id: int):
    return db.query(models.Task).filter(
        models.Task.id == task_id,
        models.Task.user_id == user_id
    ).first()


def get_user_tasks(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 10,
    completed: bool | None = None
):
    query = db.query(models.Task).filter(models.Task.user_id == user_id)

    if completed is not None:
        query = query.filter(models.Task.completed == completed)

    return query.order_by(desc(models.Task.created_at)).offset(skip).limit(limit).all()


def create_task(db: Session, task: schemas.TaskCreate, user_id: int):
    try:
        db_task = models.Task(
            title=task.title,
            description=task.description,
            completed=task.completed,
            due_date=task.due_date,
            user_id=user_id
        )
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        logger.info(f"Created new task '{task.title}' for user {user_id}")
        return db_task
    except Exception as e:
        logger.error(f"Error creating task for user {user_id}: {e}")
        db.rollback()
        raise


def update_task(db: Session, task_id: int, user_id: int, task_update: schemas.TaskBase):
    db_task = get_task(db, task_id, user_id)
    if db_task:
        for key, value in task_update.model_dump(exclude_unset=True).items():
            setattr(db_task, key, value)
        db.commit()
        db.refresh(db_task)
    return db_task


def delete_task(db: Session, task_id: int, user_id: int):
    db_task = get_task(db, task_id, user_id)
    if db_task:
        db.delete(db_task)
        db.commit()
        return db_task
    return None

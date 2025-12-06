from sqlalchemy.orm import Session

from .. import models, schemas
from ..services.auth_service import get_password_hash
from .base import handle_db_operation


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
        secret_word=get_password_hash(user.secret_word),
        group_id=user.group_id,
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


@handle_db_operation("update user role")
def update_user_role(db: Session, user_id: int, new_role: str):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user:
        db_user.role = new_role
        db.commit()
        db.refresh(db_user)
    return db_user

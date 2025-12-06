from typing import List

from fastapi import APIRouter, Body, HTTPException, status
from sqlalchemy.orm import joinedload

from .. import crud, models, schemas
from ..dependencies import current_user_dependency, db_dependency
from ..services import auth_service as auth
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter(prefix="/users", tags=["users"])

password_body = Body(...)


@router.post("/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: db_dependency):
    logger.info(f"Creating user with email: {user.email}")
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        logger.warning(f"Email already registered: {user.email}")
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = crud.create_user(db=db, user=user)
    logger.info(f"User created: {new_user.email}")
    return new_user


@router.get("/me/", response_model=schemas.User)
def read_users_me(current_user: current_user_dependency, db: db_dependency):
    logger.info(f"Current user: {current_user.email}, role: {current_user.role}")

    user = (
        db.query(models.User)
        .options(joinedload(models.User.tasks), joinedload(models.User.created_tasks))
        .filter(models.User.id == current_user.id)
        .first()
    )

    return {
        "email": user.email,
        "id": user.id,
        "created_at": user.created_at,
        "role": user.role,
        "is_active": user.is_active,
        "tasks": user.tasks,
        "created_tasks": user.created_tasks,
    }


@router.get("/", response_model=List[schemas.User])
def read_users(db: db_dependency, current_user: current_user_dependency, skip: int = 0, limit: int = 10):
    logger.info(f"Reading users: skip={skip}, limit={limit}")
    users = crud.get_users(db, skip=skip, limit=limit)
    logger.info(f"Found {len(users)} users")
    return users


@router.get("/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: db_dependency):
    logger.info(f"Reading user: {user_id}")
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        logger.warning(f"User not found: {user_id}")
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.put("/{user_id}", response_model=schemas.User)
def update_user(user_id: int, user_update: schemas.UserUpdate, db: db_dependency):
    logger.info(f"Updating user: {user_id}")
    db_user = crud.update_user(db, user_id=user_id, user_update=user_update)
    if db_user is None:
        logger.warning(f"User not found: {user_id}")
        raise HTTPException(status_code=404, detail="User not found")
    logger.info(f"User updated: {db_user.email}")
    return db_user


@router.delete("/{user_id}", response_model=schemas.User)
def delete_user(user_id: int, db: db_dependency):
    logger.info(f"Deleting user: {user_id}")
    db_user = crud.delete_user(db, user_id=user_id)
    if db_user is None:
        logger.warning(f"User not found: {user_id}")
        raise HTTPException(status_code=404, detail="User not found")
    logger.info(f"User deleted: {db_user.email}")
    return db_user


@router.put("/me/password")
async def change_password(current_user: current_user_dependency, db: db_dependency, body: dict = password_body):
    logger.info(f"User {current_user.email} is attempting to change password")
    current_password = body.get("current_password")
    new_password = body.get("new_password")

    if not current_password or not new_password:
        logger.warning("Current or new password not provided")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Необходимо указать текущий и новый пароль")

    if not auth.verify_password(current_password, current_user.password_hash):
        logger.warning(f"User {current_user.email} provided invalid current password")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Неверный текущий пароль")

    if current_password == new_password:
        logger.warning(f"User {current_user.email} attempted to set new password same as current")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Новый пароль должен отличаться от текущего"
        )

    if auth.verify_password(new_password, current_user.password_hash):
        logger.warning(f"User {current_user.email} attempted to set new password same as current (hashed check)")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Новый пароль должен отличаться от текущего"
        )

    user_update = schemas.UserUpdate(password=new_password)
    crud.update_user(db, current_user.id, user_update)
    logger.info(f"Password changed successfully for user: {current_user.email}")
    return {"message": "Пароль успешно изменен"}


@router.post("/me/check-password")
async def check_password(current_user: current_user_dependency, db: db_dependency, body: dict = password_body):
    password = body.get("password")
    logger.info(f"User {current_user.email} is checking password")

    if not password:
        logger.warning("Password not provided for password check")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Необходимо указать пароль")

    if not auth.verify_password(password, current_user.password_hash):
        logger.warning(f"User {current_user.email} provided invalid password")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный пароль")

    logger.info(f"User {current_user.email} password check successful")
    return {"message": "Пароль верный"}


@router.post("/verify-reset", response_model=dict)
def verify_reset_credentials(reset_request: schemas.PasswordResetRequest, db: db_dependency):
    user = crud.get_user_by_email(db, reset_request.email)
    if not user:
        logger.warning(f"Password reset attempted for non-existent email: {reset_request.email}")
        raise HTTPException(status_code=404, detail="Пользователь с таким email не найден")

    if not auth.verify_secret_word(reset_request.secret_word, user.secret_word):
        logger.warning(f"Invalid secret word provided for password reset: {reset_request.email}")
        raise HTTPException(status_code=400, detail="Неверное кодовое слово")

    logger.info(f"Password reset credentials verified for user: {reset_request.email}")
    return {"message": "Данные подтверждены"}


@router.post("/reset-password", response_model=dict)
def reset_password(reset_data: schemas.PasswordReset, db: db_dependency):
    user = crud.get_user_by_email(db, reset_data.email)
    if not user:
        logger.warning(f"Password reset attempted for non-existent email: {reset_data.email}")
        raise HTTPException(status_code=404, detail="Пользователь с таким email не найден")

    if not auth.verify_secret_word(reset_data.secret_word, user.secret_word):
        logger.warning(f"Invalid secret word provided for password reset: {reset_data.email}")
        raise HTTPException(status_code=400, detail="Неверное кодовое слово")

    hashed_password = auth.get_password_hash(reset_data.new_password)
    user.password_hash = hashed_password
    db.commit()

    logger.info(f"Password successfully reset for user: {reset_data.email}")
    return {"message": "Пароль успешно изменен"}

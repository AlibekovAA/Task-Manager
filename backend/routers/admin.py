from typing import List

from fastapi import APIRouter, HTTPException, status

from .. import crud, schemas
from ..dependencies import admin_user_dependency, db_dependency
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users/", response_model=List[schemas.UserResponse])
def list_all_users(current_user: admin_user_dependency, db: db_dependency, skip: int = 0, limit: int = 10):
    logger.info(f"Admin {current_user.email} is listing all users (skip={skip}, limit={limit})")
    users = crud.get_users(db, skip=skip, limit=limit)
    logger.info(f"Admin {current_user.email} retrieved {len(users)} users")
    return users


@router.put("/users/{user_id}/block", response_model=schemas.UserResponse)
def block_user(
    user_id: int, block_update: schemas.UserBlockUpdate, current_user: admin_user_dependency, db: db_dependency
):
    if user_id == current_user.id:
        logger.warning(f"Admin {current_user.email} attempted to block themselves")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot block yourself")

    db_user = crud.get_user(db, user_id)
    if not db_user:
        logger.error(f"User with ID {user_id} not found for admin {current_user.email}")
        raise HTTPException(status_code=404, detail="User not found")

    db_user.is_active = block_update.is_active
    db.commit()
    db.refresh(db_user)

    action = "unblocked" if block_update.is_active else "blocked"
    logger.info(f"Admin {current_user.email} {action} user {db_user.email}")

    return db_user


@router.put("/users/{user_id}/role", response_model=schemas.UserResponse)
async def change_user_role(
    user_id: int, role_update: schemas.UserRoleUpdate, current_user: admin_user_dependency, db: db_dependency
):
    logger.info(f"Admin {current_user.email} is changing role for user {user_id} to {role_update.role}")

    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Только администраторы могут изменять роли пользователей"
        )

    user = crud.get_user(db, user_id)
    if not user:
        logger.error(f"User with ID {user_id} not found for admin {current_user.email}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

    if user.role == "admin":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Невозможно изменить роль администратора")

    updated_user = crud.update_user_role(db, user_id, role_update.role)
    logger.info(f"Admin {current_user.email} changed role for user {user.email} to {role_update.role}")

    return updated_user

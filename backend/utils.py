from typing import Generator

import backend.crud as crud
import backend.schemas as schemas
from backend.database import SessionLocal
from backend.config import ADMIN_EMAIL, ADMIN_PASSWORD, ADMIN_SECRET_WORD
from backend.logger import setup_logger

logger = setup_logger(__name__)


def create_admin_user() -> None:
    db = next(get_db())
    admin = crud.get_user_by_email(db, ADMIN_EMAIL)
    if not admin:
        admin_user = schemas.UserCreate(
            email=ADMIN_EMAIL,
            password=ADMIN_PASSWORD,
            secret_word=ADMIN_SECRET_WORD
        )
        admin = crud.create_user(db, admin_user)
        admin.is_admin = True
        db.commit()
        logger.info("Admin user created successfully")
    else:
        logger.info("Admin user already exists")


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

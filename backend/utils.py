from typing import Generator

import backend.crud as crud
import backend.schemas as schemas
from backend.database import SessionLocal
from backend.config import ADMIN_EMAIL, ADMIN_PASSWORD, ADMIN_SECRET_WORD
from backend.logger import setup_logger

logger = setup_logger(__name__)


def create_admin_user() -> None:
    db = SessionLocal()
    try:
        if not crud.get_user_by_email(db, ADMIN_EMAIL):
            admin = crud.create_user(
                db=db,
                user=schemas.UserCreate(
                    email=ADMIN_EMAIL,
                    password=ADMIN_PASSWORD,
                    secret_word=ADMIN_SECRET_WORD
                )
            )
            admin.role = "admin"
            db.commit()
            logger.info("Admin user created successfully")
        else:
            logger.info("Admin user already exists")
    except Exception as e:
        logger.error("Error creating admin user: %s", e, exc_info=True)
    finally:
        db.close()


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def convert_ty_binary_file(filename: str):
    with open(filename, 'rb') as file:
        blob_data = file.read()
    return blob_data


def write_binary_to_file(data, filename: str):
    with open(filename, 'wb') as file:
        file.write(data)

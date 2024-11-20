from typing import Generator
import os
import mimetypes

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


def get_content_type(filename: str) -> str:
    content_type, _ = mimetypes.guess_type(filename)
    return content_type or 'application/octet-stream'


def get_file_size(file_data: bytes) -> int:
    return len(file_data)


def validate_file_size(file_size: int, max_size: int = 10 * 1024 * 1024) -> bool:
    return file_size <= max_size


def validate_file_type(filename: str) -> bool:
    allowed_extensions = {'.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.gif'}
    file_extension = os.path.splitext(filename)[1].lower()
    return file_extension in allowed_extensions


def sanitize_filename(filename: str) -> str:
    filename = os.path.basename(filename)
    return ''.join(c if c.isalnum() or c in '.-_' else '_' for c in filename)

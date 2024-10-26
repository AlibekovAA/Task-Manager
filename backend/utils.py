import traceback

import backend.crud as crud
import backend.schemas as schemas
from backend.database import SessionLocal
from backend.config import ADMIN_EMAIL, ADMIN_PASSWORD
from backend.logger import setup_logger

logger = setup_logger(__name__)


def create_admin_user():
    db = SessionLocal()
    try:
        logger.info(f"Trying to create admin user with email: {ADMIN_EMAIL}")

        admin = crud.get_user_by_email(db, ADMIN_EMAIL)
        if not admin:
            admin_user = schemas.UserCreate(
                email=ADMIN_EMAIL,
                password=ADMIN_PASSWORD
            )
            crud.create_user(db=db, user=admin_user)
            logger.info("Admin user created successfully")
        else:
            logger.info("Admin user already exists")
    except Exception as e:
        logger.error(f"Error creating admin user: {e}")
        logger.error(traceback.format_exc())
    finally:
        db.close()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

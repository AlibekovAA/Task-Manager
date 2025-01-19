from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import event

import logging

logger = logging.getLogger(__name__)

SQLALCHEMY_DATABASE_URL = "sqlite:///./task_manager.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def set_sqlite_timezone(dbapi_connection, connection_record):
    try:
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute('PRAGMA timezone = "+03:00"')
            logger.info("Database engine created successfully with timezone UTC+3")
        finally:
            cursor.close()
    except Exception as e:
        logger.error(f"Error setting timezone: {str(e)}")


event.listen(engine, 'connect', set_sqlite_timezone)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

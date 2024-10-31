from typing import Any

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from .logger import setup_logger

logger = setup_logger(__name__)

SQLALCHEMY_DATABASE_URL = "sqlite:///database.db"


def create_engine_with_timezone(url: str) -> Any:
    try:
        engine = create_engine(url, connect_args={"check_same_thread": False})

        def set_sqlite_timezone(dbapi_connection, connection_record) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA timezone = '+03:00';")
            cursor.close()

        event.listen(engine, 'connect', set_sqlite_timezone)
        logger.info("Database engine created successfully with timezone UTC+3")
        return engine
    except SQLAlchemyError as e:
        logger.error("Error creating database engine: %s", e, exc_info=True)
        raise


engine = create_engine_with_timezone(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

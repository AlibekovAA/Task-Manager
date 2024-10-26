from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .logger import setup_logger

logger = setup_logger(__name__)

SQLALCHEMY_DATABASE_URL = "sqlite:///database.db"

try:
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

    def set_sqlite_timezone(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA timezone = '+03:00';")
        cursor.close()

    event.listen(engine, 'connect', set_sqlite_timezone)
    logger.info("Database engine created successfully with timezone UTC+3")
except Exception as e:
    logger.error(f"Error creating database engine: {e}")
    raise

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

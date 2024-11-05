from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from email_validator import validate_email, EmailNotValidError

from .database import Base
from .logger import setup_logger

logger = setup_logger(__name__)


def now_moscow():
    return datetime.now()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    secret_word = Column(String, nullable=False)
    created_at = Column(DateTime, default=now_moscow, nullable=False)
    role = Column(String, default='default', nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan", foreign_keys="Task.user_id")
    created_tasks = relationship("Task", foreign_keys='Task.created_by_id', back_populates="created_by")

    def validate_email(self) -> bool:
        try:
            validate_email(self.email)
            logger.debug(f"Email validation successful for {self.email}")
            return True
        except EmailNotValidError as e:
            logger.warning(f"Invalid email {self.email}: {str(e)}")
            return False


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    description = Column(String, index=True)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=now_moscow, nullable=False)
    due_date = Column(DateTime, nullable=True)
    priority = Column(Integer, default=3, nullable=False)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    user = relationship("User", back_populates="tasks", foreign_keys=[user_id])
    created_by = relationship("User", back_populates="created_tasks", foreign_keys=[created_by_id])

    @classmethod
    def create_task(cls, **kwargs) -> "Task":
        try:
            task = cls(**kwargs)
            logger.info(f"Task created: {task.title} for user {task.user_id}")
            return task
        except Exception as e:
            logger.error(f"Error creating task: {e}")
            raise

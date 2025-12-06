from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from ..database import Base
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    secret_word = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    role = Column(String, default="default", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    group_id = Column(Integer, default=0, nullable=False)

    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan", foreign_keys="Task.user_id")
    created_tasks = relationship("Task", foreign_keys="Task.created_by_id", back_populates="created_by")

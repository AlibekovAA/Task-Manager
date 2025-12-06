from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from ..database import Base
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    description = Column(String, index=True)
    status = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    due_date = Column(DateTime, nullable=True)
    priority = Column(Integer, default=3, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    user = relationship("User", back_populates="tasks", foreign_keys=[user_id])
    created_by = relationship("User", back_populates="created_tasks", foreign_keys=[created_by_id])
    files = relationship("TaskFile", back_populates="task", cascade="all, delete-orphan")

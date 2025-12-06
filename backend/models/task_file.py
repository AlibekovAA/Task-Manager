from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, LargeBinary, String
from sqlalchemy.orm import relationship

from ..database import Base


class TaskFile(Base):
    __tablename__ = "task_files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    data = Column(LargeBinary, nullable=False)
    size = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, index=True)

    task = relationship("Task", back_populates="files")

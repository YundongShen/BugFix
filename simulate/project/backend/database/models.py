from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from backend.database.connection import DatabaseManager

Base = declarative_base()

class Task(DatabaseManager.Base):
    """ORM model for tasks."""
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    description = Column(String(255), nullable=False)  # Ensure 'description' column exists
    completed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<Task(id={self.id}, description='{self.description}', completed={self.completed})>"
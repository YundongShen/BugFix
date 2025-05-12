"""
This module contains the business logic for managing tasks in the to-do list application.
"""

from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, validator
from backend.modules.tasks.repository import TaskRepository
from backend.database.models import Task as TaskModel
from backend.database.connection import DatabaseManager
from uuid import uuid4
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskCreate(BaseModel):
    """Input model for creating a new task."""
    description: str

    @validator("description")
    def validate_description(cls, value):
        if not value or not isinstance(value, str) or len(value.strip()) == 0:
            raise ValueError("Task description must be a non-empty string.")
        if len(value) > 255:
            raise ValueError("Task description must not exceed 255 characters.")
        return value.strip()

class TaskResponse(BaseModel):
    """Output model for returning task details."""
    id: int
    description: str
    completed: bool
    created_at: str

class TaskService:
    """Handles business logic for task operations."""

    def __init__(self):
        self.repository = TaskRepository(db_manager=DatabaseManager())

    async def create_task(self, task_data: TaskCreate) -> TaskResponse:
        """Creates a new task and returns its details."""
        trace_id = str(uuid4())
        logger.info(f"Creating task with description: {task_data.description}. Trace ID: {trace_id}")
        try:
            new_task = await self.repository.add_task(description=task_data.description)
            if not new_task:
                logger.error(f"Failed to create task. Trace ID: {trace_id}")
                raise HTTPException(status_code=500, detail="Failed to create task due to an unknown error.")
            
            return TaskResponse(
                id=new_task.id,
                description=new_task.description,
                completed=new_task.completed,
                created_at=new_task.created_at.isoformat()
            )
        except IntegrityError as e:
            logger.error(f"Database constraint violation while creating task. Trace ID: {trace_id}. Error: {e}")
            raise HTTPException(status_code=400, detail="Failed to create task due to database constraint violation.") from e
        except ValueError as e:
            logger.error(f"Invalid input while creating task. Trace ID: {trace_id}. Error: {e}")
            raise HTTPException(status_code=400, detail=str(e)) from e

    async def complete_task(self, task_id: int) -> TaskResponse:
        """Marks a task as completed and returns its updated details."""
        trace_id = str(uuid4())
        logger.info(f"Marking task as completed. Task ID: {task_id}. Trace ID: {trace_id}")
        try:
            updated_task = await self.repository.update_task_status(task_id=task_id, completed=True)
            if not updated_task:
                logger.error(f"Task not found. Task ID: {task_id}. Trace ID: {trace_id}")
                raise HTTPException(status_code=404, detail="Task not found.")
            
            return TaskResponse(
                id=updated_task.id,
                description=updated_task.description,
                completed=updated_task.completed,
                created_at=updated_task.created_at.isoformat()
            )
        except IntegrityError as e:
            logger.error(f"Database constraint violation while updating task status. Trace ID: {trace_id}. Error: {e}")
            raise HTTPException(status_code=400, detail="Failed to update task due to database constraint violation.") from e

    async def remove_task(self, task_id: int) -> None:
        trace_id = str(uuid4())
        logger.info(f"Deleting task. Task ID: {task_id}. Trace ID: {trace_id}")
        try:
            await self.repository.delete_task(task_id=task_id)
            logger.info(f"Successfully deleted task. Task ID: {task_id}. Trace ID: {trace_id}")
            
        except ValueError as ve:
            logger.warning(f"Task not found. Task ID: {task_id}. Trace ID: {trace_id}")  # warning级别
            raise HTTPException(status_code=404, detail=str(ve))
        except IntegrityError as e:
            logger.error(f"Database constraint violation while deleting task. Trace ID: {trace_id}. Error: {e}")
            raise HTTPException(status_code=400, detail="Failed to delete task due to database constraint violation.")
        except Exception as e:
            logger.error(f"Unexpected error while deleting task. Task ID: {task_id}. Trace ID: {trace_id}. Error: {e}")
            raise HTTPException(status_code=500, detail="Failed to delete task due to server error.")

    async def fetch_tasks(self, status: bool) -> List[TaskResponse]:
        """Fetches tasks based on their completion status."""
        trace_id = str(uuid4())
        logger.info(f"Fetching tasks with status: {status}. Trace ID: {trace_id}")
        try:
            tasks = await self.repository.get_tasks_by_status(completed=status)
            return [
                TaskResponse(
                    id=task.id,
                    description=task.description,
                    completed=task.completed,
                    created_at=task.created_at.isoformat()
                )
                for task in tasks
            ]
        except IntegrityError as e:
            logger.error(f"Database constraint violation while fetching tasks. Trace ID: {trace_id}. Error: {e}")
            raise HTTPException(status_code=400, detail="Failed to fetch tasks due to database constraint violation.") from e
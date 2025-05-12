from typing import List, Optional
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models import Task as TaskModel
from backend.database.connection import DatabaseManager
from fastapi import HTTPException
from uuid import uuid4
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskRepository:
    """Handles database operations for tasks."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    async def add_task(self, description: str) -> TaskModel:
        """Adds a new task to the database."""
        trace_id = str(uuid4())
        logger.info(f"Adding task with description: {description}. Trace ID: {trace_id}")
        try:
            async with self.db_manager.session() as session:
                new_task = TaskModel(description=description)
                session.add(new_task)
                await session.commit()
                await session.refresh(new_task)  # 刷新获取完整对象
                return new_task
        except Exception as e:
            logger.error(f"Failed to add task. Trace ID: {trace_id}. Error: {e}")
            raise HTTPException(status_code=500, detail="Failed to add task.") from e

    async def update_task_status(self, task_id: int, completed: bool) -> Optional[TaskModel]:
        """Updates the completion status of a task."""
        trace_id = str(uuid4())
        logger.info(f"Updating task status. Task ID: {task_id}, Completed: {completed}. Trace ID: {trace_id}")
        try:
            async with self.db_manager.session() as session:
                # 先获取任务对象
                task = await session.get(TaskModel, task_id)
                if not task:
                    logger.error(f"Task not found. Task ID: {task_id}. Trace ID: {trace_id}")
                    raise HTTPException(status_code=404, detail="Task not found.")
                
                # 更新状态
                task.completed = completed
                await session.commit()
                await session.refresh(task)  # 刷新获取最新数据
                return task
        except Exception as e:
            logger.error(f"Failed to update task status. Trace ID: {trace_id}. Error: {e}")
            raise HTTPException(status_code=500, detail="Failed to update task status.") from e

    async def delete_task(self, task_id: int) -> None:
        trace_id = str(uuid4())
        logger.info(f"Deleting task. Task ID: {task_id}. Trace ID: {trace_id}")
        try:
            async with self.db_manager.session() as session:
                task = await session.get(TaskModel, task_id)
                if not task:
                    logger.warning(f"Task not found. Task ID: {task_id}. Trace ID: {trace_id}")  # 改为warning级别
                    raise ValueError(f"Task with ID {task_id} not found")  # 使用ValueError而不是HTTPException
                
                await session.delete(task)
                await session.commit()
                logger.info(f"Successfully deleted task. Task ID: {task_id}. Trace ID: {trace_id}")
                
        except ValueError as ve:
            # 重新抛出ValueError让service层处理
            raise ve
        except Exception as e:
            logger.error(f"Database error during deletion. Task ID: {task_id}. Trace ID: {trace_id}. Error: {e}")
            raise Exception("Database operation failed") from e  # 抛出普通异常

    async def get_tasks_by_status(self, completed: bool) -> List[TaskModel]:
        """Retrieves tasks based on their completion status."""
        trace_id = str(uuid4())
        logger.info(f"Fetching tasks with status: {completed}. Trace ID: {trace_id}")
        try:
            async with self.db_manager.session() as session:
                stmt = select(TaskModel).where(TaskModel.completed == completed)
                result = await session.execute(stmt)
                tasks = result.scalars().all()
                return tasks
        except Exception as e:
            logger.error(f"Failed to fetch tasks. Trace ID: {trace_id}. Error: {e}")
            raise HTTPException(status_code=500, detail="Failed to fetch tasks.") from e


db_manager = DatabaseManager()
task_repository = TaskRepository(db_manager)
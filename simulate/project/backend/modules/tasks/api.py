from fastapi import APIRouter, HTTPException, Depends
from typing import List
from pydantic import BaseModel
from backend.modules.tasks.services import TaskService
from backend.database.connection import DatabaseManager

router = APIRouter(prefix="/tasks", tags=["Task Management"])

class TaskCreateRequest(BaseModel):
    """Request model for creating a new task."""
    description: str

class TaskResponse(BaseModel):
    """Response model for returning task details."""
    id: int
    description: str
    completed: bool
    created_at: str

@router.post("/", response_model=TaskResponse, status_code=201)
async def add_task(task_data: TaskCreateRequest, service: TaskService = Depends(TaskService)):
    """
    Add a new task.
    """
    try:
        return await service.create_task(task_data)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error occurred while creating the task.")

@router.put("/{task_id}/complete", response_model=TaskResponse)
async def complete_task(task_id: int, service: TaskService = Depends(TaskService)):
    """
    Mark a task as completed.
    """
    try:
        return await service.complete_task(task_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error occurred while marking the task as completed.")

@router.delete("/{task_id}", status_code=200)
async def delete_task(task_id: int, service: TaskService = Depends(TaskService)):
    """
    Delete a task by its ID.
    """
    try:
        await service.remove_task(task_id)
        return {"success": True}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error occurred while deleting the task.")

@router.get("/", response_model=List[TaskResponse])
async def get_tasks(status: bool = False, service: TaskService = Depends(TaskService)):
    """
    Fetch tasks based on their completion status.
    """
    try:
        return await service.fetch_tasks(status)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error occurred while fetching tasks.")
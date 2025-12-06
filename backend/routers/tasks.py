from typing import List

from fastapi import APIRouter, HTTPException

from .. import crud, schemas
from ..dependencies import current_user_dependency, db_dependency
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/", response_model=schemas.TaskResponse)
def create_task(task: schemas.TaskCreate, db: db_dependency, current_user: current_user_dependency):
    logger.info(f"Creating task: {task.title} for user: {current_user.email}")

    if current_user.role == "pm" and task.user_id:
        created_task = crud.create_task(db=db, task=task, user_id=task.user_id, created_by_id=current_user.id)
    else:
        created_task = crud.create_task(db=db, task=task, user_id=current_user.id, created_by_id=current_user.id)

    logger.info(f"Task created successfully: {task.title} with priority {task.priority}")
    return created_task


@router.get("/", response_model=List[schemas.TaskResponse])
def read_tasks(db: db_dependency, current_user: current_user_dependency):
    logger.info(f"Reading tasks for user: {current_user.email}")
    tasks = crud.get_user_tasks(db, user_id=current_user.id)
    logger.info(f"Found {len(tasks)} tasks for user: {current_user.email}")
    return tasks


@router.get("/{task_id}", response_model=schemas.TaskResponse)
def read_task(task_id: int, db: db_dependency, current_user: current_user_dependency):
    logger.info(f"Reading task: {task_id} for user: {current_user.email}")
    db_task = crud.get_task(db, task_id=task_id, user_id=current_user.id)
    if db_task is None:
        logger.warning(f"Task not found: {task_id}")
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task


@router.put("/{task_id}", response_model=schemas.TaskResponse)
def update_task(
    task_id: int, task_update: schemas.TaskUpdate, db: db_dependency, current_user: current_user_dependency
):
    logger.info(f"Updating task: {task_id} for user: {current_user.email}")
    db_task = crud.get_task(db, task_id=task_id, user_id=current_user.id)
    if db_task is None:
        logger.warning(f"Task not found: {task_id}")
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = task_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_task, key, value)

    db.commit()
    db.refresh(db_task)
    logger.info(f"Task updated: {db_task.title}")
    return db_task


@router.delete("/{task_id}", response_model=schemas.TaskResponse)
def delete_task(task_id: int, db: db_dependency, current_user: current_user_dependency):
    logger.info(f"Deleting task: {task_id} for user: {current_user.email}")
    db_task = crud.delete_task(db=db, task_id=task_id, user_id=current_user.id)
    if db_task is None:
        logger.warning(f"Task not found: {task_id}")
        raise HTTPException(status_code=404, detail="Task not found")
    logger.info(f"Task deleted: {db_task.title}")
    return db_task


@router.get("/assigned-tasks/", response_model=List[schemas.TaskResponse])
def read_assigned_tasks(db: db_dependency, current_user: current_user_dependency, skip: int = 0, limit: int = 10):
    logger.info(f"User {current_user.email} is retrieving assigned tasks (skip={skip}, limit={limit})")
    tasks = crud.get_assigned_tasks(db, created_by_id=current_user.id, skip=skip, limit=limit)
    logger.info(f"User {current_user.email} retrieved {len(tasks)} assigned tasks")
    return tasks


@router.put("/{task_id}/reassign", response_model=schemas.TaskResponse)
def reassign_task(task_id: int, new_user_id: int, db: db_dependency, current_user: current_user_dependency):
    logger.info(f"User {current_user.email} is reassigning task {task_id} to user {new_user_id}")
    db_task = crud.reassign_task(db=db, task_id=task_id, new_user_id=new_user_id, created_by_id=current_user.id)
    if db_task is None:
        logger.error(f"Task {task_id} not found or unauthorized access by user {current_user.email}")
        raise HTTPException(status_code=404, detail="Task not found or unauthorized access")
    logger.info(f"User {current_user.email} successfully reassigned task {task_id}")
    return db_task


@router.delete("/assigned-tasks/{task_id}", response_model=schemas.TaskResponse)
def delete_assigned_task(task_id: int, db: db_dependency, current_user: current_user_dependency):
    logger.info(f"User {current_user.email} is attempting to delete assigned task {task_id}")
    db_task = crud.delete_assigned_task(db=db, task_id=task_id, created_by_id=current_user.id)
    if db_task is None:
        logger.error(f"Task {task_id} not found or unauthorized access by user {current_user.email}")
        raise HTTPException(status_code=404, detail="Task not found or unauthorized access")
    logger.info(f"User {current_user.email} successfully deleted assigned task {task_id}")
    return db_task

from typing import List
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import Response

from .. import crud, schemas
from ..dependencies import current_user_dependency, db_dependency
from ..utils.file_utils import sanitize_filename, validate_file_size, validate_file_type
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter(prefix="/tasks", tags=["files"])


@router.post("/{task_id}/files/")
async def upload_task_file(task_id: int, file: UploadFile, db: db_dependency, current_user: current_user_dependency):
    task = crud.get_task(db, task_id, current_user.id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    filename = sanitize_filename(file.filename)
    if not validate_file_type(filename):
        raise HTTPException(status_code=400, detail="Invalid file type")

    file_data = await file.read()
    if not validate_file_size(len(file_data)):
        raise HTTPException(status_code=400, detail="File too large")

    try:
        db_file = crud.create_task_file(db, task_id, filename, file_data)
        return {"id": db_file.id, "filename": db_file.filename}
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail="Could not upload file")


@router.get("/{task_id}/files/", response_model=List[schemas.TaskFileResponse])
async def get_task_files(task_id: int, db: db_dependency, current_user: current_user_dependency):
    task = crud.get_task(db, task_id, current_user.id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    files = crud.get_task_files(db, task_id)
    return files


@router.get("/{task_id}/files/{file_id}")
async def download_task_file(task_id: int, file_id: int, db: db_dependency, current_user: current_user_dependency):
    file = crud.get_task_file(db, file_id=file_id)
    if not file or file.task_id != task_id:
        raise HTTPException(status_code=404, detail="Файл не найден")

    task = crud.get_task(db, task_id=task_id, user_id=current_user.id)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    if (
        task.user_id != current_user.id
        and task.created_by_id != current_user.id
        and current_user.role not in ["admin", "pm"]
    ):
        raise HTTPException(status_code=403, detail="Нет доступа к файлу")

    filename_encoded = quote(file.filename)

    return Response(
        content=file.data,
        media_type=file.content_type,
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename_encoded}"},
    )


@router.delete("/{task_id}/files/{file_id}", response_model=schemas.TaskFileResponse)
async def delete_task_file(task_id: int, file_id: int, db: db_dependency, current_user: current_user_dependency):
    task = crud.get_task(db, task_id, current_user.id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    file = crud.get_task_file(db, file_id)
    if not file or file.task_id != task_id:
        raise HTTPException(status_code=404, detail="File not found")

    if (
        task.user_id != current_user.id
        and task.created_by_id != current_user.id
        and current_user.role not in ["admin", "pm"]
    ):
        raise HTTPException(status_code=403, detail="Нет доступа к файлу")

    try:
        deleted_file = crud.delete_task_file(db, file_id)
        if deleted_file:
            return deleted_file
        raise HTTPException(status_code=404, detail="Файл не найден")
    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        raise HTTPException(status_code=500, detail="Не удалось удалить файл")

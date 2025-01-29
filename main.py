from datetime import timedelta
from typing import Annotated, List
from urllib.parse import quote

from fastapi import FastAPI, Depends, HTTPException, status, Body, UploadFile
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from jose import JWTError
from fastapi.middleware.cors import CORSMiddleware

import backend.models as models
import backend.schemas as schemas
import backend.crud as crud
import backend.auth as auth
from backend.config import ACCESS_TOKEN_EXPIRE_MINUTES
from backend.utils import create_admin_user, get_db, sanitize_filename, validate_file_type, validate_file_size
from backend.database import engine
from backend.logger import setup_logger
from backend.rate_limiter import RateLimiter

logger = setup_logger(__name__)

models.Base.metadata.create_all(bind=engine)
create_admin_user()

app = FastAPI(
    title="Task Manager API",
    description="API для управления задачами",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

db_dependency = Annotated[Session, Depends(get_db)]
token_dependency = Annotated[str, Depends(oauth2_scheme)]
refresh_token_body = Body(...)
password_body = Body(...)

rate_limiter = RateLimiter()


def get_current_user(db: db_dependency, token: token_dependency):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = auth.decode_access_token(token)
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = schemas.TokenData(email=email)
    except JWTError:
        logger.warning("JWTError: Invalid token")
        raise credentials_exception
    user = crud.get_user_by_email(db, email=token_data.email)
    if user is None:
        logger.warning(f"User not found: {token_data.email}")
        raise credentials_exception
    logger.info(f"User authenticated: {user.email}")
    return user


current_user_dependency = Annotated[schemas.User, Depends(get_current_user)]
form_data_dependency = Annotated[OAuth2PasswordRequestForm, Depends()]


@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: db_dependency):
    logger.info(f"Creating user with email: {user.email}")
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        logger.warning(f"Email already registered: {user.email}")
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = crud.create_user(db=db, user=user)
    logger.info(f"User created: {new_user.email}")
    return new_user


@app.get("/users/me/", response_model=schemas.User)
def read_users_me(current_user: current_user_dependency):
    logger.info(f"Current user: {current_user.email}, role: {current_user.role}")
    return {
        "email": current_user.email,
        "id": current_user.id,
        "created_at": current_user.created_at,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "tasks": current_user.tasks,
        "created_tasks": current_user.created_tasks
    }


@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: db_dependency
):
    logger.info(f"Logging in user: {form_data.username}")

    try:
        rate_limiter.check_rate_limit(form_data.username)

        user = auth.authenticate_user(db, form_data.username, form_data.password)
        if not user:
            rate_limiter.add_attempt(form_data.username)
            logger.warning(f"Failed login attempt for user: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный email или пароль",
                headers={"WWW-Authenticate": "Bearer"},
            )

        rate_limiter.reset_attempts(form_data.username)

        access_token = auth.create_access_token(
            data={"sub": user.email},
            expires_delta=timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))
        )
        refresh_token = auth.create_refresh_token(
            data={"sub": user.email}
        )

        logger.info(f"Tokens generated for user: {form_data.username}")
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error during login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера"
        )


@app.post("/token/refresh", response_model=schemas.Token)
async def refresh_token(refresh_token: str = refresh_token_body):
    logger.info("Refreshing access token")
    new_access_token = auth.refresh_access_token(refresh_token)
    if not new_access_token:
        logger.warning("Invalid refresh token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    logger.info("Access token refreshed successfully")
    return {
        "access_token": new_access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@app.get("/users/", response_model=List[schemas.User])
def read_users(
    db: db_dependency,
    current_user: current_user_dependency,
    skip: int = 0,
    limit: int = 10
):
    logger.info(f"Reading users: skip={skip}, limit={limit}")
    users = crud.get_users(db, skip=skip, limit=limit)
    logger.info(f"Found {len(users)} users")
    return users


@app.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: db_dependency):
    logger.info(f"Reading user: {user_id}")
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        logger.warning(f"User not found: {user_id}")
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.put("/users/{user_id}", response_model=schemas.User)
def update_user(user_id: int, user_update: schemas.UserUpdate, db: db_dependency):
    logger.info(f"Updating user: {user_id}")
    db_user = crud.update_user(db, user_id=user_id, user_update=user_update)
    if db_user is None:
        logger.warning(f"User not found: {user_id}")
        raise HTTPException(status_code=404, detail="User not found")
    logger.info(f"User updated: {db_user.email}")
    return db_user


@app.delete("/users/{user_id}", response_model=schemas.User)
def delete_user(user_id: int, db: db_dependency):
    logger.info(f"Deleting user: {user_id}")
    db_user = crud.delete_user(db, user_id=user_id)
    if db_user is None:
        logger.warning(f"User not found: {user_id}")
        raise HTTPException(status_code=404, detail="User not found")
    logger.info(f"User deleted: {db_user.email}")
    return db_user


@app.post("/tasks/", response_model=schemas.TaskResponse)
def create_task(
    task: schemas.TaskCreate,
    db: db_dependency,
    current_user: current_user_dependency
):
    logger.info(f"Creating task: {task.title} for user: {current_user.email}")

    if current_user.role == 'pm' and task.user_id:
        created_task = crud.create_task(
            db=db,
            task=task,
            user_id=task.user_id,
            created_by_id=current_user.id
        )

    else:
        created_task = crud.create_task(
            db=db,
            task=task,
            user_id=current_user.id,
            created_by_id=current_user.id
        )

    logger.info(f"Task created successfully: {task.title} with priority {task.priority}")
    return created_task


@app.get("/tasks/", response_model=List[schemas.TaskResponse])
def read_tasks(db: db_dependency, current_user: current_user_dependency):
    logger.info(f"Reading tasks for user: {current_user.email}")
    tasks = crud.get_user_tasks(db, user_id=current_user.id)
    logger.info(f"Found {len(tasks)} tasks for user: {current_user.email}")
    return tasks


@app.get("/tasks/{task_id}", response_model=schemas.TaskResponse)
def read_task(task_id: int, db: db_dependency, current_user: current_user_dependency):
    logger.info(f"Reading task: {task_id} for user: {current_user.email}")
    db_task = crud.get_task(db, task_id=task_id, user_id=current_user.id)
    if db_task is None:
        logger.warning(f"Task not found: {task_id}")
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task


@app.put("/tasks/{task_id}", response_model=schemas.TaskResponse)
def update_task(
    task_id: int,
    task_update: schemas.TaskUpdate,
    db: db_dependency,
    current_user: current_user_dependency
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


@app.delete("/tasks/{task_id}", response_model=schemas.TaskResponse)
def delete_task(task_id: int, db: db_dependency, current_user: current_user_dependency):
    logger.info(f"Deleting task: {task_id} for user: {current_user.email}")
    db_task = crud.delete_task(db=db, task_id=task_id, user_id=current_user.id)
    if db_task is None:
        logger.warning(f"Task not found: {task_id}")
        raise HTTPException(status_code=404, detail="Task not found")
    logger.info(f"Task deleted: {db_task.title}")
    return db_task


@app.get("/")
async def read_root():
    return FileResponse("frontend/index.html")


@app.get("/dashboard.html")
async def read_dashboard():
    return FileResponse("frontend/dashboard.html")


@app.put("/users/me/password")
async def change_password(
    current_user: current_user_dependency,
    db: db_dependency,
    body: dict = password_body
):
    logger.info(f"User {current_user.email} is attempting to change password")
    current_password = body.get("current_password")
    new_password = body.get("new_password")

    if not current_password or not new_password:
        logger.warning("Current or new password not provided")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Необходимо указать текущий и новый пароль"
        )

    if not auth.verify_password(current_password, current_user.password_hash):
        logger.warning(f"User {current_user.email} provided invalid current password")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный текущий пароль"
        )

    user_update = schemas.UserUpdate(password=new_password)
    crud.update_user(db, current_user.id, user_update)
    logger.info(f"Password changed successfully for user: {current_user.email}")
    return {"message": "Пароль успешно изменен"}


@app.get("/profile.html")
async def read_profile():
    return FileResponse("frontend/profile.html")


@app.get("/register.html")
async def read_register():
    return FileResponse("frontend/register.html")


@app.get('/favicon.ico')
async def favicon():
    return FileResponse('frontend/static/images/favicon.ico')


def get_admin_user(current_user: current_user_dependency):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


admin_user_dependency = Annotated[schemas.User, Depends(get_admin_user)]
db_admin_dependency = Annotated[Session, Depends(get_db)]


@app.get("/admin/users/", response_model=List[schemas.UserResponse])
def list_all_users(
    current_user: admin_user_dependency,
    db: db_admin_dependency,
    skip: int = 0,
    limit: int = 10
):
    logger.info(f"Admin {current_user.email} is listing all users (skip={skip}, limit={limit})")
    users = crud.get_users(db, skip=skip, limit=limit)
    logger.info(f"Admin {current_user.email} retrieved {len(users)} users")
    return users


@app.put("/admin/users/{user_id}/block", response_model=schemas.UserResponse)
def block_user(
    user_id: int,
    block_update: schemas.UserBlockUpdate,
    current_user: admin_user_dependency,
    db: db_admin_dependency
):
    if user_id == current_user.id:
        logger.warning(f"Admin {current_user.email} attempted to block themselves")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot block yourself"
        )

    db_user = crud.get_user(db, user_id)
    if not db_user:
        logger.error(f"User with ID {user_id} not found for admin {current_user.email}")
        raise HTTPException(status_code=404, detail="User not found")

    db_user.is_active = block_update.is_active
    db.commit()
    db.refresh(db_user)

    action = "unblocked" if block_update.is_active else "blocked"
    logger.info(f"Admin {current_user.email} {action} user {db_user.email}")

    return db_user


@app.get("/token/verify")
async def verify_token(current_user: current_user_dependency):
    logger.info(f"Token verified for user {current_user.email}")
    return {
        "valid": True,
        "user": current_user.email,
        "role": current_user.role
    }


@app.get("/admin.html")
async def read_admin():
    return FileResponse("frontend/admin.html")


@app.put("/admin/users/{user_id}/role", response_model=schemas.UserResponse)
async def change_user_role(
    user_id: int,
    role_update: schemas.UserRoleUpdate,
    current_user: admin_user_dependency,
    db: db_admin_dependency
):
    logger.info(f"Admin {current_user.email} is changing role for user {user_id} to {role_update.role}")

    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только администраторы могут изменять роли пользователей"
        )

    user = crud.get_user(db, user_id)
    if not user:
        logger.error(f"User with ID {user_id} not found for admin {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )

    if user.role == "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Невозможно изменить роль администратора"
        )

    updated_user = crud.update_user_role(db, user_id, role_update.role)
    logger.info(f"Admin {current_user.email} changed role for user {user.email} to {role_update.role}")

    return updated_user


@app.post("/users/me/check-password")
async def check_password(
    current_user: current_user_dependency,
    db: db_dependency,
    body: dict = password_body
):
    password = body.get("password")
    logger.info(f"User {current_user.email} is checking password")

    if not password:
        logger.warning("Password not provided for password check")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Необходимо указать пароль"
        )

    if not auth.verify_password(password, current_user.password_hash):
        logger.warning(f"User {current_user.email} provided invalid password")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный пароль"
        )

    logger.info(f"User {current_user.email} password check successful")
    return {"message": "Пароль верный"}


@app.get("/assigned-tasks/", response_model=List[schemas.TaskResponse])
def read_assigned_tasks(
    db: db_dependency,
    current_user: current_user_dependency,
    skip: int = 0,
    limit: int = 10
):
    logger.info(f"User {current_user.email} is retrieving assigned tasks (skip={skip}, limit={limit})")
    tasks = crud.get_assigned_tasks(db, created_by_id=current_user.id, skip=skip, limit=limit)
    logger.info(f"User {current_user.email} retrieved {len(tasks)} assigned tasks")
    return tasks


@app.put("/tasks/{task_id}/reassign", response_model=schemas.TaskResponse)
def reassign_task(
    task_id: int,
    new_user_id: int,
    db: db_dependency,
    current_user: current_user_dependency
):
    logger.info(f"User {current_user.email} is reassigning task {task_id} to user {new_user_id}")
    db_task = crud.reassign_task(db=db, task_id=task_id, new_user_id=new_user_id, created_by_id=current_user.id)
    if db_task is None:
        logger.error(f"Task {task_id} not found or unauthorized access by user {current_user.email}")
        raise HTTPException(status_code=404, detail="Task not found or unauthorized access")
    logger.info(f"User {current_user.email} successfully reassigned task {task_id}")
    return db_task


@app.delete("/assigned-tasks/{task_id}", response_model=schemas.TaskResponse)
def delete_assigned_task(
    task_id: int,
    db: db_dependency,
    current_user: current_user_dependency
):
    logger.info(f"User {current_user.email} is attempting to delete assigned task {task_id}")
    db_task = crud.delete_assigned_task(db=db, task_id=task_id, created_by_id=current_user.id)
    if db_task is None:
        logger.error(f"Task {task_id} not found or unauthorized access by user {current_user.email}")
        raise HTTPException(status_code=404, detail="Task not found or unauthorized access")
    logger.info(f"User {current_user.email} successfully deleted assigned task {task_id}")
    return db_task


@app.post("/users/verify-reset", response_model=dict)
def verify_reset_credentials(
    reset_request: schemas.PasswordResetRequest,
    db: db_dependency
):
    user = crud.get_user_by_email(db, reset_request.email)
    if not user:
        logger.warning(f"Password reset attempted for non-existent email: {reset_request.email}")
        raise HTTPException(
            status_code=404,
            detail="Пользователь с таким email не найден"
        )

    if not auth.verify_secret_word(reset_request.secret_word, user.secret_word):
        logger.warning(f"Invalid secret word provided for password reset: {reset_request.email}")
        raise HTTPException(
            status_code=400,
            detail="Неверное кодовое слово"
        )

    logger.info(f"Password reset credentials verified for user: {reset_request.email}")
    return {"message": "Данные подтверждены"}


@app.post("/users/reset-password", response_model=dict)
def reset_password(
    reset_data: schemas.PasswordReset,
    db: db_dependency
):
    user = crud.get_user_by_email(db, reset_data.email)
    if not user:
        logger.warning(f"Password reset attempted for non-existent email: {reset_data.email}")
        raise HTTPException(
            status_code=404,
            detail="Пользователь с таким email не найден"
        )

    if not auth.verify_secret_word(reset_data.secret_word, user.secret_word):
        logger.warning(f"Invalid secret word provided for password reset: {reset_data.email}")
        raise HTTPException(
            status_code=400,
            detail="Неверное кодовое слово"
        )

    hashed_password = auth.get_password_hash(reset_data.new_password)
    user.password_hash = hashed_password
    db.commit()

    logger.info(f"Password successfully reset for user: {reset_data.email}")
    return {"message": "Пароль успешно изменен"}


@app.post("/tasks/{task_id}/files/")
async def upload_task_file(
    task_id: int,
    file: UploadFile,
    db: db_dependency,
    current_user: current_user_dependency
):
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


@app.get("/tasks/{task_id}/files/", response_model=List[schemas.TaskFileResponse])
async def get_task_files(
    task_id: int,
    db: db_dependency,
    current_user: current_user_dependency
):
    """Получить список всех файлов задачи"""
    task = crud.get_task(db, task_id, current_user.id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    files = crud.get_task_files(db, task_id)
    return files


@app.get("/tasks/{task_id}/files/{file_id}")
async def download_task_file(
    task_id: int,
    file_id: int,
    db: db_dependency,
    current_user: current_user_dependency
):
    file = crud.get_task_file(db, file_id=file_id)
    if not file or file.task_id != task_id:
        raise HTTPException(status_code=404, detail="Файл не найден")

    task = crud.get_task(db, task_id=task_id, user_id=current_user.id)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    if task.user_id != current_user.id and task.creator_id != current_user.id and current_user.role not in ['admin', 'pm']:
        raise HTTPException(status_code=403, detail="Нет доступа к файлу")

    filename_encoded = quote(file.filename)

    return Response(
        content=file.data,
        media_type=file.content_type,
        headers={
            'Content-Disposition': f'attachment; filename*=UTF-8\'\'{filename_encoded}'
        }
    )


@app.delete("/tasks/{task_id}/files/{file_id}", response_model=schemas.TaskFileResponse)
async def delete_task_file(
    task_id: int,
    file_id: int,
    db: db_dependency,
    current_user: current_user_dependency
):
    task = crud.get_task(db, task_id, current_user.id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    file = crud.get_task_file(db, file_id)
    if not file or file.task_id != task_id:
        raise HTTPException(status_code=404, detail="File not found")

    if task.user_id != current_user.id and task.creator_id != current_user.id and current_user.role not in ['admin', 'pm']:
        raise HTTPException(status_code=403, detail="Нет доступа к файлу")

    try:
        deleted_file = crud.delete_task_file(db, file_id)
        if deleted_file:
            return deleted_file
        raise HTTPException(status_code=404, detail="Файл не найден")
    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        raise HTTPException(status_code=500, detail="Не удалось удалить файл")

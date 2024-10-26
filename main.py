from datetime import timedelta
from typing import Annotated, List

from fastapi import FastAPI, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from jose import JWTError

import backend.models as models
import backend.schemas as schemas
import backend.crud as crud
import backend.auth as auth
from backend.config import ACCESS_TOKEN_EXPIRE_MINUTES
from backend.utils import create_admin_user, get_db
from backend.database import engine
from backend.logger import setup_logger

logger = setup_logger(__name__)

models.Base.metadata.create_all(bind=engine)
create_admin_user()

app = FastAPI()

app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

db_dependency = Annotated[Session, Depends(get_db)]
token_dependency = Annotated[str, Depends(oauth2_scheme)]


def get_current_user(db: Annotated[Session, Depends(get_db)], token: token_dependency):
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
        raise credentials_exception
    user = crud.get_user_by_email(db, email=token_data.email)
    if user is None:
        raise credentials_exception
    return user


current_user_dependency = Annotated[schemas.User, Depends(get_current_user)]
form_data_dependency = Annotated[OAuth2PasswordRequestForm, Depends()]


@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Annotated[Session, Depends(get_db)]):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)


@app.get("/users/me/", response_model=schemas.User)
def read_users_me(current_user: current_user_dependency):
    return current_user


@app.post("/token", response_model=schemas.Token)
def login_for_access_token(
    db: Annotated[Session, Depends(get_db)],
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль, либо аккаунт заблокирован",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/", response_model=list[schemas.User])
def read_users(db: Annotated[Session, Depends(get_db)], skip: int = 0, limit: int = 10):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@app.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Annotated[Session, Depends(get_db)]):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.put("/users/{user_id}", response_model=schemas.User)
def update_user(user_id: int, user_update: schemas.UserUpdate, db: Annotated[Session, Depends(get_db)]):
    db_user = crud.update_user(db, user_id=user_id, user_update=user_update)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.delete("/users/{user_id}", response_model=schemas.User)
def delete_user(user_id: int, db: Annotated[Session, Depends(get_db)]):
    db_user = crud.delete_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.post("/tasks/", response_model=schemas.TaskResponse)
def create_task(task: schemas.TaskCreate, db: db_dependency, current_user: current_user_dependency):
    return crud.create_task(db=db, task=task, user_id=current_user.id)


@app.get("/tasks/", response_model=List[schemas.TaskResponse])
def read_tasks(db: db_dependency, current_user: current_user_dependency):
    tasks = crud.get_user_tasks(db, user_id=current_user.id)
    return tasks


@app.get("/tasks/{task_id}", response_model=schemas.TaskResponse)
def read_task(task_id: int, db: db_dependency, current_user: current_user_dependency):
    db_task = crud.get_task(db, task_id=task_id, user_id=current_user.id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task


@app.put("/tasks/{task_id}", response_model=schemas.TaskResponse)
def update_task(
    task_id: int,
    task_update: schemas.TaskUpdate,
    db: db_dependency,
    current_user: current_user_dependency
):
    db_task = crud.get_task(db, task_id=task_id, user_id=current_user.id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = task_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_task, key, value)

    db.commit()
    db.refresh(db_task)
    return db_task


@app.delete("/tasks/{task_id}", response_model=schemas.TaskResponse)
def delete_task(task_id: int, db: db_dependency, current_user: current_user_dependency):
    db_task = crud.delete_task(db=db, task_id=task_id, user_id=current_user.id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task


@app.get("/")
async def read_root():
    return FileResponse("frontend/index.html")


@app.get("/dashboard.html")
async def read_dashboard():
    return FileResponse("frontend/dashboard.html")

password_body = Body(...)


@app.put("/users/me/password")
async def change_password(
    current_user: current_user_dependency,
    db: db_dependency,
    body: dict = password_body
):
    current_password = body.get("current_password")
    new_password = body.get("new_password")

    if not current_password or not new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Необходимо указать текущий и новый пароль"
        )

    if not auth.verify_password(current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный текущий пароль"
        )

    user_update = schemas.UserUpdate(password=new_password)
    crud.update_user(db, current_user.id, user_update)
    return {"message": "ароль успешно изменен"}


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
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@app.put("/admin/users/{user_id}/block", response_model=schemas.UserResponse)
def block_user(
    user_id: int,
    block_update: schemas.UserBlockUpdate,
    current_user: admin_user_dependency,
    db: db_admin_dependency
):
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot block yourself"
        )

    db_user = crud.get_user(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    db_user.is_active = block_update.is_active
    db.commit()
    db.refresh(db_user)

    action = "unblocked" if block_update.is_active else "blocked"
    logger.info(f"Admin {current_user.email} {action} user {db_user.email}")

    return db_user

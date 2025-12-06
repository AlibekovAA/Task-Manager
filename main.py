from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.database import engine
from backend.models import Base
from backend.routers import admin, auth, files, static, tasks, users
from backend.utils import admin as admin_utils

Base.metadata.create_all(bind=engine)
admin_utils.create_admin_user()

app = FastAPI(
    title="Task Manager API",
    description="API для управления задачами",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(tasks.router)
app.include_router(admin.router)
app.include_router(files.router)
app.include_router(static.router)

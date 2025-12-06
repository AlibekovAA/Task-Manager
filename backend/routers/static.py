from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter(tags=["static"])


@router.get("/")
async def read_root():
    return FileResponse("frontend/index.html")


@router.get("/dashboard.html")
async def read_dashboard():
    return FileResponse("frontend/dashboard.html")


@router.get("/profile.html")
async def read_profile():
    return FileResponse("frontend/profile.html")


@router.get("/register.html")
async def read_register():
    return FileResponse("frontend/register.html")


@router.get("/admin.html")
async def read_admin():
    return FileResponse("frontend/admin.html")


@router.get("/favicon.ico")
async def favicon():
    return FileResponse("frontend/static/images/favicon.ico")

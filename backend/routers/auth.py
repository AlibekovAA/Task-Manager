from datetime import timedelta

from fastapi import APIRouter, Body, HTTPException, status

from .. import schemas
from ..config import ACCESS_TOKEN_EXPIRE_MINUTES
from ..dependencies import current_user_dependency, db_dependency, form_data_dependency
from ..services import auth_service as auth
from ..utils.logger import setup_logger
from ..utils.rate_limiter import rate_limiter

logger = setup_logger(__name__)

router = APIRouter(prefix="/token", tags=["auth"])

refresh_token_body = Body(...)


@router.post("", response_model=schemas.Token)
async def login_for_access_token(form_data: form_data_dependency, db: db_dependency):
    username = form_data.username.lower().strip() if form_data.username else ""
    logger.info(f"Logging in user: {username}")

    if not username or not form_data.password:
        logger.warning("Empty username or password provided")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email и пароль обязательны для заполнения",
        )

    try:
        rate_limiter.check_rate_limit(username)

        user = auth.authenticate_user(db, username, form_data.password)
        if not user:
            rate_limiter.add_attempt(username)
            logger.warning(f"Failed login attempt for user: {username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный email или пароль",
                headers={"WWW-Authenticate": "Bearer"},
            )

        rate_limiter.reset_attempts(username)

        access_token = auth.create_access_token(
            data={"sub": user.email}, expires_delta=timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))
        )
        refresh_token = auth.create_refresh_token(data={"sub": user.email})

        logger.info(f"Tokens generated for user: {username}")
        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error during login: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутренняя ошибка сервера")


@router.post("/refresh", response_model=schemas.Token)
async def refresh_token(refresh_token: str = refresh_token_body):
    logger.info("Refreshing access token")
    new_access_token = auth.refresh_access_token(refresh_token)
    if not new_access_token:
        logger.warning("Invalid refresh token")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    logger.info("Access token refreshed successfully")
    return {"access_token": new_access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.get("/verify")
async def verify_token(current_user: current_user_dependency):
    logger.info(f"Token verified for user {current_user.email}")
    return {"valid": True, "user": current_user.email, "role": current_user.role}

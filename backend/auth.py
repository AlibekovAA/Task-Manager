from datetime import datetime, timedelta
from typing import Optional

from passlib.context import CryptContext
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from . import crud
from .config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from .logger import setup_logger

logger = setup_logger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _handle_password_operation(operation: str, *args, log_msg: str):
    logger.info(f"Attempting to {operation} password")
    try:
        result = getattr(pwd_context, operation)(*args)
        logger.info(log_msg)
        return result
    except Exception as e:
        logger.error(f"Error {operation} password: {e}")
        return False if operation == "verify" else None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return _handle_password_operation(
        "verify",
        plain_password,
        hashed_password,
        log_msg="Password verification completed"
    )


def get_password_hash(password: str) -> str:
    result = _handle_password_operation(
        "hash",
        password,
        log_msg="Password hashed successfully"
    )
    if result is None:
        raise ValueError("Failed to hash password")
    return result


def authenticate_user(db: Session, email: str, password: str):
    logger.info(f"Attempting to authenticate user: {email}")
    try:
        user = crud.get_user_by_email(db, email)
        if not user or not user.is_active or not verify_password(password, user.password_hash):
            logger.warning(f"Authentication failed for user {email}")
            return False
        logger.info(f"User {email} authenticated successfully")
        return user
    except Exception as e:
        logger.error(f"Error during authentication: {e}")
        return False


def _create_token(data: dict, expires_delta: Optional[timedelta], token_type: str = "access"):
    try:
        to_encode = data.copy()
        expire = datetime.now() + (expires_delta or timedelta(minutes=15))
        to_encode.update({"exp": expire})
        if token_type == "refresh":
            to_encode.update({"type": "refresh"})

        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        logger.info(f"{token_type.title()} token created for user: {data.get('sub')}")
        return encoded_jwt
    except Exception as e:
        logger.error(f"Error creating {token_type} token: {e}")
        raise


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    return _create_token(data, expires_delta)


def create_refresh_token(data: dict):
    return _create_token(data, timedelta(days=30), "refresh")


def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        logger.debug(f"Token decoded successfully for user: {payload.get('sub')}")
        return payload
    except (JWTError, Exception) as e:
        logger.warning(f"Token decoding failed: {e}")
        return None


def refresh_access_token(refresh_token: str):
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh" or not (email := payload.get("sub")):
            logger.warning("Invalid refresh token")
            return None

        return create_access_token(
            data={"sub": email},
            expires_delta=timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))
        )
    except JWTError as e:
        logger.warning(f"Invalid refresh token: {e}")
        return None


verify_secret_word = verify_password

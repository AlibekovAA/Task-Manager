from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError
from sqlalchemy.orm import Session

from . import crud, schemas
from .database import get_db
from .services import auth_service as auth
from .utils.logger import setup_logger

logger = setup_logger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

db_dependency = Annotated[Session, Depends(get_db)]
token_dependency = Annotated[str, Depends(oauth2_scheme)]
form_data_dependency = Annotated[OAuth2PasswordRequestForm, Depends()]


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


def get_admin_user(current_user: current_user_dependency):
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    return current_user


admin_user_dependency = Annotated[schemas.User, Depends(get_admin_user)]

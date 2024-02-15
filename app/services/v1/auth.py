import uuid
from datetime import datetime, timedelta
from typing import List

from app.config import Settings
from app.models.pydantic import User_Pydantic
from app.models.tortoise import Users
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from passlib.context import CryptContext
from pydantic import UUID4
from starlette import status

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
settings = Settings()


class Auth:
    password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    @classmethod
    def get_password_hash(cls, password: str) -> str:
        return cls.password_context.hash(password)

    @classmethod
    def verify_password(cls, plain_password: str, hashed_password: str) -> bool:
        return cls.password_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_token(data: dict, expires_delta: int) -> str:
        to_encode = data.copy()
        to_encode.update(
            {
                "exp": datetime.now() + timedelta(minutes=expires_delta),
                "iss": settings.app_name,
            }
        )
        return jwt.encode(
            to_encode,
            settings.secret_key.get_secret_value(),
            algorithm=settings.token_algorithm,
        )

    @staticmethod
    def get_confirmation_token(email: str):
        jti = uuid.uuid4()
        claims = {"sub": email, "scope": "registration", "jti": jti.hex}
        return {
            "jti": jti.hex,
            "token": Auth.get_token(
                data=claims, expires_delta=settings.registration_token_lifetime
            ),
        }

    @staticmethod
    def get_access_token(email: str):
        jti = uuid.uuid4()
        claims = {"sub": email, "scope": "login", "jti": jti.hex}
        return {
            "jti": jti.hex,
            "token": Auth.get_token(
                data=claims, expires_delta=settings.login_token_lifetime
            ),
        }

    @staticmethod
    def get_refresh_token(email: str):
        jti = uuid.uuid4()
        claims = {"sub": email, "scope": "refresh", "jti": jti.hex}
        return {
            "jti": jti.hex,
            "token": Auth.get_token(
                data=claims, expires_delta=settings.refresh_token_lifetime
            ),
        }

    @staticmethod
    def get_reset_password_token(email: str):
        jti = uuid.uuid4()
        claims = {"sub": email, "scope": "reset-password", "jti": jti.hex}
        return {
            "jti": jti.hex,
            "token": Auth.get_token(
                data=claims, expires_delta=settings.login_token_lifetime
            ),
        }

    # Authenticate and return user
    @staticmethod
    async def authenticate_user(email: str, password: str) -> User_Pydantic:
        user = await Users.get_or_none(email=email.lower())
        if not user:
            return False
        if not Auth.verify_password(
            plain_password=password, hashed_password=user.hashed_password
        ):
            return False
        return user


async def get_current_user(
    token: str = Depends(oauth2_scheme),
) -> User_Pydantic:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            str(settings.secret_key.get_secret_value()),
            algorithms=[settings.token_algorithm],
        )
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except jwt.JWTError:
        raise credentials_exception
    user = await Users.get_or_none(email=email)
    if user is None:
        raise credentials_exception
    await user.fetch_related("roles", "address", "working_hours")
    return user


# get current active use
async def get_current_active_user(
    current_user=Depends(get_current_user),
) -> User_Pydantic:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="User is inactive")
    return current_user


# Role Checker
class RoleChecker:
    def __init__(self, allowed_roles: List):
        self.allowed_roles = allowed_roles

    async def __call__(self, user: User_Pydantic = Depends(get_current_active_user)):
        await user.fetch_related("roles")
        for role in user.roles:
            if role.name in self.allowed_roles:
                return True
        raise HTTPException(status_code=403, detail="Operation not permitted")

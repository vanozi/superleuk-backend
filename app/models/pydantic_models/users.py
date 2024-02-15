from typing import Optional
from pydantic import BaseModel, EmailStr, SecretStr
import datetime
from app.models.pydantic_models.roles import RoleInUserResponse
from app.models.pydantic_models.address import AddressResponse


class CreateUserRequest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: SecretStr


class UserResponse(BaseModel):
    id: int
    first_name: Optional[str]
    last_name: Optional[str]
    email: EmailStr
    telephone_number: Optional[str]
    date_of_birth: Optional[datetime.date]
    is_active: bool
    roles: list[RoleInUserResponse]
    address: Optional[AddressResponse]


class UpdateUserRequest(BaseModel):
    first_name: Optional[str]
    last_name: Optional[str]
    email: Optional[EmailStr]
    telephone_number: Optional[str]
    date_of_birth: Optional[datetime.date]

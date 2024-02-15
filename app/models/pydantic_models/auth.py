import datetime

from typing import Optional, Union, List
import uuid
from pydantic import BaseModel, EmailStr, field_validator, SecretStr
from ..pydantic_models.roles import RoleResponse


class RegisterUserRequest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: SecretStr

    @field_validator("email", mode="before")
    def transform_email_to_lowercase(cls, value: EmailStr):
        return value.lower()


class UserResponse(BaseModel):
    id: int
    created_at: datetime.datetime
    last_modified_at: datetime.datetime
    first_name: str
    last_name: str
    date_of_birth: Union[datetime.date, None]
    email: EmailStr
    telephone_number: Union[str, None]
    is_active: bool
    confirmation: Union[uuid.UUID, None]
    roles: Union[List[RoleResponse], None]

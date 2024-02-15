import datetime

from pydantic import BaseModel, EmailStr, validator
from datetime import date


class AllowedUserRequest(BaseModel):
    email: EmailStr

    @validator("email", pre=True, always=True)
    def transform_email_to_lowercase(cls, value):
        return value.lower()


class AllowedUserResponse(BaseModel):
    id: int
    created_at: datetime.datetime
    last_modified_at: datetime.datetime
    email: EmailStr

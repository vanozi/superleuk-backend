from pydantic import BaseModel, validator
import datetime
from typing import Optional
from app.models.pydantic_models.users import UserResponse


class VakantieRequest(BaseModel):
    start_date: datetime.date
    end_date: datetime.date

    @validator("end_date")
    def end_date_must_be_greater_than_start_date(cls, v, values):
        if "start_date" in values and v < values["start_date"]:
            raise ValueError("eind datum moet groter zijn dan start datum")
        return v


class VakantieResponse(BaseModel):
    id: int
    start_date: datetime.date
    end_date: datetime.date


class VakantiesForCalendarResponse(BaseModel):
    id: int
    start: datetime.date
    end: datetime.date
    resourceId: int


class ResourceResponse(BaseModel):
    id: int
    groupId: int
    title: str

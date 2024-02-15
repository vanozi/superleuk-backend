import datetime
from typing import Optional, List
from pydantic import BaseModel


class WorkingHoursResponse(BaseModel):
    id: int
    date: datetime.date
    hours: float
    milkings: int
    description: str
    submitted: bool


class WorkingHoursRequest(BaseModel):
    id: Optional[int] = None
    date: datetime.date
    hours: float
    milkings: Optional[int] = 0
    description: str
    submitted: Optional[bool] = False


class WorkingHoursWeekOverviewResponse(BaseModel):
    year: int
    week: int
    week_start: datetime.date
    week_end: datetime.date
    working_hours: List[WorkingHoursResponse]
    sum_hours: float
    sum_milkings: float
    submitted: bool


class ReleaseRequest(BaseModel):
    from_date: datetime.date
    to_date: datetime.date
    user_id: int

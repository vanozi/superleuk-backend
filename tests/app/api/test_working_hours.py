import json, datetime
import pytest
from fastapi.testclient import TestClient
from app.models.pydantic_models.working_hours import WorkingHoursRequest
from fastapi import Response
from app.services.v2.mail import fm

pytestmark = pytest.mark.anyio


# Registration
async def test_get_all_working_hours_success(
        test_client: TestClient, insert_working_hours: WorkingHoursRequest
):
    # Current date
    current_date = datetime.date.today()
    # Dates for one week, one month, and six months ago
    one_week_ago = current_date - datetime.timedelta(weeks=1)
    one_month_ago = current_date - datetime.timedelta(weeks=1)
    six_months_ago = current_date - datetime.timedelta(weeks=1)
    working_hours_one_week_ago: WorkingHoursRequest = WorkingHoursRequest(
        date=one_week_ago,
        hours=2,
        milkings=0,
        description=' lekker gewerkt',
        submitted=False
    )
    working_hours_one_month_ago: WorkingHoursRequest = WorkingHoursRequest(
        date=one_month_ago,
        hours=2,
        milkings=0,
        description=' lekker gewerkt',
        submitted=False
    )
    working_hours_six_months_ago: WorkingHoursRequest = WorkingHoursRequest(
        date=six_months_ago,
        hours=2,
        milkings=0,
        description=' lekker gewerkt',
        submitted=False
    )
    await insert_working_hours(working_hours_one_week_ago, 'werknemer@werknemer.com')
    await insert_working_hours(working_hours_one_month_ago, 'werknemer@werknemer.com')
    await insert_working_hours(working_hours_six_months_ago, 'werknemer@werknemer.com')
    # Get all working hours
    await test_client

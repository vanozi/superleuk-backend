import pytest
from app.models.pydantic_models.working_hours import WorkingHoursRequest
from app.services.v2.auth import Auth
from fastapi import Response


@pytest.fixture(scope="function")
async def insert_working_hours(test_client):
    async def _add_new_working_hours(working_hours: WorkingHoursRequest, email_gebruiker: str):
        response = await test_client.put(
            "/working_hours/", headers={
                "Authorization": f"Bearer {Auth.get_access_token(email_gebruiker)['token']}",
                "Content-Type": "application/json",
            }, content=working_hours.model_dump_json()
        )
        if response.status_code == 200:
            return
        else:
            raise Exception(response.text)

    return _add_new_working_hours

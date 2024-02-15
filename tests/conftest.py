import os

import pytest
from httpx import AsyncClient
from tortoise import Tortoise

from app.config import Settings
from app.main import create_application
from app.models.pydantic import AllowedUsersCreateSchema, MachineCreateSchema
from app.models.pydantic_models.auth import RegisterUserRequest
from app.services.v2.mail import fm
from app.models.tortoise import Users
from pathlib import Path

from tests.fixtures.working_hours import *


async def execute_sql_file(file_name):
    # Directory of the script or module
    script_dir = Path(__file__).parent

    # Construct the full file path relative to the script directory
    file_path = script_dir / 'data' / file_name

    # Read the SQL file
    with file_path.open("r") as sql_file:
        sql_content = sql_file.read()

    # Split the SQL content into individual queries (assuming queries are separated by ';')
    queries = sql_content.split(";")

    # Execute each query
    for query in queries:
        query = query.strip()  # Remove leading/trailing whitespace
        if query:
            await Tortoise.get_connection("default").execute_query(query)


async def init_db(
        db_url,
        create_db: bool = False,
        create_schemas: bool = False,
        create_test_data: bool = False,
) -> None:
    """Initial database connection"""
    await Tortoise.init(
        db_url=db_url,
        modules={"models": ["app.models.tortoise"]},
        _create_db=create_db,
    )
    if create_schemas:
        await Tortoise.generate_schemas()
    if create_test_data:
        await execute_sql_file("setup_testdata.sql")


async def init(db_url: str = os.getenv("DATABASE_TEST_URL")) -> None:
    await init_db(db_url, True, True, True)


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
async def test_client(anyio_backend):
    app = create_application()
    await init()
    async with AsyncClient(app=app, base_url=os.getenv("BASE_URL_API")) as client:
        yield client
    await client.aclose()
    await Tortoise._drop_databases()
    print("Database dropped")


@pytest.fixture(scope="function")
async def admin_token(test_client):
    # Get admin access token
    response = await test_client.post(
        url="/auth/login",
        headers={},
        data={"username": "admin@admin.com", "password": "admin"},
        files=[],
    )
    print(response.status_code)
    yield response.json()["access_token"]


@pytest.fixture(scope="function")
async def werknemer_token(test_client):
    # Get admin access token
    response = await test_client.post(
        url="/auth/login",
        headers={},
        data={"username": "werknemer@werknemer.com", "password": "werknemer"},
        files=[],
    )
    yield response.json()["access_token"]


@pytest.fixture(scope="function")
async def invite_new_user_fixture(test_client, admin_token: str):
    async def _send_invitation(email_adress: str):
        fm.config.SUPPRESS_SEND = 1
        headers = {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json",
        }
        payload = AllowedUsersCreateSchema(email=email_adress).json()
        response = await test_client.post(
            "/allowed_users/", headers=headers, content=payload
        )
        return response.status_code

    return _send_invitation


@pytest.fixture(scope="function")
async def insert_new_machine_fixture(test_client, admin_token: str):
    async def _add_new_machine(work_number: str):
        headers = {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json",
        }
        payload = MachineCreateSchema(
            work_number=work_number,
            work_name="Test Machine 3",
            category="Trekker 3",
            group="Gemotoriseerd 3",
            brand_name="John Deere 3",
            type_name="7810 3",
            licence_number="MM-11-XX 3",
            chassis_number="123456789 3",
            construction_year="2012",
            ascription_code="1234567801",
        ).json()
        response = await test_client.post(
            "/machines/", headers=headers, content=payload
        )
        return response.status_code

    return _add_new_machine


@pytest.fixture(scope="function")
async def add_user(test_client, admin_token: str):
    async def _add_user(user: dict):
        try:
            added_user = await Users.create(**user)
            return added_user
        except Exception as e:
            print(e)

    return _add_user

# HTML REPORT HOOKS
# def pytest_html_report_title(report):
#     report.title = "Backend Test Report"

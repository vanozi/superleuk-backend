import json
import uuid

import pytest
from fastapi.testclient import TestClient

from app.models.pydantic_models.auth import RegisterUserRequest
from app.services.v2.mail import fm

pytestmark = pytest.mark.anyio

from app.services.v2.auth import Auth


# Registration
async def test_registration_success(
        test_client: TestClient, invite_new_user_fixture: int
):
    # Invite user for registration
    await invite_new_user_fixture("test_gebruiker@test.com")
    # Set user details for registration
    payload = json.dumps(
        {
            "first_name": "test",
            "last_name": "gebruiker",
            "email": "test_gebruiker@test.com",
            "password": "testgebruiker",
        }
    )
    headers = {"Content-Type": "application/json"}
    fm.config.SUPPRESS_SEND = 1
    with fm.record_messages() as outbox:
        response = await test_client.post(
            "/auth/register", headers=headers, data=payload
        )
        assert response.status_code == 201
        assert type(response.json()["id"] == int)
        assert response.json()['created_at']
        assert response.json()['last_modified_at']
        assert response.json()["email"] == "test_gebruiker@test.com"
        assert response.json()["is_active"] == False
        assert len(response.json()["roles"]) == 1
        assert response.json()["roles"][0]["name"] == "werknemer"
        # Email checks
        assert len(outbox) == 1
        assert (
                outbox[0]["from"] == "Superleuk app Gebr. Vroege <supermooiapp@gmail.com>"
        )
        assert outbox[0]["To"] == "test_gebruiker@test.com"
        assert outbox[0]["Subject"] == "Welkom!!"


async def test_registration_user_already_registered(test_client: TestClient):
    payload = json.dumps(
        {
            "first_name": "test",
            "last_name": "gebruiker",
            "email": "test_gebruiker@test.com",
            "password": "testgebruiker",
        }
    )
    headers = {"Content-Type": "application/json"}
    response = await test_client.post("/auth/register", headers=headers, data=payload)
    # check response code is 400 and response text as expected
    assert response.status_code == 400
    assert response.json()["detail"] == "Gebruiker bestaat al"


async def test_registration_user_not_invited(
        test_client: TestClient,
):
    payload = json.dumps(
        {
            "first_name": "test",
            "last_name": "gebruiker",
            "email": "test2_gebruiker@test.com",
            "password": "testgebruiker",
        }
    )
    headers = {"Content-Type": "application/json"}

    response = await test_client.post("/auth/register", headers=headers, data=payload)
    # check response code is 400 and response text as expected
    assert response.status_code == 400
    assert (
            response.json()["detail"]
            == "Dit email adres is niet bevoegd om zich te registeren"
    )

# Activate account
async def test_activation_success(test_client: TestClient, add_user: dict):
    # Generate invalid token
    # add user to database with invalid token
    confirmation_token = Auth.get_confirmation_token(email='peter@pan.com')
    user = {
        'first_name': 'peter',
        'last_name': 'pan',
        'email': 'peter@pan.com',
        'password': 'johndeere',
        'confirmation': confirmation_token['jti'],
        'hashed_password': '$2b$12$5.D0HbFurnUj9RMjPE1hheMCdUF/J7S5iA.PAq1SqW7bQ03sK7kwG'
    }
    await add_user(user)
    # send request and verify response
    data = json.dumps({
        'token': confirmation_token["token"],
        'refresh_token': ''
    })
    headers = {
        'accept': 'application/json'
    }
    response = await test_client.post("/auth/activate_account", headers=headers, data=data)
    assert response.status_code == 200
    assert response.json()['detail'] == 'Account geactiveerd'


async def test_activation_invalid_token(test_client: TestClient,add_user: dict):
    # Generate invalid token
    # add user to database with invalid token
    confirmation_token = Auth.get_confirmation_token(email='peter2@pan2.com')
    user = {
        'first_name': 'peter2',
        'last_name': 'pan2',
        'email': 'peter2@pan2.com',
        'password': 'johndeere',
        'confirmation': confirmation_token['jti'],
        'hashed_password': '$2b$12$5.D0HbFurnUj9RMjPE1hheMCdUF/J7S5iA.PAq1SqW7bQ03sK7kwG'
    }
    await add_user(user)
    # send request and verify response
    data = json.dumps({
        'token': confirmation_token["token"] + "123",
        'refresh_token': ''
    })
    headers = {
        'accept': 'application/json'
    }
    response = await test_client.post("/auth/activate_account", headers=headers, data=data)
    assert response.status_code == 400
    assert response.json()['detail'] == 'Signature verification failed.'


async def test_activation_expired_token(test_client: TestClient, add_user: dict):
    # Generate invalid token
    # add user to database with invalid token
    confirmation_token = Auth.get_confirmation_token(email='peter3@pan3.com')
    user = {
        'first_name': 'peter3',
        'last_name': 'pan3',
        'email': 'peter3@pan3.com',
        'password': 'johndeere',
        'confirmation': confirmation_token['jti'],
        'hashed_password': '$2b$12$5.D0HbFurnUj9RMjPE1hheMCdUF/J7S5iA.PAq1SqW7bQ03sK7kwG'
    }
    await add_user(user)
    # send request and verify response
    jti = uuid.uuid4()
    claims = {"sub": 'peter3@pan3.com', "scope": "registration", "jti": jti.hex}
    data = json.dumps({
        'token': Auth.get_token(claims, expires_delta=-300),
        'refresh_token': ''
    })
    headers = {
        'accept': 'application/json'
    }
    response = await test_client.post("/auth/activate_account", headers=headers, data=data)
    assert response.status_code == 400
    assert response.json()['detail'] == 'Signature has expired.'


async def test_activation_user_allready_active(test_client: TestClient):
    assert True


# Login
async def test_login_success(test_client: TestClient):
    data = {
        'grant_type': '',
        'username': 'admin@admin.com',
        'password': 'admin',
        'scope': '',
        'client_id': '',
        'client_secret': '',
    }
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    response = await test_client.post("/auth/login", headers=headers, data=data)
    # check response code is 200 and response text as expected
    assert response.status_code == 200
    assert response.json()["access_token"] is not None
    assert response.cookies['refresh_token'] is not None


async def test_login_invalid_username(test_client: TestClient):
    data = {
        'grant_type': '',
        'username': 'admin1@admin.com',
        'password': 'admin',
        'scope': '',
        'client_id': '',
        'client_secret': '',
    }
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    response = await test_client.post("/auth/login", headers=headers, data=data)
    assert response.status_code == 401
    assert response.json()["detail"] == 'Ongeldige combinatie gebruikersnaam en wachtwoord'


async def test_login_invalid_password(test_client: TestClient):
    data = {
        'grant_type': '',
        'username': 'admin@admin.com',
        'password': 'admin1',
        'scope': '',
        'client_id': '',
        'client_secret': '',
    }
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    response = await test_client.post("/auth/login", headers=headers, data=data)
    assert response.status_code == 401
    assert response.json()["detail"] == 'Ongeldige combinatie gebruikersnaam en wachtwoord'


async def test_login_user_inactive(test_client: TestClient, add_user: RegisterUserRequest):
    user = {'first_name': 'henk',
            'last_name': 'klaas',
            'email': 'henk@klaas.com',
            'hashed_password': '$2b$12$5.D0HbFurnUj9RMjPE1hheMCdUF/J7S5iA.PAq1SqW7bQ03sK7kwG'
            }
    await add_user(user)
    data = {
        'grant_type': '',
        'username': 'henk@klaas.com',
        'password': 'johndeere',
        'scope': '',
        'client_id': '',
        'client_secret': '',
    }
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    response = await test_client.post("/auth/login", headers=headers, data=data)
    assert response.status_code == 401
    assert response.json()["detail"] == 'Gebruiker inactief'

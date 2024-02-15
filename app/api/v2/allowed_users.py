import os
from typing import List
from app.models.tortoise import AllowedUsers
from app.models.tortoise import Users
from app.services.v2.auth import RoleChecker, get_current_active_user
from app.services.v2.mail import Mailer
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.param_functions import Depends
from fastapi_mail import MessageType
from starlette import status


from app.models.pydantic_models.allowed_users import (
    AllowedUserRequest,
    AllowedUserResponse,
)
from app.services.v2.auth import RoleChecker
from app.services.v2.mail import Mailer
from app.models.pydantic import EmailSchema


router = APIRouter()

# CRUD Implementation for allowed users


# Create allowed user (only the admin can do this)
@router.post(
    "/",
    response_model=AllowedUserResponse,
    status_code=201,
    dependencies=[Depends(RoleChecker(["admin"]))]
)
async def add_allowed_user(
    added_user: AllowedUserRequest,
    background_tasks: BackgroundTasks,
    current_active_user=Depends(get_current_active_user)
) -> AllowedUserResponse:
    email = added_user.email.lower()
    if await AllowedUsers.get_or_none(email=email) is not None:
        raise HTTPException(
            status_code=400,
            detail="Er is al een uitnodiging gestuurd naar dit e-mailadres",
        )
    if await Users.get_or_none(email=email) is not None:
        raise HTTPException(
            status_code=400, detail="Dit e-mailadres is al geregistreerd"
        )
    try:
        allowed_user = await AllowedUsers.create(email=added_user.email.lower())
        email_schema = EmailSchema(
            recipient_addresses=[allowed_user.email],
            body={
                "base_url": os.getenv("BASE_URL_FRONTEND"),
                "sender": "Gebroeders Vroege",
            }
        )
        background_tasks.add_task(Mailer.send_invitation_message, email=email_schema)
        return AllowedUserResponse(id=allowed_user.id, created_at=allowed_user.created_at, last_modified_at=allowed_user.last_modified_at, email=allowed_user.email )
    except Exception as e:
        if allowed_user is not None:
            await allowed_user.delete()
        raise HTTPException(
            status_code=500,
            detail=e,
        )


# Read all allowed users (Only the admin can do this)
@router.get(
    "/",
    response_model=List[AllowedUserResponse],
    dependencies=[Depends(RoleChecker(["admin"]))],
)
async def get_allowed_users():
    return await AllowedUsers.all()


@router.get(
    "/{id}",
    response_model=AllowedUserResponse,
    dependencies=[Depends(RoleChecker(["admin"]))],
)
async def get_allowed_user(id: int):
    allowed_user = await AllowedUsers.get_or_none(id=id)
    if allowed_user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dit e-mailadres komt niet voor in de lijst met toegestane gebruikers",
        )
    else:
        return allowed_user


# Update allowed user
@router.put("/{id}", dependencies=[Depends(RoleChecker(["admin"]))])
async def update_allowed_user(
    id: int,
    update_request: AllowedUserRequest,
    background_tasks: BackgroundTasks,
):
    allowed_user = await AllowedUsers.get_or_none(id=id)
    if allowed_user is None:
        raise HTTPException(
            status_code=404,
            detail="Gebruiker niet gevonden",
        )
    try:
        allowed_user.email = update_request.email
        await allowed_user.save()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e,
        )
    email = EmailSchema(
        recipient_addresses=[allowed_user.email],
        body={
            "base_url": os.getenv("BASE_URL_FRONTEND"),
            "sender": "Gebroeders Vroege",
        },
    )
    background_tasks.add_task(Mailer.send_invitation_message, email=email)
    return allowed_user


# Delete allowed user
@router.delete("/{id}", dependencies=[Depends(RoleChecker(["admin"]))])
async def delete_allowed_user(id: int):
    allowed_user = await AllowedUsers.get_or_none(id=id)
    if allowed_user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dit e-mailadres komt niet voor in de lijst met toegestane gebruikers",
        )
    else:
        await allowed_user.delete()
        return allowed_user

import os
from typing import List

from app.config import get_fastapi_mail_config
from app.models.pydantic import (
    AllowedUsersCreateSchema,
    AllowedUsersUpdateschema,
    AllowedUsersResponseSchema,
    EmailSchema,
    ResponseMessage,
)
from app.models.tortoise import AllowedUsers, Users
from app.services.v1.auth import RoleChecker
from app.services.v1.mail import Mailer
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from fastapi.param_functions import Depends
from fastapi_mail import ConnectionConfig
from starlette import status

router = APIRouter()

# CRUD Implementation for allowed users


# Create allowed user (only the admin can do this)
@router.post(
    "/",
    response_model=AllowedUsersResponseSchema,
    status_code=201,
    dependencies=[Depends(RoleChecker(["admin"]))],
    responses={400: {"model": ResponseMessage}, 500: {"model": ResponseMessage}},
)
async def post_allowed_users(
    added_user: AllowedUsersCreateSchema,
) -> AllowedUsersResponseSchema:
    if await AllowedUsers.get_or_none(email=added_user.email.lower()) is not None:
        return JSONResponse(
            status_code=400,
            content={
                "detail": "Er is al een uitnodiging gestuurd naar dit e-mailadres"
            },
        )
    elif await Users.get_or_none(email=added_user.email) is not None:
        return JSONResponse(
            status_code=400, content={"detail": "Dit e-mailadres is al geregistreerd"}
        )
    # Add allowed user to database
    try:
        allowed_user = await AllowedUsers.create(email=added_user.email.lower())
    except:
        return JSONResponse(
            status_code=500,
            content={
                "detail",
                "Er is een onverwachte fout opgetreden bij het opslaan in de database",
            },
        )
    # Send email
    try:
        await Mailer.send_invitation_message(
            email=EmailSchema(
                recipient_addresses=[allowed_user.email],
                body={
                    "base_url": os.getenv("BASE_URL_FRONTEND"),
                    "sender": "Gebroeders Vroege",
                },
            ),
        )
    except:
        await allowed_user.delete()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Er is een onverwachte fout opgetreden bij het versturen van de email",
        )
    return allowed_user


# Read all allowed users (Only the admin can do this)
@router.get(
    "/",
    response_model=List[AllowedUsersResponseSchema],
    dependencies=[Depends(RoleChecker(["admin"]))],
)
async def get_allowed_users():
    return await AllowedUsers.all()


@router.get(
    "/{id}",
    response_model=AllowedUsersResponseSchema,
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
    user_to_update: AllowedUsersUpdateschema,
    config: ConnectionConfig = Depends(get_fastapi_mail_config),
):
    allowed_user = await AllowedUsers.get_or_none(id=id)
    if allowed_user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dit e-mailadres komt niet voor in de lijst met toegestane gebruikers",
        )
    else:
        allowed_user.email = user_to_update.email
        await allowed_user.save()
        # Send email
        try:
            await Mailer.send_invitation_message(
                email=EmailSchema(
                    recipient_addresses=[allowed_user.email],
                    body={
                        "base_url": os.getenv("BASE_URL_FRONTEND"),
                        "sender": "Gebroeders Vroege",
                    },
                ),
            )
        except:
            await allowed_user.delete()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Er is een overwachte fout opgetreden bij het versturen van de email",
            )
        return status.HTTP_200_OK


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

from app.models.tortoise import LoginStatusDevices
from app.services.v1.auth import Auth, get_current_user, get_current_active_user
from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import JSONResponse
from starlette import status
from fastapi.param_functions import Depends
from app.models.pydantic import LogoutRequest

router = APIRouter()


@router.get("/")
async def hello_world():
    return {"Hello, world"}


@router.get("/device_id_status")
async def get_device_id_status(device_id: str):
    login_status_device = await LoginStatusDevices.get_or_none(device_id=device_id)
    if login_status_device is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dit device is nog niet ingelogd geweest",
        )
    elif login_status_device.logged_in is False:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Login status van dit device is: uitgelogd",
        )
    else:
        # opgeslagen token decrypten en een nieuwe token maken op basis van de claims
        user = await get_current_user(
            token=login_status_device.last_provided_access_token
        )
        access_token = Auth.get_access_token(email=user.email)
        refresh_token = Auth.get_refresh_token(email=user.email)
        login_status_device.last_provided_access_token = access_token["token"]
        await login_status_device.save()
        return JSONResponse(
            {
                "access_token": access_token["token"],
                "refresh_token": refresh_token["token"],
                "token_type": "bearer",
            },
            status_code=200,
        )


@router.post("/login")
async def login_ionic(
    username: str = Form(default=""),
    password: str = Form(default=""),
    device_id: str = Form(default=""),
):
    user = await Auth.authenticate_user(email=username.lower(), password=password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email en/of wachtwoord onjuist",
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif user.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Gebruiker is nog niet geactiveerd!",
            headers={"WWW-Authenticate": "Bearer"},
        )
    else:
        access_token = Auth.get_access_token(email=user.email)
        refresh_token = Auth.get_refresh_token(email=user.email)
        # Kijken of er al een device login status aanwezig is, zo ja bijwerken, zo niet aanmaken
        device_login_status = await LoginStatusDevices.get_or_none(device_id=device_id)
        if device_login_status is None:
            await LoginStatusDevices.create(
                device_id=device_id,
                logged_in=True,
                user=user,
                last_provided_access_token=access_token["token"],
            )
        else:
            device_login_status.logged_in = True
            device_login_status.last_provided_access_token = access_token["token"]
            await device_login_status.save()

        return JSONResponse(
            {
                "access_token": access_token["token"],
                "refresh_token": refresh_token["token"],
                "token_type": "bearer",
            },
            status_code=200,
        )


@router.post("/logout")
async def logout_ionic(
    logoutRequestData: LogoutRequest,
    current_active_user=Depends(get_current_active_user),
):
    login_status_device = await LoginStatusDevices.get_or_none(
        device_id=logoutRequestData.device_id
    )
    if login_status_device is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dit device is nog niet ingelogd geweest",
        )
    else:
        await login_status_device.delete()
        return JSONResponse(
            {
                "message": f"Device ID {logoutRequestData.device_id} is succesvol uitgelogd"
            },
            status_code=200,
        )

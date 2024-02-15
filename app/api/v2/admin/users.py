from fastapi import APIRouter, Depends
from typing import List
from starlette.exceptions import HTTPException
from app.models.pydantic_models.users import UserResponse, UpdateUserRequest
from app.models.pydantic_models.roles import (
    AddRoleToUserRequest,
    RemoveRoleFromUserRequest,
)
from app.models.tortoise import Users, Roles
from app.services.v2.auth import RoleChecker

router = APIRouter()


@router.get(
    "/",
    response_model=List[UserResponse],
    dependencies=[Depends(RoleChecker(["admin"]))],
)
async def get_all_users():
    users = await Users.all().prefetch_related("roles", "address")
    return users


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    dependencies=[Depends(RoleChecker(["admin"]))],
)
async def get_user(user_id: int):
    user = await Users.get_or_none(id=user_id)
    if user is None:
        raise HTTPException(status_code=404, detail=f"Gebruiker niet gevonden")
    await user.fetch_related("roles", "address")
    return user


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    dependencies=[Depends(RoleChecker(["admin"]))],
)
async def update_user(user_id: int, update_user: UpdateUserRequest):
    user = await Users.get_or_none(id=user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Gebruiker niet gevonden")
    # fetch related roles and address
    await user.fetch_related("roles", "address")
    # updat the general info of the user
    await user.update_from_dict(update_user.dict(exclude_unset=True)).save()
    return user


@router.delete(
    "/{user_id}",
    dependencies=[Depends(RoleChecker(["admin"]))],
)
async def delete_user(user_id: int):
    user = await Users.get_or_none(id=user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Gebruiker niet gevonden")
    await user.delete()
    return {"message": "Gebruiker verwijderd"}


# UserRoles
@router.post(
    "/add_role_to_user/",
    response_model=UserResponse,
    dependencies=[Depends(RoleChecker(["admin"]))],
)
async def add_role_to_user(userRole: AddRoleToUserRequest):
    user = await Users.get_or_none(id=userRole.user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Gebruiker niet gevonden")
    role = await Roles.get_or_none(id=userRole.role_id)
    if role is None:
        raise HTTPException(status_code=404, detail="Role niet gevonden")
    await user.roles.add(role)
    await user.fetch_related("roles", "address")
    return user


@router.delete(
    "/remove_role_from_user/",
    response_model=UserResponse,
    dependencies=[Depends(RoleChecker(["admin"]))],
)
async def remove_role_from_user(userRoleToDelete: RemoveRoleFromUserRequest):
    user = await Users.get_or_none(id=userRoleToDelete.user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Gebruiker niet gevonden")
    role = await Roles.get_or_none(id=userRoleToDelete.role_id)
    if role is None:
        raise HTTPException(status_code=404, detail="Role niet gevonden")
    await user.roles.remove(role)
    await user.fetch_related("roles", "address")
    return user

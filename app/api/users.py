from fastapi import APIRouter
from typing import List

from fastapi.param_functions import Depends
from starlette.exceptions import HTTPException

from app.services.v1.auth import get_current_active_user, RoleChecker
from app.models.pydantic import (
    User_Pydantic,
    UpdateUser,
    ResponseMessage,
    UpdateAddress,
    AddUserRole,
    DeleteUserRole,
)
from app.models.tortoise import Users, Addresses, Roles

router = APIRouter()


@router.get("/me", response_model=User_Pydantic)
async def get_me(current_active_user=Depends(get_current_active_user)) -> User_Pydantic:
    return current_active_user


@router.put("/me", response_model=User_Pydantic)
async def update_me(
    update_user: UpdateUser, current_active_user=Depends(get_current_active_user)
) -> User_Pydantic:
    await current_active_user.update_from_dict(
        update_user.dict(exclude_unset=True)
    ).save()
    return current_active_user


# Admin routes


@router.get(
    "/",
    response_model=List[User_Pydantic],
    tags=["users", "admin"],
    dependencies=[Depends(RoleChecker(["admin"]))],
)
async def get_all_users():
    users = await Users.all().prefetch_related("roles", "address")
    return users


@router.get(
    "/{user_id}",
    response_model=User_Pydantic,
    tags=["users", "admin"],
    dependencies=[Depends(RoleChecker(["admin"]))],
)
async def get_user(user_id: int):
    user = await Users.get_or_none(id=user_id).prefetch_related("roles", "address")
    if user is None:
        raise HTTPException(status_code=404, detail=f"Gebruiker niet gevonden")
    return user


@router.put(
    "/{user_id}",
    response_model=User_Pydantic,
    tags=["users", "admin"],
    dependencies=[Depends(RoleChecker(["admin"]))],
)
async def update_user(user_id: int, update_user: UpdateUser):
    user = await Users.get_or_none(id=user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Gebruiker niet gevonden")
    # fetch related roles and address
    await user.fetch_related("roles", "address")
    # updat the general info of the user
    await user.update_from_dict(update_user.dict(exclude_unset=True)).save()
    return user


@router.put(
    "/address/{user_id}",
    response_model=User_Pydantic,
    tags=["users", "admin"],
    dependencies=[Depends(RoleChecker(["admin"]))],
)
async def update_user_address(user_id: int, update_address: UpdateAddress):
    user = await Users.get_or_none(id=user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Gebruiker niet gevonden")
    await user.fetch_related("address", "roles")
    # Update the user's address if it exists
    if user.address:
        address = await Addresses.get_or_none(user=user)
        await address.update_from_dict(update_address.dict(exclude_unset=True)).save()
    else:
        # Create a new address if it does not exist
        await Addresses.create(**update_address.dict(), user=user)
    return user


@router.post(
    "/add-role/",
    response_model=User_Pydantic,
    tags=["users", "admin"],
    dependencies=[Depends(RoleChecker(["admin"]))],
)
async def add_user_role(userRole: AddUserRole):
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
    "/delete-role/",
    response_model=User_Pydantic,
    tags=["users", "admin"],
    dependencies=[Depends(RoleChecker(["admin"]))],
)
async def add_user_role(userRoleToDelete: DeleteUserRole):
    user = await Users.get_or_none(id=userRoleToDelete.user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Gebruiker niet gevonden")
    role = await Roles.get_or_none(id=userRoleToDelete.role_id)
    if role is None:
        raise HTTPException(status_code=404, detail="Role niet gevonden")
    await user.roles.remove(role)
    await user.fetch_related("roles", "address")
    return user


@router.delete(
    "/{user_id}",
    tags=["users", "admin"],
    dependencies=[Depends(RoleChecker(["admin"]))],
    response_model=ResponseMessage,
)
async def delete_user(user_id: int):
    user = await Users.get_or_none(id=user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    await user.delete()
    return ResponseMessage(
        detail=f"Gebruiker met email-adres {user.email} is verwijderd"
    )

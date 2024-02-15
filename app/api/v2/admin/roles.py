from typing import List
from fastapi import APIRouter, Depends
from starlette.exceptions import HTTPException
from app.models.pydantic_models.auth import UserResponse
from app.models.pydantic_models.roles import (
    AddRoleToUserRequest,
    RemoveRoleFromUserRequest,
    RoleResponse,
    CreateRoleRequest,
)
from app.models.tortoise import Users, Roles
from app.services.v2.auth import RoleChecker


router = APIRouter()


#  Roles
@router.post(
    "/",
    response_model=RoleResponse,
    dependencies=[Depends(RoleChecker(["admin"]))],
)
async def create_role(role_to_create: CreateRoleRequest):
    role = await Roles.get_or_none(name=role_to_create.name)
    if role:
        raise HTTPException(status_code=400, detail="Rol met deze naam bestaat al")
    role_created = await Roles.create(
        name=role_to_create.name, description=role_to_create.description
    )
    return role_created


@router.get(
    "/",
    response_model=List[RoleResponse],
    dependencies=[Depends(RoleChecker(["admin"]))],
)
async def get_all_roles():
    return await Roles.all()


@router.delete(
    "/{role_id}",
    dependencies=[Depends(RoleChecker(["admin"]))],
)
async def delete_role(role_id: int):
    role = await Roles.get_or_none(id=role_id)
    if role is None:
        raise HTTPException(status_code=404, detail="Rol niet gevonden")
    await role.delete()
    return {"detail": "Rol verwijderd"}

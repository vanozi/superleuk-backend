from os import name
from fastapi import APIRouter, HTTPException, Depends
from app.models.pydantic import RolesSchema
from app.models.tortoise import Roles

from typing import List

from app.services.v1.auth import RoleChecker


router = APIRouter()


@router.post(
    "/", response_model=RolesSchema, dependencies=[Depends(RoleChecker(["admin"]))]
)
async def create_role(role: RolesSchema):
    role = Roles.get_or_none(name=role.name)
    if role:
        raise HTTPException(status_code=400, detail="Role already exists")
    role = await Roles.create(name=role.name, description=role.description)
    return role


@router.get(
    "/",
    response_model=List[RolesSchema],
    dependencies=[Depends(RoleChecker(["admin"]))],
)
async def get_all_roles():
    return await Roles.all()

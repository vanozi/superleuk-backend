from os import name
from fastapi import APIRouter, HTTPException, Depends
from app.models.pydantic import User_Pydantic
from app.models.tortoise import Roles, Users

from app.services.v1.auth import RoleChecker


router = APIRouter()


@router.post(
    "/", response_model=User_Pydantic, dependencies=[Depends(RoleChecker(["admin"]))]
)
async def create_user_role(email: str, role: str):
    # add user roles
    user = await Users.get_or_none(email=email)
    if user is None:
        raise HTTPException(status_code=400, detail="User does not exist")
    role = Roles.get_or_none(name=role)
    if role is None:
        raise HTTPException(status_code=400, detail="Role does not exist")
    await user.roles.add(role)
    await user.fetch_related("roles")
    return user

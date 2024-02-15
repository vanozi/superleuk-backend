from fastapi import APIRouter

from fastapi.param_functions import Depends

from app.services.v2.auth import get_current_active_user
from app.models.pydantic_models.users import (
    UpdateUserRequest,
)
from app.models.pydantic_models.auth import UserResponse

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_me(current_active_user=Depends(get_current_active_user)) -> UserResponse:
    return current_active_user


@router.put("/me", response_model=UserResponse)
async def update_me(
    update_user: UpdateUserRequest, current_active_user=Depends(get_current_active_user)
) -> UserResponse:
    await current_active_user.update_from_dict(
        update_user.model_dump(exclude_unset=True)
    ).save()
    return current_active_user

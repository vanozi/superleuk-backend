from typing import List
from fastapi import APIRouter, Depends
from starlette.exceptions import HTTPException
from app.models.pydantic_models.auth import UserResponse
from app.models.tortoise import Users, Addresses
from app.models.pydantic_models.address import UpdateAddressRequest
from app.services.v2.auth import RoleChecker


router = APIRouter()


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    dependencies=[Depends(RoleChecker(["admin"]))],
)
async def update_user_address(user_id: int, update_address: UpdateAddressRequest):
    user = await Users.get_or_none(id=user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Gebruiker niet gevonden")
    await user.fetch_related("address", "roles")
    # Update the user's address if it exists
    if user.address:
        address = await Addresses.get_or_none(user=user)
        await address.update_from_dict(
            update_address.model_dump(exclude_unset=True)
        ).save()
    else:
        # Create a new address if it does not exist
        await Addresses.create(**update_address.model_dump(), user=user)
    return user

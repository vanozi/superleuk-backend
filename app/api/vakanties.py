from datetime import date
from typing import List

from starlette import status

from app.models.pydantic import (
    VakantieCreateSchema,
    VakantiesResponseSchema,
    VakantiesAllResponseSchema,
    VakantieCreateSchemaForUserAsAdmin,
)
from app.models.tortoise import Vakanties, Users
from app.services.v1.auth import RoleChecker
from fastapi import APIRouter, HTTPException
from fastapi.param_functions import Depends
from fastapi.responses import JSONResponse

from app.services.v1.auth import get_current_active_user

router = APIRouter()


@router.post(
    "/",
    dependencies=[Depends(get_current_active_user)],
    response_model=VakantiesResponseSchema,
)
async def add_vakantie(
    vakantie: VakantieCreateSchema, current_active_user=Depends(get_current_active_user)
):
    # alle vakanties van de user ophalen
    vakanties = await Vakanties.all().filter(user=current_active_user)
    # als er geen vakanties zijn dan kun je gerust toevoegen
    if vakanties is None:
        try:
            return await Vakanties.create(
                **vakantie.dict(exclude_none=True),
                created_by=current_active_user.email,
                last_modified_by=current_active_user.email,
                user=current_active_user,
            )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    "Er is een onverwachte fout opgetreden, neem contact op met de beheerder"
                ),
            )
    # checken of er overlap is met een bestaande vakantie
    else:
        # checken of de nieuwe vakantie overlapt met een bestaande vakantie
        for vakantie_item in vakanties:
            if (
                vakantie_item.start_date <= vakantie.end_date
                and vakantie_item.end_date >= vakantie.start_date
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"De nieuwe vakantie overlapt met een bestaande vakantie van {vakantie_item.start_date} tot {vakantie_item.end_date}"
                    ),
                )
        # als er geen overlap is dan kun je de vakantie toevoegen
        try:
            return await Vakanties.create(
                **vakantie.dict(exclude_none=True),
                created_by=current_active_user.email,
                last_modified_by=current_active_user.email,
                user=current_active_user,
            )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    "Er is een onverwachte fout opgetreden, neem contact op met de beheerder"
                ),
            )


@router.post(
    "/admin/add_vakantie_for_user",
    dependencies=[Depends(get_current_active_user), Depends(RoleChecker(["admin"]))],
    response_model=VakantiesResponseSchema,
)
async def add_vakantie_for_other_as_admin(
    vakantie: VakantieCreateSchemaForUserAsAdmin,
    current_active_user=Depends(get_current_active_user),
):
    # check if user bestaat
    user = await Users.get_or_none(id=vakantie.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(f"De user met id {vakantie.user_id} bestaat niet"),
        )
    # alle vakanties van de user ophalen
    vakanties = await Vakanties.all().filter(user=vakantie.user_id)
    # als er geen vakanties zijn dan kun je gerust toevoegen
    if vakanties is None:
        try:
            return await Vakanties.create(
                **vakantie.dict(exclude_none=True),
                created_by=current_active_user.email,
                last_modified_by=current_active_user.email,
                user=vakantie.user_id,
            )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    "Er is een onverwachte fout opgetreden, neem contact op met de beheerder"
                ),
            )
    # checken of er overlap is met een bestaande vakantie
    else:
        # checken of de nieuwe vakantie overlapt met een bestaande vakantie
        for vakantie_item in vakanties:
            if (
                vakantie_item.start_date <= vakantie.end_date
                and vakantie_item.end_date >= vakantie.start_date
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"De nieuwe vakantie overlapt met een bestaande vakantie van {vakantie_item.start_date} tot {vakantie_item.end_date}"
                    ),
                )
        # als er geen overlap is dan kun je de vakantie toevoegen
        try:
            return await Vakanties.create(
                **vakantie.dict(),
                created_by=current_active_user.email,
                last_modified_by=current_active_user.email,
                user=user,
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    "Er is een onverwachte fout opgetreden, neem contact op met de beheerder"
                ),
            )


@router.get(
    "/",
    dependencies=[Depends(RoleChecker(["werknemer"]))],
    response_model=List[VakantiesResponseSchema],
)
async def get_vakanties_for_logged_in_user(
    current_active_user=Depends(get_current_active_user)
):
    vakanties = (
        await Vakanties.all().filter(user=current_active_user).order_by("-start_date")
    )
    return vakanties


@router.get(
    "/all",
    dependencies=[Depends(RoleChecker(["admin"]))],
    response_model=List[VakantiesAllResponseSchema],
)
async def get_all_vakanties():
    vakanties = await Vakanties.all().prefetch_related("user__roles", "user__address")

    return vakanties


@router.get(
    "/all_between_dates",
    dependencies=[Depends(RoleChecker(["admin", "werknemer", "monteur"]))],
    response_model=List[VakantiesAllResponseSchema],
)
async def get_all_vakanties_between_dates(start_date: date, end_date: date):
    vakanties = await Vakanties.filter(
        start_date__lte=end_date, end_date__gte=start_date
    ).prefetch_related("user__roles", "user__address")

    return vakanties


@router.delete("/{vakantie_id}", dependencies=[Depends(RoleChecker(["werknemer"]))])
async def delete_vakantie(
    vakantie_id: int, current_active_user=Depends(get_current_active_user)
):
    vakantie = await Vakanties.get_or_none(id=vakantie_id)
    await vakantie.fetch_related("user")
    if vakantie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(f"De vakantie met id {vakantie_id} is niet gevonden"),
        )
    if vakantie.user != current_active_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(f"Je mag alleen je eigen vakanties verwijderen"),
        )
    await vakantie.delete()
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": f"De vakantie met id {vakantie_id} is verwijderd"},
    )

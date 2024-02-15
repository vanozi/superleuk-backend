from datetime import date
from typing import List

from starlette import status

from app.models.pydantic import (
    VakantieCreateSchema,
    VakantiesResponseSchema,
    VakantiesAllResponseSchema,
    VakantieCreateSchemaForUserAsAdmin,
)
from app.models.pydantic_models.vakanties import (
    VakantieRequest,
    VakantieResponse,
    ResourceResponse,
    VakantiesForCalendarResponse,
)
from app.models.tortoise import Vakanties, Users
from app.services.v2.auth import RoleChecker, get_current_active_user
from fastapi import APIRouter, HTTPException
from fastapi.param_functions import Depends
from fastapi.responses import JSONResponse


router = APIRouter()


@router.get("/resources", response_model=List[ResourceResponse])
async def get_all_resources():
    users = await Users.all().prefetch_related("roles")
    # Create a list to store the ResourceResponse instances
    resource_responses = []

    # Loop over users and check if they have the 'werknemer' role before creating ResourceResponse instances
    for user in users:
        has_werknemer_role = False
        for role in user.roles:
            if role.name == "werknemer":
                has_werknemer_role = True
                break

        if has_werknemer_role:
            if any(role.name == "part-time" for role in user.roles):
                groupId = 2
            else:
                groupId = 1
            resource_response = ResourceResponse(
                id=user.id,
                title=user.first_name + " " + user.last_name,
                groupId=groupId,
            )
            resource_responses.append(resource_response)
    return resource_responses


@router.post(
    "/",
    dependencies=[Depends(get_current_active_user)],
)
async def add_vakantie(
    vakantie: VakantieRequest, current_active_user=Depends(get_current_active_user)
):
    # alle vakanties van de user ophalen
    vakanties = await Vakanties.all().filter(user=current_active_user)
    # als er geen vakanties zijn dan kun je gerust toevoegen
    if vakanties is None:
        try:
            await Vakanties.create(
                **vakantie.dict(exclude_none=True),
                created_by=current_active_user.email,
                last_modified_by=current_active_user.email,
                user=current_active_user,
            )
            return {
                "detail": f"De vakantie van {vakantie.start_date} tot {vakantie.end_date} is toegevoegd"
            }
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
            await Vakanties.create(
                **vakantie.model_dump(exclude_none=True),
                created_by=current_active_user.email,
                last_modified_by=current_active_user.email,
                user=current_active_user,
            )
            return {
                "detail": f"De vakantie van {vakantie.start_date} tot {vakantie.end_date} is toegevoegd"
            }
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
    response_model=VakantieResponse,
)
async def add_vakantie_for_other_as_admin(
    vakantie: VakantieCreateSchemaForUserAsAdmin,
    current_active_user=Depends(get_current_active_user),
    response_code=status.HTTP_201_CREATED,
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
            await Vakanties.create(
                **vakantie.dict(exclude_none=True),
                created_by=current_active_user.email,
                last_modified_by=current_active_user.email,
                user=vakantie.user_id,
            )
            return {
                "detail": f"De vakantie van {vakantie.start_date} tot {vakantie.end_date} is toegevoegd"
            }
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
            await Vakanties.create(
                **vakantie.model_dump(),
                created_by=current_active_user.email,
                last_modified_by=current_active_user.email,
                user=user,
            )
            return {
                "detail": f"De vakantie van {vakantie.start_date} tot {vakantie.end_date} is toegevoegd"
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    "Er is een onverwachte fout opgetreden, neem contact op met de beheerder"
                ),
            )


@router.get(
    "/all_for_me",
    dependencies=[Depends(RoleChecker(["werknemer"]))],
    response_model=List[VakantieResponse],
)
async def get_vakanties_for_logged_in_user(
    current_active_user=Depends(get_current_active_user),
):
    vakanties = (
        await Vakanties.all().filter(user=current_active_user).order_by("-start_date")
    )
    return vakanties


@router.get(
    "/all",
    dependencies=[Depends(RoleChecker(["admin", "werknemer"]))],
    response_model=List[VakantiesForCalendarResponse],
)
async def get_all_vakanties():
    vakanties_in_db = await Vakanties.all().prefetch_related("user__roles")
    # Create a list to store the VakantieResponse instances
    vakantie_responses = []
    # Loop over vakanties_in_db and create VakantieResponse instances
    for vakantie in vakanties_in_db:
        vakantie_response = VakantiesForCalendarResponse(
            id=vakantie.id,
            start=vakantie.start_date,
            end=vakantie.end_date,
            resourceId=vakantie.user.id,
        )

        vakantie_responses.append(vakantie_response)

    return vakantie_responses


@router.get(
    "/all_between_dates",
    dependencies=[Depends(RoleChecker(["admin", "werknemer", "monteur"]))],
    response_model=List[VakantieResponse],
)
async def get_all_vakanties_between_dates(start_date: date, end_date: date):
    vakanties_in_db = await Vakanties.filter(
        start_date__lte=end_date, end_date__gte=start_date
    )
    # Create a list to store the VakantieResponse instances
    vakantie_responses = []

    # Loop over vakanties_in_db and create VakantieResponse instances
    for vakantie in vakanties_in_db:
        vakantie_response = VakantieResponse(
            id=vakantie.id,
            start_date=vakantie.start_date,
            end_date=vakantie.end_date,
            resource_id=vakantie.user.id,
        )
        vakantie_responses.append(vakantie_response)
    return vakantie_responses


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

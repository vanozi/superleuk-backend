import os
from typing import List

from app.models.pydantic import (
    GeneralMaintenanceResponseSchema,
    GeneralMaintenanceCreateSchema,
    GeneralMaintenanceUpdateSchema,
)
from app.models.tortoise import GeneralMaintenance
from app.services.v1.auth import RoleChecker, get_current_active_user
from fastapi import APIRouter, HTTPException
from fastapi.param_functions import Depends
from starlette import status

router = APIRouter()

# CRUD Implementation for general maintenace


# Create a gemeral maitenace issue, all users should be able to do this
@router.post("/", response_model=GeneralMaintenanceResponseSchema, status_code=201)
async def post_general_maintenance(
    maintenance_issue: GeneralMaintenanceCreateSchema,
    current_active_user=Depends(get_current_active_user),
) -> GeneralMaintenanceResponseSchema:
    # Add maintenace issue to the database
    try:
        maintenace_issue = await GeneralMaintenance.create(
            description=maintenance_issue.description,
            created_by=current_active_user.email,
            last_modified_by=current_active_user.email,
        )
    except:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Er is een onverwachte fout opgetreden, neem contact op met de beheerder",
        )
    return maintenace_issue


# Read all maintenace issues (Only the admin can do this)
@router.get(
    "/",
    response_model=List[GeneralMaintenanceResponseSchema],
    dependencies=[Depends(get_current_active_user)],
)
async def get_all_general_maintenace():
    return await GeneralMaintenance.all().order_by("-created_at")


# Read single general maintenace issue
@router.get(
    "/{id}",
    response_model=GeneralMaintenanceResponseSchema,
    dependencies=[Depends(get_current_active_user)],
)
async def get_general_maintenace(id: int):
    general_maintenance = await GeneralMaintenance.get_or_none(id=id)
    if general_maintenance is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dit object komt niet voor in de database",
        )
    else:
        return general_maintenance


# Update allowed user
@router.put("/{id}", dependencies=[Depends(get_current_active_user)])
async def update_general_maintenace(
    id: int,
    maintenace_issue_to_update: GeneralMaintenanceUpdateSchema,
    current_active_user=Depends(get_current_active_user),
):
    general_maintenance = await GeneralMaintenance.get_or_none(id=id)
    if general_maintenance is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dit object komt niet voor in de database",
        )
    else:
        general_maintenance.description = maintenace_issue_to_update.description
        general_maintenance.last_modified_by = current_active_user.email
        await general_maintenance.save()
        return general_maintenance


# Delete general maintenance issue
@router.delete("/{id}", dependencies=[Depends(get_current_active_user)])
async def delete_allowed_user(id: int):
    general_maintenance = await GeneralMaintenance.get_or_none(id=id)
    if general_maintenance is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dit object komt niet voor in de database",
        )
    else:
        await general_maintenance.delete()
        return general_maintenance

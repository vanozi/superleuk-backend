from typing import List

from app.models.pydantic import (
    MachineMaintenanceCreate,
    MachineMaintenanceResponseSchema,
    MachineMaintenanceUpdate,
)
from app.services.v1.auth import get_current_active_user
from fastapi import APIRouter, HTTPException
from fastapi.param_functions import Depends
from starlette import status
from starlette.responses import JSONResponse

from app.models.tortoise import MaintenanceMachines, Machines, Users


router = APIRouter()


@router.post(
    "/",
    status_code=201,
    response_model=MachineMaintenanceResponseSchema,
)
async def post_machine_maintenance_issue(
    incoming_issue: MachineMaintenanceCreate,
    current_active_user=Depends(get_current_active_user),
):
    # Check if work number already exists
    machine = await Machines.get_or_none(id=incoming_issue.machine_id)
    if machine is not None:
        # create new machine maintenance issue
        try:
            maintenace_issue = await MaintenanceMachines.create(
                issue_description=incoming_issue.issue_description,
                status=incoming_issue.status,
                machine=machine,
                created_by=current_active_user.email,
                last_modified_by=current_active_user.email,
                user=current_active_user,
            )
            return maintenace_issue
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Er is een onverwachte fout opgetreden, neem contact op met de beheerder",
            )

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Machine niet bekend",
        )


@router.put(
    "/",
    status_code=200,
    response_model=MachineMaintenanceResponseSchema,
)
async def update_machine_maintenance_issue(
    updated_maintenance_issue: MachineMaintenanceUpdate,
    current_active_user=Depends(get_current_active_user),
):
    # Check if work number already exists
    maintenance_issue = await MaintenanceMachines.get_or_none(
        id=updated_maintenance_issue.id
    )
    if maintenance_issue is not None:
        try:
            # Update machine maintenance issue
            maintenance_issue.update_from_dict(updated_maintenance_issue.dict())
            maintenance_issue.last_modified_by = current_active_user.email
            await maintenance_issue.save()
            await maintenance_issue.fetch_related("machine")
            user = await Users.get_or_none(email=maintenance_issue.created_by)
            await user.fetch_related("roles", "address")
            maintenance_issue.user = user
            return maintenance_issue
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Er is een onverwachte fout opgetreden, neem contact op met de beheerder",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Onderhouds issue niet bekend",
        )


@router.get("/", status_code=200, response_model=List[MachineMaintenanceResponseSchema])
async def get_maintenance_issues(
    current_active_user=Depends(get_current_active_user),
) -> List[MachineMaintenanceResponseSchema]:
    maintenance_issues = (
        await MaintenanceMachines.all()
        .prefetch_related("machine", "user__roles", "user__address")
        .order_by("-created_at")
    )
    return maintenance_issues


@router.get("/{id}", status_code=200, response_model=MachineMaintenanceResponseSchema)
async def get_single_maintenance_issues(
    id: int, current_active_user=Depends(get_current_active_user)
) -> MachineMaintenanceResponseSchema:
    maintenance_issue = await MaintenanceMachines.get_or_none(id=id)
    if maintenance_issue is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Onderhouds issue niet gevonden",
        )
    user_reported = await Users.get_or_none(id=maintenance_issue.user_id)
    await user_reported.fetch_related("roles")
    maintenance_issue.user = user_reported
    await maintenance_issue.fetch_related("machine")
    return maintenance_issue


@router.delete("/{id}", status_code=200)
async def delete_single_maintenance_issue(id: int):
    maintenance_issue = await MaintenanceMachines.get_or_none(id=id)
    if maintenance_issue is not None:
        await maintenance_issue.delete()
        return JSONResponse(
            {"detail": "Onderhouds issue succesvol verwijderd"}, status_code=200
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Onderhouds issue is niet gevonden",
        )

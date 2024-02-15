import os
from platform import machine
from typing import List

from app.models.pydantic import (
    MachineCreateSchema,
    MachineResponseSchema,
    SingleMachineDataReponse,
)
from app.models.tortoise import Machines, TankTransactions
from app.services.v1.auth import RoleChecker, get_current_active_user
from fastapi import APIRouter, HTTPException
from fastapi.param_functions import Depends
from starlette import status
from starlette.responses import JSONResponse

from app.models.tortoise import MaintenanceMachines


router = APIRouter()


@router.post(
    "/",
    dependencies=[Depends(RoleChecker(["admin", "monteur"]))],
    status_code=201,
    response_model=MachineResponseSchema,
)
async def post_machine(
    incoming_machine: MachineCreateSchema,
    current_active_user=Depends(get_current_active_user),
):
    # Check if work number already exists
    machine = await Machines.get_or_none(work_number=incoming_machine.work_number)
    if machine is None:
        # create new machine
        try:
            machine = await Machines.create(
                **incoming_machine.dict(),
                created_by=current_active_user.email,
                last_modified_by=current_active_user.email,
            )
        except:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Er is een onverwachte fout opgetreden, neem contact op met de beheerder",
            )
        return machine
    else:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Machine met werknummer {incoming_machine.work_number} bestaat al",
        )


@router.put(
    "/",
    dependencies=[Depends(RoleChecker(["admin", "monteur"]))],
    status_code=200,
    response_model=MachineResponseSchema,
)
async def update_machine(
    incoming_machine: MachineCreateSchema,
    current_active_user=Depends(get_current_active_user),
):
    # Check if work number already exists
    machine = await Machines.get_or_none(work_number=incoming_machine.work_number)
    if machine is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Machine met werknummer {incoming_machine.work_number} niet gevonden",
        )
    else:
        await machine.update_from_dict(incoming_machine.dict()).save()
        machine = await Machines.get(work_number=incoming_machine.work_number)
        return machine


@router.get("/", status_code=200, response_model=List[MachineResponseSchema])
async def get_machines(
    current_active_user=Depends(get_current_active_user),
) -> List[MachineResponseSchema]:
    return await Machines.all()


@router.get("/{id}", status_code=200, response_model=SingleMachineDataReponse)
async def get_single_machines(
    id: int, current_active_user=Depends(get_current_active_user)
) -> SingleMachineDataReponse:
    machine = await Machines.get_or_none(id=id)
    if machine is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Machine met ID {id} niet gevonden",
        )
    maintenance_issues = await MaintenanceMachines.filter(machine=machine.id)
    tank_transactions = await TankTransactions.filter(vehicle=machine.work_name)

    return {
        "info": machine,
        "maintenance_issues": maintenance_issues,
        "tank_transactions": tank_transactions,
    }


@router.delete(
    "/{id}", status_code=200, dependencies=[Depends(RoleChecker(["admin", "monteur"]))]
)
async def delete_single_machine(id: int):
    machine = await Machines.get_or_none(id=id)
    if machine is not None:
        await machine.delete()
        return JSONResponse({"detail": "Machine succesvol verwijderd"}, status_code=200)
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Machine niet gevonden",
        )

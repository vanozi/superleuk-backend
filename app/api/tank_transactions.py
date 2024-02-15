import os
from collections import Counter
from datetime import date
from functools import reduce
from operator import add
from platform import machine
from typing import List

from app.models.pydantic import (
    TankTransactionCreate,
    TankTransactionResponseSchema,
)
from app.models.tortoise import TankTransactions
from app.services.v1.auth import RoleChecker, get_current_active_user
from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, HTTPException
from fastapi.param_functions import Depends
from starlette import status
from starlette.responses import JSONResponse

router = APIRouter()


@router.post(
    "/",
    status_code=201,
    response_model=TankTransactionResponseSchema,
)
async def post_tank_transaction(
    incoming_tank_transaction: TankTransactionCreate,
):
    # Check if work number already exists
    transaction = await TankTransactions.get_or_none(
        start_date_time=incoming_tank_transaction.start_date_time
    )
    if transaction is None:
        # create new machine
        try:
            transaction = await TankTransactions.create(
                **incoming_tank_transaction.dict(),
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Er is een onverwachte fout opgetreden, neem contact op met de beheerder",
            )
        return transaction
    else:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Tank transactie bestaat al op basis van start tijd tank beurt",
        )


@router.get("/", status_code=200, response_model=List[TankTransactionResponseSchema])
async def get_tank_transactions(
    current_active_user=Depends(get_current_active_user),
) -> List[TankTransactionResponseSchema]:
    return (
        await TankTransactions.all()
        .exclude(vehicle="Klein materiaal")
        .order_by("-start_date_time")
    )


@router.get("/{id}", status_code=200, response_model=TankTransactionResponseSchema)
async def get_tank_transaction_by_id(
    id: int, current_active_user=Depends(get_current_active_user)
) -> TankTransactionResponseSchema:
    transactie = await TankTransactions.get_or_none(id=id)
    if transactie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tank transactie met {id} niet gevonden",
        )
    return transactie


@router.get(
    "/vehicle/{werk_naam}",
    status_code=200,
    response_model=List[TankTransactionResponseSchema],
)
async def get_tank_transactions_by_vehicle(
    werk_naam: str, current_active_user=Depends(get_current_active_user)
) -> List[TankTransactionResponseSchema]:
    transacties = await TankTransactions.filter(vehicle=werk_naam).order_by(
        "-start_date_time"
    )
    if transacties == []:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Geen transacties voor {werk_naam} gevonden",
        )
    return transacties


@router.delete("/{id}", status_code=200, dependencies=[Depends(RoleChecker(["admin"]))])
async def delete_single_machine(id: int):
    transactie = await TankTransactions.get_or_none(id=id)
    if transactie is not None:
        await transactie.delete()
        return JSONResponse(
            {"detail": "Tank transactie succesvol verwijderd"}, status_code=200
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tank transactie niet gevonden",
        )


# Methods for charts
@router.get("/summed_quantity/between_dates", status_code=200)
async def get_data_for_chart_between_two_dates(
    from_date: date = date.today() - relativedelta(months=1),
    to_date: date = date.today(),
    current_active_user=Depends(get_current_active_user),
):
    data = []
    transactions = (
        await TankTransactions.filter(
            start_date_time__gte=from_date, start_date_time__lte=to_date
        )
        .exclude(vehicle="Klein materiaal")
        .order_by("start_date_time")
    )
    for transaction in transactions:
        list_item = {
            transaction.start_date_time.strftime("%Y-%m-%d"): int(transaction.quantity)
        }
        data.append(list_item)
    sum_dict = reduce(add, (map(Counter, data)))
    return sum_dict

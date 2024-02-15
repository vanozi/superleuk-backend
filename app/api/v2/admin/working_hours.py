from typing import List
import datetime

from app.services.v2.auth import get_current_active_user

from fastapi import APIRouter, HTTPException
from fastapi.param_functions import Depends
from babel.dates import format_date
from app.helpers.date_functions import (
    get_month_names,
    get_week_numbers,
    get_week_start_end_dates,
)
from app.services.v2.auth import RoleChecker
from app.models.tortoise import Users, WorkingHours
from app.models.pydantic_models.working_hours import (
    WorkingHoursWeekOverviewResponse,
    ReleaseRequest,
)
from starlette import status

router = APIRouter()


@router.get(
    "/year_overview/",
    dependencies=[Depends(RoleChecker(["admin"]))],
)
async def get_year_overview(year: int, user_id: int):
    user = await Users.get_or_none(id=user_id).prefetch_related("working_hours")

    # Initialize a dictionary to store aggregated data
    aggregated_data = {}

    # Iterate through records and aggregate by month
    for item in user.working_hours:
        if item.date.year == year:
            maand = format_date(item.date, "MMMM", locale="nl")
            if maand not in aggregated_data:
                aggregated_data[maand] = {
                    "month": maand,
                    "hours": 0,
                    "milkings": 0,
                }
            aggregated_data[maand]["hours"] += item.hours
            aggregated_data[maand]["milkings"] += item.milkings

    # Fill in missing months with dictionaries containing 0 hours and 0 milkings
    all_months = get_month_names("nl")
    for month in all_months:  # Translate to Dutch
        if month not in aggregated_data:
            aggregated_data[month] = {
                "month": month,
                "hours": 0,
                "milkings": 0,
            }

    return sorted(
        list(aggregated_data.values()),
        key=lambda x: get_month_names("nl").index(x["month"]),
    )


@router.get(
    "/week_overview/",
    response_model=List[WorkingHoursWeekOverviewResponse],
    dependencies=[Depends(RoleChecker(["admin"]))],
)
async def get_week_overview(
    from_date: datetime.date, to_date: datetime.date, user_id: int
):
    if from_date > to_date:
        raise HTTPException(
            status_code=400, detail="Van datum moet voor tot datum zijn"
        )
    # Retrieve all relevant data in one query (if possible)
    user = await Users.get_or_none(id=user_id)
    await user.fetch_related("working_hours")
    working_hours = await user.working_hours.filter(
        date__range=[from_date, to_date + datetime.timedelta(days=1)]
    )

    # Process the data
    result_list = []
    for year, week_number in get_week_numbers(from_date, to_date):
        week_hours = filter(
            lambda x: x.date.isocalendar()[:2] == (year, week_number), working_hours
        )
        week_hours_list = list(week_hours)

        sum_hours = sum(i.hours for i in week_hours_list)
        sum_milkings = sum(i.milkings for i in week_hours_list)
        submitted = (
            all(i.submitted for i in week_hours_list) if week_hours_list else False
        )

        week_start, week_end = get_week_start_end_dates(year, week_number)

        result_list.append(
            {
                "year": year,
                "week": week_number,
                "week_start": week_start.strftime("%Y-%m-%d"),
                "week_end": week_end.strftime("%Y-%m-%d"),
                "sum_hours": sum_hours,
                "sum_milkings": sum_milkings,
                "submitted": submitted,
                "working_hours": week_hours_list,  # Ensure this is serializable or transformed to match the response model
            }
        )

    return result_list


# Add or update a working hours item
@router.put(
    "/release",
    dependencies=[Depends(RoleChecker(["admin"]))],
    status_code=200,
)
async def release_working_hours(
    release_request: ReleaseRequest,
):
    # make a list of all dates between from_date and to_date including the from_date and to_date
    date_list = [
        release_request.from_date + datetime.timedelta(days=x)
        for x in range(
            0, (release_request.to_date - release_request.from_date).days + 1
        )
    ]
    # For all the dates in date list update the corresponding working hours item in the database and set submitted to False
    for date in date_list:
        working_hours_item = await WorkingHours.get_or_none(
            date=date, user=release_request.user_id
        )
        if working_hours_item is not None:
            try:
                await working_hours_item.update_from_dict({"submitted": False}).save()
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=(
                        "Er is een onverwachte fout opgetreden, neem contact op met de beheerder"
                    ),
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"Werkuren voor {date.strftime('%d-%m-%Y')} zijn niet gevonden"
                ),
            )
    return {"detail": "Werkuren zijn succesvol vrijgegeven"}

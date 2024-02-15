from typing import List

from app.services.v2.auth import get_current_active_user
from app.models.tortoise import WorkingHours
from app.models.pydantic_models.working_hours import (
    WorkingHoursResponse,
    WorkingHoursRequest,
    WorkingHoursWeekOverviewResponse,
)
from fastapi import APIRouter
from fastapi.param_functions import Depends
import datetime
from babel import Locale
from babel.dates import format_date
from starlette import status
from fastapi import HTTPException
from app.helpers.date_functions import (
    get_month_names,
    get_week_numbers,
    get_week_start_end_dates,
)

router = APIRouter()


@router.get(
    "/all",
    response_model=List[WorkingHoursResponse],
    dependencies=[Depends(get_current_active_user)],
)
async def get_all(
    current_active_user=Depends(get_current_active_user),
):
    await current_active_user.fetch_related("working_hours")
    return current_active_user.working_hours


@router.get("/between_dates/", response_model=List[WorkingHoursResponse])
async def get_working_hours_between_dates(
    from_date: datetime.date,
    to_date: datetime.date,
    current_active_user=Depends(get_current_active_user),
):
    await current_active_user.fetch_related("working_hours")
    return [
        x for x in current_active_user.working_hours if (from_date <= x.date <= to_date)
    ]


@router.get("/year_overview/", dependencies=[Depends(get_current_active_user)])
async def get_year_overview(
    year: int, current_active_user=Depends(get_current_active_user)
):
    await current_active_user.fetch_related("working_hours")

    # Initialize a dictionary to store aggregated data
    aggregated_data = {}

    # Iterate through records and aggregate by month
    for item in current_active_user.working_hours:
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
    dependencies=[Depends(get_current_active_user)],
)
async def get_week_overview(
    from_date: datetime.date,
    to_date: datetime.date,
    current_active_user=Depends(get_current_active_user),
):
    if from_date > to_date:
        raise HTTPException(
            status_code=400, detail="Van datum moet voor tot datum zijn"
        )
    # Retrieve all relevant data in one query (if possible)
    await current_active_user.fetch_related("working_hours")
    working_hours = await current_active_user.working_hours.filter(
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
@router.put("/", dependencies=[Depends(get_current_active_user)])
async def update_working_hours_item(
    request_data: WorkingHoursRequest,
    current_active_user=Depends(get_current_active_user),
):
    working_hours_item = await WorkingHours.get_or_none(
        date=request_data.date, user=current_active_user.id
    )

    if working_hours_item is None:
        try:
            working_hours_item = await WorkingHours.create(
                **request_data.model_dump(exclude_none=True),
                created_by=current_active_user.email,
                last_modified_by=current_active_user.email,
                user=current_active_user,
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    "Er is een onverwachte fout opgetreden, neem contact op met de"
                    " beheerder"
                ),
            )
        return working_hours_item
    else:
        try:
            data = request_data.model_dump(exclude_none=True)
            await working_hours_item.update_from_dict(data)
            await working_hours_item.save()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    "Er is een onverwachte fout opgetreden, neem contact op met de"
                    " beheerder"
                ),
            )
        return working_hours_item

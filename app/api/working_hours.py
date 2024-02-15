import datetime
from collections import Counter
from isoweek import Week
from typing import List

from app.helpers.date_functions import daterange
from app.models.pydantic import (
    WeeksNotSubmittedAllUsersResponseSchema,
    WorkingHoursResponseSchema,
    WeeksNotSubmittedSingleUsersResponseSchema,
    WorkingHoursUpdateSchema,
    WeekData,
)
from app.models.tortoise import Users, WorkingHours
from app.services.v1.auth import RoleChecker, get_current_active_user
from fastapi import APIRouter, HTTPException
from fastapi.param_functions import Depends
from starlette import status
from starlette.responses import JSONResponse

router = APIRouter()


# CRUD Implementation for general maintenace


# Add or update a working hours item
@router.put("/", dependencies=[Depends(get_current_active_user)])
async def update_working_hours_item(
    working_hours_issue_to_update: WorkingHoursUpdateSchema,
    current_active_user=Depends(get_current_active_user),
):
    working_hours_item = await WorkingHours.get_or_none(
        date=working_hours_issue_to_update.date, user=current_active_user.id
    )
    # if the working item cannot be found then we assume the user want to create a new one
    if working_hours_item is None:
        # lookup the user for whom the hours are submitted
        user = await Users.get_or_none(id=current_active_user.id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="De gebruiker waarvoor de uren zijn ingediend is niet bekend",
            )
        # Add working hour to the database
        try:
            working_hours_item = await WorkingHours.create(
                **working_hours_issue_to_update.dict(exclude_none=True),
                created_by=current_active_user.email,
                last_modified_by=current_active_user.email,
                user=user,
            )
        except Exception as e:
            print(e)
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
            data = working_hours_issue_to_update.dict(exclude_none=True)
            await working_hours_item.update_from_dict(data)
            await working_hours_item.save()
        except Exception as e:
            print(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    "Er is een onverwachte fout opgetreden, neem contact op met de"
                    " beheerder"
                ),
            )
        return working_hours_item


# All working hours
@router.get(
    "/all_for_user/{user_id}",
    response_model=List[WorkingHoursResponseSchema],
    dependencies=[Depends(get_current_active_user)],
)
async def get_working_hours_for_user(user_id: str):
    # lookup the user for whom the hours are submitted
    user = await Users.get_or_none(id=user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="De gebruiker waarvoor de uren zijn ingediend is niet bekend",
        )
    await user.fetch_related("working_hours")
    return list(user.working_hours)


# All working hours
@router.get(
    "/all",
    response_model=List[WorkingHoursResponseSchema],
    dependencies=[Depends(get_current_active_user)],
)
async def get_all_working_hours_for_logged_in_user(
    current_active_user=Depends(get_current_active_user),
):
    # lookup the user for whom the hours are submitted
    user = await Users.get_or_none(id=current_active_user.id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="De gebruiker waarvoor de uren zijn ingediend is niet bekend",
        )
    await user.fetch_related("working_hours")

    return list(user.working_hours)


# Read single working_hours item
@router.get(
    "",
    response_model=WorkingHoursResponseSchema,
    dependencies=[Depends(get_current_active_user)],
)
async def get_single_working_hours(id: int):
    working_hours_item = await WorkingHours.get_or_none(id=id)
    if working_hours_item is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dit object komt niet voor in de database",
        )
    else:
        return working_hours_item


# Delete working hours item
@router.delete("/{id}", dependencies=[Depends(get_current_active_user)])
async def delete_working_hours_item(id: int):
    working_hours_item = await WorkingHours.get_or_none(id=id)
    if working_hours_item is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dit object komt niet voor in de database",
        )
    else:
        await working_hours_item.delete()
        # Create a success respons
        return JSONResponse({"detail": "Uren succesvol verwijderd"}, status_code=200)


# Week overview for specific user between 2 dates
@router.get(
    "/week_overview/",
    response_model=WeeksNotSubmittedSingleUsersResponseSchema,
    dependencies=[Depends(get_current_active_user)],
)
async def get_week_overview(
    from_date: datetime.date, to_date: datetime.date, user_id: int
):
    # Create a list of week numbers for the date range
    week_numbers_from_date_range = list(
        dict.fromkeys(
            [
                (x.isocalendar()[0], x.isocalendar()[1])
                for x in daterange(from_date, to_date)
            ]
        )
    )

    # lookup the user for whom the hours are submitted
    user = await Users.get_or_none(id=user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="De gebruiker waarvoor de uren zijn ingediend is niet bekend",
        )
    await user.fetch_related("roles", "working_hours", "address")
    # loop over weeks and collect data
    result_list = []
    for item in week_numbers_from_date_range:
        year = item[0]
        week_number = item[1]
        week_start = Week(item[0], item[1]).monday()
        week_end = Week(item[0], item[1]).sunday()
        if user.created_at.date() > week_end:
            continue
        else:
            working_hours = await user.working_hours.filter(
                date__range=[week_start, week_end]
            )
            sum_hours = sum([i.hours for i in working_hours])
            sum_milkings = sum([i.milkings for i in working_hours])
            # check if after the user was created he did not register hours for a particular week
            submitted = (
                False
                if working_hours == [] and user.created_at.date() <= week_end
                else None
            )
            # if any of the working items
            for i in working_hours:
                submitted = False if i.submitted == False else True
                if submitted == False:
                    break
        result_list.append(
            {
                "year": year,
                "week": week_number,
                "week_start": datetime.date.strftime(week_start, "%Y-%m-%d"),
                "week_end": datetime.date.strftime(week_end, "%Y-%m-%d"),
                "sum_hours": sum_hours,
                "sum_milkings": sum_milkings,
                "submitted": submitted,
                "working_hours": working_hours,
            }
        )
    return {"werknemer": user, "week_data": result_list}


@router.get(
    "/my_week_overview/",
    response_model=List[WeekData],
    dependencies=[Depends(get_current_active_user)],
)
async def get_week_overview(
    from_date: datetime.date,
    to_date: datetime.date,
    user=Depends(get_current_active_user),
):
    # Create a list of week numbers for the date range
    week_numbers_from_date_range = set(
        (x.isocalendar()[0], x.isocalendar()[1]) for x in daterange(from_date, to_date)
    )

    result_list = []
    for year, week_number in sorted(week_numbers_from_date_range, reverse=True):
        week_start = Week(year, week_number).monday()
        week_end = Week(year, week_number).sunday()

        working_hours = await user.working_hours.filter(
            date__range=[week_start, week_end]
        )
        sum_hours = sum([i.hours for i in working_hours])
        sum_milkings = sum([i.milkings for i in working_hours])

        submitted = all(i.submitted for i in working_hours) if working_hours else False

        result_list.append(
            {
                "year": year,
                "week": week_number,
                "week_start": week_start.strftime("%Y-%m-%d"),
                "week_end": week_end.strftime("%Y-%m-%d"),
                "sum_hours": sum_hours,
                "sum_milkings": sum_milkings,
                "submitted": submitted,
                "working_hours": working_hours,
            }
        )

    return result_list


@router.get("/between_dates/", response_model=List[WorkingHoursResponseSchema])
async def get_working_hours_between_dates(
    from_date: datetime.date,
    to_date: datetime.date,
    current_user=Depends(get_current_active_user),
):
    user = await Users.get(id=current_user.id)
    await user.fetch_related("working_hours")
    working_hours = user.working_hours
    return [x for x in working_hours if (x.date >= from_date and x.date <= to_date)]


english_to_dutch_months = {
    "January": "januari",
    "February": "februari",
    "March": "maart",
    "April": "april",
    "May": "mei",
    "June": "juni",
    "July": "juli",
    "August": "augustus",
    "September": "september",
    "October": "oktober",
    "November": "november",
    "December": "december",
}


@router.get("/year_overview/", dependencies=[Depends(get_current_active_user)])
async def get_year_overview(year: int, current_user=Depends(get_current_active_user)):
    user = await Users.get(id=current_user.id)
    await user.fetch_related("working_hours")

    # Initialize a dictionary to store aggregated data
    aggregated_data = {}

    # Iterate through records and aggregate by month
    for item in user.working_hours:
        if item.date.year == year:
            month = item.date.strftime("%B")  # Get month name
            dutch_month = english_to_dutch_months.get(
                month, month
            )  # Translate to Dutch
            if dutch_month not in aggregated_data:
                aggregated_data[dutch_month] = {
                    "month": dutch_month,
                    "hours": 0,
                    "milkings": 0,
                }
            aggregated_data[dutch_month]["hours"] += item.hours
            aggregated_data[dutch_month]["milkings"] += item.milkings

    # Fill in missing months with dictionaries containing 0 hours and 0 milkings
    all_months = [
        datetime.datetime(year, month, 1).strftime("%B") for month in range(1, 13)
    ]
    for month in all_months:
        dutch_month = english_to_dutch_months.get(month, month)  # Translate to Dutch
        if dutch_month not in aggregated_data:
            aggregated_data[dutch_month] = {
                "month": dutch_month,
                "hours": 0,
                "milkings": 0,
            }

    # Convert aggregated data to a list of dictionaries and sort by month index
    result_list = sorted(
        list(aggregated_data.values()),
        key=lambda x: list(english_to_dutch_months.values()).index(
            english_to_dutch_months.get(x["month"], x["month"])
        ),
    )
    return result_list


@router.get(
    "/month_overview_for_year/", dependencies=[Depends(get_current_active_user)]
)
async def get_month_overview_year(
    year: int, current_user=Depends(get_current_active_user)
):
    user = await Users.get(id=current_user.id)
    await user.fetch_related("working_hours")
    working_hours = user.working_hours
    sum_hours = sum(
        (
            Counter({x.date.month: x.hours})
            for x in working_hours
            if (x.date.year == year) and (x.submitted is True)
        ),
        Counter(),
    )
    sum_milkings = sum(
        (
            Counter({x.date.month: x.milkings})
            for x in working_hours
            if (x.date.year == year) and (x.submitted is True)
        ),
        Counter(),
    )
    return [sum_hours, sum_milkings]


# admin routes
# Get weeks not submitted for all users in timerange
@router.get(
    "/admin/week_overview",
    response_model=List[WeeksNotSubmittedAllUsersResponseSchema],
    dependencies=[Depends(RoleChecker(["admin"]))],
)
async def get_week_overview_admin(from_date: datetime.date, to_date: datetime.date):
    # Create a list of week numbers for the date range
    week_numbers_from_date_range = list(
        dict.fromkeys(
            [
                (x.isocalendar()[0], x.isocalendar()[1])
                for x in daterange(from_date, to_date)
            ]
        )
    )

    # create a list of users with role werknemer
    werknemers = []
    users = await Users.all().filter(is_active=True)
    for user in users:
        await user.fetch_related("roles", "working_hours")
        for role in user.roles:
            if role.name == "werknemer":
                werknemers.append(user)
    # loop over weeks and collect data
    result_list = []
    for item in week_numbers_from_date_range:
        week_results = []
        year = item[0]
        week_number = item[1]
        week_start = Week(item[0], item[1]).monday()
        week_end = Week(item[0], item[1]).sunday()
        employee_hours = []
        for werknemer in werknemers:
            if werknemer.created_at.date() > week_end and werknemer.is_active == True:
                continue
            else:
                werknemer_info = {}
                werknemer_info["user_id"] = werknemer.id
                werknemer_info["name"] = f"{werknemer.first_name} {werknemer.last_name}"
                working_hours = await werknemer.working_hours.filter(
                    date__range=[week_start, week_end]
                )
                werknemer_info["working_hours"] = working_hours
                werknemer_info["sum_hours"] = sum([i.hours for i in working_hours])
                werknemer_info["sum_milkings"] = sum(
                    [i.milkings for i in working_hours]
                )
                # check if after the user was created he did not register hours for a particular week
                werknemer_info["submitted"] = (
                    False
                    if working_hours == [] and werknemer.created_at.date() < week_end
                    else None
                )
                # if any of the working items
                for i in working_hours:
                    werknemer_info["submitted"] = (
                        False if i.submitted == False else True
                    )
                    if werknemer_info["submitted"] == False:
                        break
                employee_hours.append(werknemer_info)

            week_results.append(werknemer_info)
        result_list.append(
            {
                "year": year,
                "week": week_number,
                "week_start": datetime.date.strftime(week_start, "%Y-%m-%d"),
                "week_end": datetime.date.strftime(week_end, "%Y-%m-%d"),
                "employee_info": week_results,
            }
        )
    return result_list


# admin routes
# Get weeks not submitted for all users in timerange
@router.get("/admin/unlock_week", dependencies=[Depends(RoleChecker(["admin"]))])
async def get_weeks_not_submitted(
    user_id: int, from_date: datetime.date, to_date: datetime.date
):
    # lookup the user for whom the hours are submitted
    user = await Users.get_or_none(id=user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="De gebruiker is niet bekend",
        )
    await user.fetch_related("working_hours")
    working_hours = await user.working_hours.filter(date__range=[from_date, to_date])
    for item in working_hours:
        item.submitted = False
        await item.save()

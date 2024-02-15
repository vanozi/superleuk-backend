import datetime
from babel.dates import format_date


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + datetime.timedelta(n)


def get_month_names(locale):
    month_names = []
    for month in range(1, 13):  # Looping through months 1 to 12
        # Creating a date object for each month (using any day, e.g., 1)
        date = datetime.date(2023, month, 1)
        # Formatting the date to get the full month name
        month_name = format_date(date, "MMMM", locale=locale)
        month_names.append(month_name)
    return month_names


def get_week_numbers(from_date, to_date):
    week_numbers = set()
    while from_date <= to_date:
        week_numbers.add(from_date.isocalendar()[:2])
        from_date += datetime.timedelta(days=7)
    return sorted(week_numbers, reverse=True)


def get_week_start_end_dates(year, week_number):
    week_start = datetime.date.fromisocalendar(year, week_number, 1)  # Monday
    week_end = datetime.date.fromisocalendar(year, week_number, 7)  # Sunday
    return week_start, week_end

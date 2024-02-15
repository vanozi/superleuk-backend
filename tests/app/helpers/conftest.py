import os
import pytest
import pandas as pd
import openpyxl

data = [
    {
        "ha": "",
        "link": "https://boerenbunder.nl/report/52.71662,6.77098",
        "gewas": "Mais",
        "opmerking": "",
        "perceel_nummer": "DE03",
        "werknaam": "Eldijk 3",
        "mest": "",
    },
    {
        "ha": 4.8877,
        "link": "https://boerenbunder.nl/report/52.70084,6.73582",
        "gewas": "Mais",
        "opmerking": "",
        "perceel_nummer": "DM01",
        "werknaam": "Reinder",
        "mest": "",
    },
]

data_to_assert = [
    {
        "ha": 0,
        "link": "https://boerenbunder.nl/report/52.71662,6.77098",
        "gewas": "Mais",
        "opmerking": "",
        "perceel_nummer": "DE03",
        "werknaam": "Eldijk 3",
        "mest": "",
    },
    {
        "ha": 4.89,
        "link": "https://boerenbunder.nl/report/52.70084,6.73582",
        "gewas": "Mais",
        "opmerking": "",
        "perceel_nummer": "DM01",
        "werknaam": "Reinder",
        "mest": "",
    },
]

@pytest.fixture
def valid_bouwplan_excel():
    filepath = "./tests/backend/app/helpersbouwplan.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    # append headers
    fieldnames = [
        "ha",
        "link",
        "gewas",
        "opmerking",
        "perceel_nummer",
        "werknaam",
        "mest",
    ]
    ws.append(
        ["ha", "link", "gewas", "opmerking", "perceel_nummer", "werknaam", "mest"]
    )
    # append data
    for item in data:
        # create a `generator` yield product `value`
        # use the fieldnames in desired order as `key`
        values = (item[k] for k in fieldnames)
    # append the `generator values`
    ws.append(values)
    wb.save(filepath)
    yield filepath
    os.remove(filepath)

from typing import List

import pytest
from app.models.pydantic import BouwPlanDataModelOut
from fastapi.testclient import TestClient
from pydantic import parse_obj_as


@pytest.mark.apitest
async def test_add_bouwplan_with_invalid_document_type(
    test_client: TestClient, admin_token: str, tmp_path
):
    files = [
        (
            "in_file",
            (
                "python_logo.jpeg",
                open("./tests/backend/app/api/data/python_logo.jpeg", "rb"),
                "image/jpeg",
            ),
        )
    ]
    headers = {"accept": "application/json", "Authorization": f"Bearer {admin_token}"}
    params = {"year": "2022"}
    response = await test_client.post(
        "/bouwplan/upload", params=params, headers=headers, files=files
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Ongeldig document type"}


@pytest.mark.apitest
async def test_add_bouwplan_with_invalid_excel_data(
    test_client: TestClient, admin_token: str, tmp_path
):
    files = [
        (
            "in_file",
            (
                "bouwplan_2022_niet_valide.xlsx",
                open(
                    "./tests/backend/app/api/data/bouwplan_2022_niet_valide.xlsx", "rb"
                ),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ),
        )
    ]
    headers = {"accept": "application/json", "Authorization": f"Bearer {admin_token}"}
    params = {"year": "2022"}
    response = await test_client.post(
        "/bouwplan/upload", params=params, headers=headers, files=files
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Fout bij inlezen van de excel"}


@pytest.mark.apitest
async def test_add_bouwplan_with_invalid_pydantic_Data(
    test_client: TestClient, admin_token: str, tmp_path
):
    files = [
        (
            "in_file",
            (
                "bouwplan_2022_niet_valide_mist_kolom.xlsx",
                open(
                    "./tests/backend/app/api/data/bouwplan_2022_niet_valide_mist_kolom.xlsx",
                    "rb",
                ),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ),
        )
    ]
    headers = {"accept": "application/json", "Authorization": f"Bearer {admin_token}"}
    params = {"year": "2022"}
    response = await test_client.post(
        "/bouwplan/upload", params=params, headers=headers, files=files
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Fout bij valideren van de data"}


@pytest.mark.apitest
async def test_add_bouwplan_with_valid_data(
    test_client: TestClient, admin_token: str, tmp_path
):
    files = [
        (
            "in_file",
            (
                "bouwplan_2022.xlsx",
                open(
                    "./tests/backend/app/api/data/bouwplan_2022.xlsx",
                    "rb",
                ),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ),
        )
    ]
    headers = {"accept": "application/json", "Authorization": f"Bearer {admin_token}"}
    params = {"year": "2022"}
    response = await test_client.post(
        "/bouwplan/upload", params=params, headers=headers, files=files
    )
    assert response.status_code == 200
    assert parse_obj_as(List[BouwPlanDataModelOut], response.json())

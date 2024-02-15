import pytest
from app.helpers.excel_functions import excel_to_list_of_dicts
from tests.backend.app.helpers.conftest import data_to_assert

@pytest.mark.unittest
def test_excel_to_list_of_dicts(valid_bouwplan_excel):
    result = excel_to_list_of_dicts(valid_bouwplan_excel)
    assert [i for i in result if i not in data_to_assert] == []
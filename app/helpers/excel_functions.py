import pandas as pd
from typing import List, BinaryIO
import pathlib

# TODO: Create test
def excel_to_list_of_dicts(
    excel_file: BinaryIO,
) -> List[dict]:
    """
    Reads an excel, converts it into a pandas dataframe and a list of dictionaries respectively.

    Parameters
    ----------
    excel_file : BinaryIO
        file like object representing the excel

    Returns
    -------
    List[dict]
        A list of dictionaries containing the bouwplan data for the given year.

    """
    excel_data = pd.read_excel(excel_file)
    df = pd.DataFrame(excel_data)
    df["ha"] = df["ha"].fillna(0)
    df["ha"] = df["ha"].astype(float)
    df["ha"] = df["ha"].round(decimals=2)
    df = df.fillna("")

    return df.to_dict(orient="records")


# return {"upload_date":pathlib.Path(excel_filename).stem,"data":df_dict}

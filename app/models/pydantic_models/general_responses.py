from pydantic import BaseModel
from typing import Optional, Any


class HTTPError(BaseModel):
    """
    HTTP error schema to be used when an `HTTPException` is thrown.
    """

    detail: str


class SuccessResponse(BaseModel):
    detail: str
    data: Optional[Any] = None

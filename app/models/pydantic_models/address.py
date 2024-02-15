from pydantic import BaseModel
from typing import Optional


class UpdateAddressRequest(BaseModel):
    street: Optional[str] = None
    number: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None


class AddressResponse(BaseModel):
    street: str = None
    number: str = None
    postal_code: str = None
    city: str = None
    country: str = None

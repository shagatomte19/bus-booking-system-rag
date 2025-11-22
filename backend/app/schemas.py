from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class DroppingPointBase(BaseModel):
    name: str
    price: int


class DroppingPointResponse(DroppingPointBase):
    id: int
    district_id: int
    
    class Config:
        from_attributes = True


class BusProviderBase(BaseModel):
    name: str


class BusProviderResponse(BusProviderBase):
    id: int
    
    class Config:
        from_attributes = True


class BusSearchRequest(BaseModel):
    from_district: str = Field(..., description="Origin district")
    to_district: str = Field(..., description="Destination district")
    max_price: Optional[int] = Field(None, description="Maximum price filter")


class BusSearchResult(BaseModel):
    provider_name: str
    drop_point: str
    price: int
    from_district: str
    to_district: str


class BookingCreate(BaseModel):
    user_name: str = Field(..., min_length=2, description="User's full name")
    phone: str = Field(..., pattern=r'^\+?[0-9]{10,15}$', description="Phone number")
    from_district: str
    to_district: str
    bus_provider: str
    travel_date: str = Field(..., description="Travel date in YYYY-MM-DD format")


class BookingResponse(BaseModel):
    id: int
    user_name: str
    phone: str
    from_district: str
    to_district: str
    bus_provider: str
    travel_date: str
    booking_date: datetime
    status: str
    
    class Config:
        from_attributes = True


class ProviderQuestionRequest(BaseModel):
    question: str = Field(..., min_length=3, description="Question about bus providers")


class ProviderQuestionResponse(BaseModel):
    answer: str
    sources: List[str]
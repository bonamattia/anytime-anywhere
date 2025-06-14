from pydantic import BaseModel, Field, constr
from typing import Optional


class FlightSearchConfig(BaseModel):
    origin: constr(min_length=2, max_length=4) = Field(..., description="IATA airport code")
    destination: constr(min_length=2, max_length=4) = Field(..., description="IATA airport code")
    departure_date: constr(pattern=r"^\d{4}-\d{2}-\d{2}$") = Field(..., description="YYYY-MM-DD")
    currency: Optional[str] = Field(default="EUR", description="Currency code")
    max_offers: Optional[int] = Field(default=24, description="Maximum number of offers to return")
    adults: Optional[int] = Field(default=2, description="Number of adult passengers")
    travel_class: Optional[str] = Field(default="ECONOMY", description="Travel class")


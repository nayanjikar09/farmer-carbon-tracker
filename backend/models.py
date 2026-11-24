from pydantic import BaseModel
from typing import Optional


class FarmerIn(BaseModel):
    name: str
    village: str
    acres: float
    crop: str
    gps_lat: Optional[float] = None
    gps_lng: Optional[float] = None


class CollectionIn(BaseModel):
    farmer_id: int
    waste_quantity_tonnes: float
    collection_date: str


class ReceiveIn(BaseModel):
    actual_weight_tonnes: float


class ProductionIn(BaseModel):
    collection_id: Optional[int] = None
    biomass_input_tonnes: float
    batch_date: str
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

class Carrier(BaseModel):
	mc_number: str
	fmcsa_verified:bool = False
	otp_verified: bool = False


class PublicLoad(BaseModel):
	load_id: str
	origin: str
	destination: str
	pickup_datetime: datetime
	delivery_datetime: datetime
	equipment_type:str
	loadboard_rate: Decimal
	weight: int
	commodity_type: str
	num_of_pieces: int
	miles: int
	dimensions: str
	notes: str | None = None

class InternalLoad(BaseModel):
	load: PublicLoad
	max_rate: Decimal
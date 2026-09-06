from datetime import datetime
from decimal import Decimal

from carrier_sales.domain.models import InternalLoad, PublicLoad


MOCK_LOADS = [
    InternalLoad(
        load=PublicLoad(
            load_id="LOAD-001",
            origin="Chicago, IL",
            destination="Dallas, TX",
            pickup_datetime=datetime(2026, 9, 7, 8, 0),
            delivery_datetime=datetime(2026, 9, 8, 16, 0),
            equipment_type="dry_van",
            loadboard_rate=Decimal("1800"),
            weight=42000,
            commodity_type="general_freight",
            num_of_pieces=24,
            miles=925,
            dimensions="48x40x60",
            notes="FCFS pickup",
        ),
        max_rate=Decimal("1950"),
    ),
    InternalLoad(
        load=PublicLoad(
            load_id="LOAD-002",
            origin="Chicago, IL",
            destination="Atlanta, GA",
            pickup_datetime=datetime(2026, 9, 7, 10, 0),
            delivery_datetime=datetime(2026, 9, 8, 18, 0),
            equipment_type="reefer",
            loadboard_rate=Decimal("2200"),
            weight=38000,
            commodity_type="food_products",
            num_of_pieces=20,
            miles=720,
            dimensions="48x40x55",
            notes="Maintain 34F",
        ),
        max_rate=Decimal("2350"),
    ),
    InternalLoad(
        load=PublicLoad(
            load_id="LOAD-003",
            origin="Houston, TX",
            destination="Phoenix, AZ",
            pickup_datetime=datetime(2026, 9, 8, 7, 30),
            delivery_datetime=datetime(2026, 9, 9, 15, 0),
            equipment_type="flatbed",
            loadboard_rate=Decimal("2500"),
            weight=45000,
            commodity_type="steel",
            num_of_pieces=12,
            miles=1175,
            dimensions="240x96x84",
            notes="Tarps required",
        ),
        max_rate=Decimal("2700"),
    ),
]


def search_loads(
    origin: str | None = None,
    destination: str | None = None,
    equipment_type: str | None = None,
) -> list[InternalLoad]:
    results = MOCK_LOADS

    if origin:
        results = [
            load for load in results
            if load.load.origin.lower() == origin.lower()
        ]

    if destination:
        results = [
            load for load in results
            if load.load.destination.lower() == destination.lower()
        ]

    if equipment_type:
        results = [
            load for load in results
            if load.load.equipment_type.lower() == equipment_type.lower()
        ]

    return results

def get_load(load_id: str) -> InternalLoad | None:
    return next(
        (
            load
            for load in MOCK_LOADS
            if load.load.load_id == load_id
        ),
        None,
    )


from pydantic import BaseModel


class BookingResult(BaseModel):
    success: bool
    load_id: str
    carrier_mc: str
    agreed_rate: float
    booking_id: str | None = None


def book_load(
    load_id: str,
    carrier_mc: str,
    agreed_rate: float,
) -> BookingResult:
    load = get_load(load_id)

    if load is None:
        return BookingResult(
            success=False,
            load_id=load_id,
            carrier_mc=carrier_mc,
            agreed_rate=agreed_rate,
        )

    if agreed_rate > float(load.max_rate):
        return BookingResult(
            success=False,
            load_id=load_id,
            carrier_mc=carrier_mc,
            agreed_rate=agreed_rate,
        )

    return BookingResult(
        success=True,
        load_id=load_id,
        carrier_mc=carrier_mc,
        agreed_rate=agreed_rate,
        booking_id=f"BOOK-{load_id}-{carrier_mc}",
    )
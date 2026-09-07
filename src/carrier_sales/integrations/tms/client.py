import os

from carrier_sales.integrations.tms.legacy_tms import (
    book_load as legacy_book_load,
    get_load as legacy_get_load,
    search_loads as legacy_search_loads,
)
from carrier_sales.integrations.tms.mock_tms import (
    book_load as mock_book_load,
    get_load as mock_get_load,
    search_loads as mock_search_loads,
)


TMS_MODE = os.getenv("TMS_MODE", "mock").strip().lower()


def search_loads(
    origin: str | None = None,
    destination: str | None = None,
    equipment_type: str | None = None,
):
    if TMS_MODE == "mock":
        return mock_search_loads(
            origin=origin,
            destination=destination,
            equipment_type=equipment_type,
        )

    if TMS_MODE == "legacy_tcp":
        return legacy_search_loads(
            origin=origin,
            destination=destination,
            equipment_type=equipment_type,
        )

    raise ValueError(
        f"Unsupported TMS_MODE: {TMS_MODE}"
    )


def get_load(load_id: str):
    if TMS_MODE == "mock":
        return mock_get_load(load_id)

    if TMS_MODE == "legacy_tcp":
        return legacy_get_load(load_id)

    raise ValueError(
        f"Unsupported TMS_MODE: {TMS_MODE}"
    )


def book_load(
    load_id: str,
    carrier_mc: str,
    agreed_rate: float,
):
    if TMS_MODE == "mock":
        return mock_book_load(
            load_id=load_id,
            carrier_mc=carrier_mc,
            agreed_rate=agreed_rate,
        )

    if TMS_MODE == "legacy_tcp":
        return legacy_book_load(
            load_id=load_id,
            carrier_mc=carrier_mc,
            agreed_rate=agreed_rate,
        )

    raise ValueError(
        f"Unsupported TMS_MODE: {TMS_MODE}"
    )
from dataclasses import dataclass

from carrier_sales.integrations.tms.tcp_client import (
    TMSMalformedResponseError,
)


@dataclass
class LegacyLoadRecord:
    load_id: str
    origin: str
    destination: str
    equipment_type: str
    loadboard_rate: float


LOAD_ID_START = 0
LOAD_ID_END = 12

ORIGIN_START = 12
ORIGIN_END = 37

DESTINATION_START = 37
DESTINATION_END = 62

EQUIPMENT_START = 62
EQUIPMENT_END = 77

RATE_START = 77
RATE_END = 87


def serialize_load_search_request(
    origin: str,
    destination: str,
    equipment_type: str,
) -> str:
    operation = "SEARCH"

    return (
        f"{operation:<10}"
        f"{origin:<25}"
        f"{destination:<25}"
        f"{equipment_type:<15}"
        "\n"
    )


def parse_load_record(
    response: str,
) -> LegacyLoadRecord:
    if len(response) < RATE_END:
        raise TMSMalformedResponseError(
            "Legacy TMS load response is too short"
        )

    load_id = response[
        LOAD_ID_START:LOAD_ID_END
    ].strip()

    origin = response[
        ORIGIN_START:ORIGIN_END
    ].strip()

    destination = response[
        DESTINATION_START:DESTINATION_END
    ].strip()

    equipment_type = response[
        EQUIPMENT_START:EQUIPMENT_END
    ].strip()

    raw_rate = response[
        RATE_START:RATE_END
    ].strip()

    if not load_id:
        raise TMSMalformedResponseError(
            "Legacy TMS response is missing load_id"
        )

    try:
        loadboard_rate = float(raw_rate)
    except ValueError as exc:
        raise TMSMalformedResponseError(
            "Legacy TMS response contains invalid rate"
        ) from exc

    return LegacyLoadRecord(
        load_id=load_id,
        origin=origin,
        destination=destination,
        equipment_type=equipment_type,
        loadboard_rate=loadboard_rate,
    )
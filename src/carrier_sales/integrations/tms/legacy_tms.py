import os
from datetime import datetime
from decimal import Decimal

from carrier_sales.domain.models import (
    InternalLoad,
    PublicLoad,
)
from carrier_sales.integrations.tms.mock_tms import (
    BookingResult,
)
from carrier_sales.integrations.tms.tcp_client import (
    LegacyTMSTCPClient,
    TCPClientConfig,
    TMSMalformedResponseError,
)


class LegacyTMSConfigurationError(Exception):
    pass


class LegacyTMSError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
    ):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def _get_client() -> LegacyTMSTCPClient:
    host = os.getenv("TMS_HOST")
    port = os.getenv("TMS_PORT")

    if not host or not port:
        raise LegacyTMSConfigurationError(
            "TMS_HOST and TMS_PORT are required "
            "when TMS_MODE=legacy_tcp"
        )

    return LegacyTMSTCPClient(
        TCPClientConfig(
            host=host,
            port=int(port),
            timeout_seconds=float(
                os.getenv(
                    "TMS_TIMEOUT_SECONDS",
                    "3",
                )
            ),
            max_retries=int(
                os.getenv(
                    "TMS_MAX_RETRIES",
                    "2",
                )
            ),
            backoff_seconds=float(
                os.getenv(
                    "TMS_BACKOFF_SECONDS",
                    "0.5",
                )
            ),
        )
    )


def _auth_token() -> str:
    token = os.getenv("TMS_AUTH_TOKEN")

    if not token:
        raise LegacyTMSConfigurationError(
            "TMS_AUTH_TOKEN is required "
            "when TMS_MODE=legacy_tcp"
        )

    return token


def _validate_value(value: str) -> str:
    value = str(value)

    if "|" in value or "\r" in value or "\n" in value:
        raise ValueError(
            "Legacy TMS values cannot contain | or CR/LF"
        )

    return value


def _build_request(
    command: str,
    **fields: str,
) -> str:
    parts = [
        f"CMD:{_validate_value(command)}",
        f"AUTH:{_validate_value(_auth_token())}",
    ]

    for key, value in fields.items():
        if value is None:
            continue

        parts.append(
            f"{key.upper()}:{_validate_value(value)}"
        )

    return "|".join(parts) + "\r\n"


def _parse_error(line: str) -> LegacyTMSError:
    parts = line.split("|")

    code = "UNKNOWN"
    message = "Legacy TMS returned an error"

    for part in parts[1:]:
        if ":" not in part:
            continue

        key, value = part.split(":", 1)

        if key == "CODE":
            code = value.strip()
        elif key == "MSG":
            message = value.strip()

    return LegacyTMSError(
        code=code,
        message=message,
    )


def _parse_record_line(
    line: str,
) -> dict[str, str]:
    if line.startswith("ERR|"):
        raise _parse_error(line)

    fields: dict[str, str] = {}

    for part in line.split("|"):
        if ":" not in part:
            raise TMSMalformedResponseError(
                "Malformed legacy TMS record"
            )

        key, value = part.split(":", 1)

        fields[key.strip()] = value.rstrip()

    return fields


def _parse_response(
    response: str,
) -> list[dict[str, str]]:
    lines = [
        line.strip("\r")
        for line in response.splitlines()
        if line.strip()
    ]

    if not lines:
        raise TMSMalformedResponseError(
            "Legacy TMS returned no response lines"
        )

    if lines[0].startswith("ERR|"):
        raise _parse_error(lines[0])

    if lines[-1] != "END":
        raise TMSMalformedResponseError(
            "Legacy TMS success response missing END terminator"
        )

    return [
        _parse_record_line(line)
        for line in lines[:-1]
    ]


def _require(
    fields: dict[str, str],
    key: str,
) -> str:
    value = fields.get(key)

    if value is None or not value.strip():
        raise TMSMalformedResponseError(
            f"Legacy TMS response missing {key}"
        )

    return value.strip()


def _to_decimal(
    value: str,
    field_name: str,
) -> Decimal:
    try:
        return Decimal(value.strip())
    except Exception as exc:
        raise TMSMalformedResponseError(
            f"Invalid {field_name}"
        ) from exc


def _to_int(
    value: str,
    field_name: str,
) -> int:
    try:
        return int(value.strip())
    except Exception as exc:
        raise TMSMalformedResponseError(
            f"Invalid {field_name}"
        ) from exc


def _record_to_load(
    fields: dict[str, str],
) -> InternalLoad:
    try:
        pickup = datetime.fromisoformat(
            _require(
                fields,
                "PICKUP_DATETIME",
            )
        )

        delivery = datetime.fromisoformat(
            _require(
                fields,
                "DELIVERY_DATETIME",
            )
        )
    except ValueError as exc:
        raise TMSMalformedResponseError(
            "Invalid load datetime"
        ) from exc

    public_load = PublicLoad(
        load_id=_require(
            fields,
            "LOAD_ID",
        ),
        origin=_require(
            fields,
            "ORIGIN",
        ),
        destination=_require(
            fields,
            "DESTINATION",
        ),
        pickup_datetime=pickup,
        delivery_datetime=delivery,
        equipment_type=_require(
            fields,
            "EQUIPMENT_TYPE",
        ),
        loadboard_rate=_to_decimal(
            _require(
                fields,
                "LOADBOARD_RATE",
            ),
            "LOADBOARD_RATE",
        ),
        weight=_to_int(
            _require(
                fields,
                "WEIGHT",
            ),
            "WEIGHT",
        ),
        commodity_type=_require(
            fields,
            "COMMODITY_TYPE",
        ),
        num_of_pieces=_to_int(
            _require(
                fields,
                "NUM_OF_PIECES",
            ),
            "NUM_OF_PIECES",
        ),
        miles=_to_int(
            _require(
                fields,
                "MILES",
            ),
            "MILES",
        ),
        dimensions=_require(
            fields,
            "DIMENSIONS",
        ),
        notes=fields.get("NOTES", "").strip() or None,
    )

    return InternalLoad(
        load=public_load,
        max_rate=_to_decimal(
            _require(
                fields,
                "MAX_RATE",
            ),
            "MAX_RATE",
        ),
    )


def search_loads(
    origin: str | None = None,
    destination: str | None = None,
    equipment_type: str | None = None,
) -> list[InternalLoad]:
    client = _get_client()

    fields: dict[str, str] = {}

    if origin:
        fields["ORIGIN"] = origin

    if destination:
        fields["DESTINATION"] = destination

    if equipment_type:
        fields["EQUIPMENT_TYPE"] = equipment_type

    request = _build_request(
        "LOAD_QUERY",
        **fields,
    )

    response = client.send(request)

    records = _parse_response(response)

    return [
        _record_to_load(record)
        for record in records
    ]


def get_load(
    load_id: str,
) -> InternalLoad | None:
    client = _get_client()

    request = _build_request(
        "LOAD_GET",
        LOAD_ID=load_id,
    )

    try:
        response = client.send(request)
        records = _parse_response(response)

    except LegacyTMSError as exc:
        if exc.code == "UNKNOWN_LOAD":
            return None

        raise

    if not records:
        return None

    if len(records) != 1:
        raise TMSMalformedResponseError(
            "LOAD_GET returned unexpected record count"
        )

    return _record_to_load(
        records[0]
    )


def book_load(
    load_id: str,
    carrier_mc: str,
    agreed_rate: float,
) -> BookingResult:
    client = _get_client()

    request = _build_request(
        "LOAD_BOOK",
        LOAD_ID=load_id,
        CARRIER_MC=carrier_mc,
        AGREED_RATE=f"{agreed_rate:.2f}",
    )

    try:
        response = client.send(
        request,
        retry_safe=False,
    )
        records = _parse_response(response)

    except LegacyTMSError as exc:
        if exc.code in {
            "UNKNOWN_LOAD",
            "ALREADY_BOOKED",
            "INVALID_RATE",
        }:
            return BookingResult(
                success=False,
                load_id=load_id,
                carrier_mc=carrier_mc,
                agreed_rate=agreed_rate,
                booking_id=None,
            )

        raise

    if len(records) != 1:
        raise TMSMalformedResponseError(
            "LOAD_BOOK returned unexpected record count"
        )

    booking_id = _require(
        records[0],
        "BOOKING_ID",
    )

    return BookingResult(
        success=True,
        load_id=load_id,
        carrier_mc=carrier_mc,
        agreed_rate=agreed_rate,
        booking_id=booking_id,
    )
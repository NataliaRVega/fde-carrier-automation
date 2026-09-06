from fastapi import FastAPI
from pydantic import BaseModel
from decimal import Decimal


from carrier_sales.integrations.fmcsa import verify_carrier
from carrier_sales.integrations.otp import send_otp, verify_otp
from carrier_sales.integrations.tms.mock_tms import search_loads
from carrier_sales.integrations.tms.mock_tms import get_load
from carrier_sales.policy.negotiation import evaluate_carrier_offer
from carrier_sales.integrations.tms.mock_tms import book_load
from carrier_sales.integrations.senior_rep import queue_for_senior_rep


app = FastAPI(
    title="Carrier Sales API",
    version="0.1.0",
)


class VerifyCarrierRequest(BaseModel):
    mc_number: str

class SendOTPRequest(BaseModel):
    destination: str

class VerifyOTPRequest(BaseModel):
    code: str

class SearchLoadsRequest(BaseModel):
    origin: str | None = None
    destination: str | None = None
    equipment_type: str | None = None

class SelectLoadRequest(BaseModel):
    load_id: str

class NegotiateRateRequest(BaseModel):
    load_id: str
    carrier_offer: Decimal
    current_broker_offer: Decimal
    round_number: int

class BookLoadRequest(BaseModel):
    load_id: str
    carrier_mc: str
    agreed_rate: float
    carrier_confirmed: bool

class HandoffRequest(BaseModel):
    carrier_mc: str
    load_id: str
    agreed_rate: float


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
    }


@app.post("/verify-carrier")
def verify_carrier_endpoint(
    request: VerifyCarrierRequest,
) -> dict:
    result = verify_carrier(request.mc_number)

    return {
        "eligible": result.active_authority,
        "status": (
            "ACTIVE"
            if result.active_authority
            else "INACTIVE"
        ),
    }


@app.post("/send-otp")
def send_otp_endpoint(
    request: SendOTPRequest,
) -> dict:
    send_otp(request.destination)

    return {
        "sent": True,
    }


@app.post("/verify-otp")
def verify_otp_endpoint(
    request: VerifyOTPRequest,
) -> dict:
    result = verify_otp(request.code)

    return {
        "verified": result.verified,
    }


@app.post("/search-loads")
def search_loads_endpoint(
    request: SearchLoadsRequest,
) -> dict:
    internal_loads = search_loads(
        origin=request.origin,
        destination=request.destination,
        equipment_type=request.equipment_type,
    )

    public_loads = [
        internal_load.load.model_dump(mode="json")
        for internal_load in internal_loads
    ]

    return {
        "count": len(public_loads),
        "loads": public_loads,
    }


@app.post("/select-load")
def select_load_endpoint(
    request: SelectLoadRequest,
) -> dict:
    internal_load = get_load(request.load_id)

    if internal_load is None:
        return {
            "found": False,
            "load": None,
        }

    return {
        "found": True,
        "load": internal_load.load.model_dump(mode="json"),
    }


@app.post("/negotiate-rate")
def negotiate_rate_endpoint(
    request: NegotiateRateRequest,
) -> dict:
    internal_load = get_load(request.load_id)

    if internal_load is None:
        return {
            "decision": "LOAD_NOT_FOUND",
            "offer_to_carrier": None,
            "round_number": request.round_number,
        }

    decision = evaluate_carrier_offer(
        carrier_offer=request.carrier_offer,
        max_rate=internal_load.max_rate,
        current_broker_offer=request.current_broker_offer,
        round_number=request.round_number,
    )

    return decision.model_dump(mode="json")


@app.post("/book-load")
def book_load_endpoint(
    request: BookLoadRequest,
) -> dict:
    if not request.carrier_confirmed:
        return {
            "success": False,
            "reason": "EXPLICIT_CONFIRMATION_REQUIRED",
            "load_id": request.load_id,
            "booking_id": None,
        }

    result = book_load(
        load_id=request.load_id,
        carrier_mc=request.carrier_mc,
        agreed_rate=request.agreed_rate,
    )

    return result.model_dump(mode="json")

@app.post("/handoff")
def handoff_endpoint(
    request: HandoffRequest,
) -> dict:
    result = queue_for_senior_rep(
        carrier_mc=request.carrier_mc,
        load_id=request.load_id,
        agreed_rate=request.agreed_rate,
    )

    return result.model_dump(mode="json")
import os

from fastapi import Depends, Header
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from decimal import Decimal
from carrier_sales.domain.states import CallState
from carrier_sales.workflow.session_store import get_session
from carrier_sales.workflow.session_store import (
    get_or_create_session,
    get_session,
)

from carrier_sales.integrations.fmcsa import verify_carrier
from carrier_sales.integrations.otp import send_otp, verify_otp
from carrier_sales.integrations.tms.client import (
    search_loads,
    get_load,
    book_load,
)
from carrier_sales.policy.negotiation import evaluate_carrier_offer
from carrier_sales.integrations.senior_rep import queue_for_senior_rep


app = FastAPI(
    title="Carrier Sales API",
    version="0.1.0",
)

API_TOKEN = os.getenv("CARRIER_SALES_API_TOKEN", "dev-secret-token")


def require_api_token(
    authorization: str | None = Header(default=None),
) -> None:
    expected = f"Bearer {API_TOKEN}"

    if authorization != expected:
        raise HTTPException(
            status_code=401,
            detail="UNAUTHORIZED",
        )

class VerifyCarrierRequest(BaseModel):
    mc_number: str
    call_id: str

class SendOTPRequest(BaseModel):
    destination: str
    call_id: str

class VerifyOTPRequest(BaseModel):
    code: str
    call_id: str

class SearchLoadsRequest(BaseModel):
    call_id: str
    origin: str | None = None
    destination: str | None = None
    equipment_type: str | None = None

class SelectLoadRequest(BaseModel):
    load_id: str
    call_id: str

class NegotiateRateRequest(BaseModel):
    call_id: str
    carrier_offer: Decimal

class BookLoadRequest(BaseModel):
    call_id: str
    carrier_confirmed: bool

class HandoffRequest(BaseModel):
    call_id: str


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
    }


@app.post("/verify-carrier")
def verify_carrier_endpoint(
    request: VerifyCarrierRequest,
    _: None = Depends(require_api_token),
) -> dict:
    session = get_or_create_session(request.call_id)

    if session.state != CallState.START:
        raise HTTPException(
            status_code=409,
            detail=f"INVALID_STATE:{session.state.value}",
        )

    session.carrier_mc = request.mc_number

    session.log_event(
        event_type="FMCSA_CHECK_STARTED",
    )

    session.move_to(CallState.FMCSA_PENDING)

    result = verify_carrier(request.mc_number)

    if result.active_authority:
        session.fmcsa_verified = True

        session.log_event(
            event_type="FMCSA_VERIFIED",
            outcome="SUCCESS",
        )

        session.move_to(CallState.OTP_PENDING)

        return {
            "eligible": True,
            "status": "ACTIVE",
            "state": session.state.value,
        }

    session.fmcsa_verified = False

    session.log_event(
        event_type="FMCSA_REJECTED",
        outcome="FAILED",
    )

    session.move_to(CallState.FAILED)

    return {
        "eligible": False,
        "status": "INACTIVE",
        "state": session.state.value,
    }


@app.post("/send-otp")
def send_otp_endpoint(
    request: SendOTPRequest,
    _: None = Depends(require_api_token),
) -> dict:
    session = get_session(request.call_id)

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="SESSION_NOT_FOUND",
        )

    if session.state != CallState.OTP_PENDING:
        raise HTTPException(
            status_code=409,
            detail=f"INVALID_STATE:{session.state.value}",
        )

    if not session.fmcsa_verified:
        raise HTTPException(
            status_code=403,
            detail="FMCSA_VERIFICATION_REQUIRED",
        )

    send_otp(request.destination)

    session.log_event(
        event_type="OTP_SENT",
        outcome="SUCCESS",
    )

    return {
        "sent": True,
        "state": session.state.value,
    }


@app.post("/verify-otp")
def verify_otp_endpoint(
    request: VerifyOTPRequest,
    _: None = Depends(require_api_token),
) -> dict:
    session = get_session(request.call_id)

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="SESSION_NOT_FOUND",
        )

    if session.state != CallState.OTP_PENDING:
        raise HTTPException(
            status_code=409,
            detail=f"INVALID_STATE:{session.state.value}",
        )

    if not session.fmcsa_verified:
        raise HTTPException(
            status_code=403,
            detail="FMCSA_VERIFICATION_REQUIRED",
        )

    result = verify_otp(request.code)

    if result.verified:
        session.otp_verified = True

        session.log_event(
            event_type="OTP_VERIFIED",
            outcome="SUCCESS",
        )

        session.move_to(CallState.VERIFIED)

        return {
            "verified": True,
            "state": session.state.value,
        }

    session.otp_verified = False

    session.log_event(
        event_type="OTP_FAILED",
        outcome="FAILED",
    )

    return {
        "verified": False,
        "state": session.state.value,
    }


@app.post("/search-loads")
def search_loads_endpoint(
    request: SearchLoadsRequest,
    _: None = Depends(require_api_token),
) -> dict:
    session = get_session(request.call_id)

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="SESSION_NOT_FOUND",
        )

    if session.state not in {
        CallState.VERIFIED,
        CallState.LOAD_SEARCH,
    }:
        raise HTTPException(
            status_code=409,
            detail=f"INVALID_STATE:{session.state.value}",
        )

    if not session.fmcsa_verified or not session.otp_verified:
        raise HTTPException(
            status_code=403,
            detail="VERIFICATION_REQUIRED",
        )

    if session.state == CallState.VERIFIED:
        session.move_to(CallState.LOAD_SEARCH)

    internal_loads = search_loads(
        origin=request.origin,
        destination=request.destination,
        equipment_type=request.equipment_type,
    )

    public_loads = [
        internal_load.load.model_dump(mode="json")
        for internal_load in internal_loads
    ]

    session.log_event(
        event_type="LOAD_SEARCH_COMPLETED",
        outcome="SUCCESS",
        metadata={
            "count": len(public_loads),
            "origin": request.origin,
            "destination": request.destination,
            "equipment_type": request.equipment_type,
        },
    )

    return {
        "count": len(public_loads),
        "loads": public_loads,
        "state": session.state.value,
    }

@app.post("/select-load")
def select_load_endpoint(
    request: SelectLoadRequest,
    _: None = Depends(require_api_token),
) -> dict:
    session = get_session(request.call_id)

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="SESSION_NOT_FOUND",
        )

    if session.state != CallState.LOAD_SEARCH:
        raise HTTPException(
            status_code=409,
            detail=f"INVALID_STATE:{session.state.value}",
        )

    internal_load = get_load(request.load_id)

    if internal_load is None:
        return {
            "found": False,
            "load": None,
            "state": session.state.value,
        }

    session.selected_load_id = request.load_id

    session.log_event(
        event_type="LOAD_SELECTED",
        outcome="SUCCESS",
    )

    session.move_to(CallState.LOAD_PRESENTED)

    return {
        "found": True,
        "load": internal_load.load.model_dump(mode="json"),
        "state": session.state.value,
    }

@app.post("/negotiate-rate")
def negotiate_rate_endpoint(
    request: NegotiateRateRequest,
    _: None = Depends(require_api_token),
) -> dict:
    session = get_session(request.call_id)

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="SESSION_NOT_FOUND",
        )

    if session.state == CallState.LOAD_PRESENTED:
        if session.selected_load_id is None:
            raise HTTPException(
                status_code=409,
                detail="NO_SELECTED_LOAD",
            )

        internal_load = get_load(session.selected_load_id)

        if internal_load is None:
            raise HTTPException(
                status_code=404,
                detail="LOAD_NOT_FOUND",
            )

        session.current_broker_offer = float(
            internal_load.load.loadboard_rate
        )
        session.negotiation_round = 0
        session.move_to(CallState.NEGOTIATING)

    elif session.state != CallState.NEGOTIATING:
        raise HTTPException(
            status_code=409,
            detail=f"INVALID_STATE:{session.state.value}",
        )

    internal_load = get_load(session.selected_load_id)

    if internal_load is None:
        raise HTTPException(
            status_code=404,
            detail="LOAD_NOT_FOUND",
        )

    decision = evaluate_carrier_offer(
        carrier_offer=request.carrier_offer,
        current_broker_offer=Decimal(
            str(session.current_broker_offer)
        ),
        max_rate=internal_load.max_rate,
        round_number=session.negotiation_round,
    )

    session.negotiation_round = decision.round_number

    if decision.decision == "ACCEPT":
        session.agreed_rate = float(request.carrier_offer)

        session.log_event(
            event_type="NEGOTIATION_ACCEPTED",
            outcome="SUCCESS",
            metadata={
                "round_number": session.negotiation_round,
                "carrier_offer": float(request.carrier_offer),
            },
        )

        session.move_to(CallState.BOOKING)

    elif decision.decision == "COUNTER":
        session.current_broker_offer = float(
            decision.offer_to_carrier
        )

        session.log_event(
            event_type="NEGOTIATION_COUNTER",
            outcome="SUCCESS",
            metadata={
                "round_number": session.negotiation_round,
                "offer_to_carrier": float(
                    decision.offer_to_carrier
                ),
            },
        )

    elif decision.decision == "FAILED_MAX_ROUNDS":
        session.log_event(
            event_type="NEGOTIATION_FAILED",
            outcome="FAILED",
            metadata={
                "round_number": session.negotiation_round,
            },
        )

        session.move_to(CallState.FAILED)

    return decision.model_dump(mode="json")


@app.post("/book-load")
def book_load_endpoint(
    request: BookLoadRequest,
    _: None = Depends(require_api_token),
) -> dict:
    session = get_session(request.call_id)

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="SESSION_NOT_FOUND",
        )
    if session.booking_completed:
        return {
            "success": True,
            "booking_id": session.booking_id,
            "load_id": session.selected_load_id,
            "agreed_rate": session.agreed_rate,
            "reason": "IDEMPOTENT_REPLAY",
            "state": session.state.value,
    }

    if session.state != CallState.BOOKING:
        raise HTTPException(
            status_code=409,
            detail=f"INVALID_STATE:{session.state.value}",
        )

    if not request.carrier_confirmed:
        return {
            "success": False,
            "reason": "EXPLICIT_CONFIRMATION_REQUIRED",
            "booking_id": None,
            "load_id": session.selected_load_id,
            "agreed_rate": session.agreed_rate,
        }

    if (
        session.selected_load_id is None
        or session.carrier_mc is None
        or session.agreed_rate is None
    ):
        raise HTTPException(
            status_code=409,
            detail="INCOMPLETE_SESSION_STATE",
        )

    result = book_load(
        load_id=session.selected_load_id,
        carrier_mc=session.carrier_mc,
        agreed_rate=session.agreed_rate,
    )

    if not result.success:
        session.log_event(
            event_type="BOOKING_FAILED",
            outcome="FAILED",
        )

        session.move_to(CallState.FAILED)

        return {
            **result.model_dump(mode="json"),
            "reason": "BOOKING_FAILED",
        }

    session.booking_id = result.booking_id
    session.booking_completed = True

    session.log_event(
        event_type="BOOKING_CONFIRMED",
        outcome="SUCCESS",
        metadata={
            "booking_id": result.booking_id,
        },
    )

    

    session.move_to(CallState.HANDOFF)

    return {
        **result.model_dump(mode="json"),
        "reason": None,
        "state": session.state.value,
    }

@app.post("/handoff")
def handoff_endpoint(
    request: HandoffRequest,
    _: None = Depends(require_api_token),
) -> dict:
    session = get_session(request.call_id)

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="SESSION_NOT_FOUND",
        )

    if session.state != CallState.HANDOFF:
        raise HTTPException(
            status_code=409,
            detail=f"INVALID_STATE:{session.state.value}",
        )

    if (
        session.carrier_mc is None
        or session.selected_load_id is None
        or session.agreed_rate is None
    ):
        raise HTTPException(
            status_code=409,
            detail="INCOMPLETE_SESSION_STATE",
        )

    result = queue_for_senior_rep(
        carrier_mc=session.carrier_mc,
        load_id=session.selected_load_id,
        agreed_rate=session.agreed_rate,
    )

    session.log_event(
        event_type="HANDOFF_QUEUED",
        outcome="SUCCESS",
    )

    session.log_event(
        event_type="CALL_COMPLETED",
        outcome="SUCCESS",
    )

    session.move_to(CallState.COMPLETE)

    return {
        **result.model_dump(mode="json"),
        "state": session.state.value,
    }
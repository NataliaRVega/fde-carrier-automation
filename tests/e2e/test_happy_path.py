from decimal import Decimal

from carrier_sales.domain.session import CallSession
from carrier_sales.domain.states import CallState
from carrier_sales.workflow.booking import complete_booking
from carrier_sales.workflow.carrier_verification import run_fmcsa_verification
from carrier_sales.workflow.handoff import complete_handoff
from carrier_sales.workflow.load_search import begin_load_search
from carrier_sales.workflow.load_selection import select_load
from carrier_sales.workflow.negotiation import (
    begin_negotiation,
    handle_carrier_offer,
)
from carrier_sales.workflow.otp_verification import run_otp_verification


def test_complete_happy_path():
    session = CallSession(call_id="call-e2e-001")

    run_fmcsa_verification(session, "123456")

    assert session.fmcsa_verified is True
    assert session.state == CallState.OTP_PENDING

    run_otp_verification(session, "123456")

    assert session.otp_verified is True
    assert session.state == CallState.VERIFIED

    begin_load_search(session)

    assert session.state == CallState.LOAD_SEARCH

    select_load(session, "LOAD-001")

    assert session.selected_load_id == "LOAD-001"
    assert session.state == CallState.LOAD_PRESENTED

    begin_negotiation(session)

    assert session.state == CallState.NEGOTIATING

    negotiation_result = handle_carrier_offer(
        session,
        Decimal("1900"),
    )

    assert negotiation_result["decision"] == "ACCEPT"
    assert session.agreed_rate == 1900.0
    assert session.state == CallState.BOOKING

    booking_result = complete_booking(session)

    assert booking_result["success"] is True
    assert booking_result["load_id"] == "LOAD-001"
    assert session.state == CallState.HANDOFF

    handoff_result = complete_handoff(session)

    assert handoff_result["queued"] is True
    assert handoff_result["queue"] == "senior-rep"
    assert session.state == CallState.COMPLETE
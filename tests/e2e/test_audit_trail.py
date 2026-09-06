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


def test_happy_path_produces_complete_audit_trail():
    session = CallSession(call_id="call-audit-001")

    run_fmcsa_verification(session, "123456")
    run_otp_verification(session, "123456")
    begin_load_search(session)
    select_load(session, "LOAD-001")
    begin_negotiation(session)
    handle_carrier_offer(session, Decimal("1900"))
    complete_booking(session)
    complete_handoff(session)

    event_types = [
        event.event_type
        for event in session.audit_events
    ]

    assert "FMCSA_CHECK_STARTED" in event_types
    assert "FMCSA_VERIFIED" in event_types
    assert "OTP_VERIFIED" in event_types
    assert "LOAD_SELECTED" in event_types
    assert "NEGOTIATION_ACCEPTED" in event_types
    assert "BOOKING_CONFIRMED" in event_types
    assert "HANDOFF_QUEUED" in event_types
    assert "CALL_COMPLETED" in event_types

    assert session.state == CallState.COMPLETE

    final_event = session.audit_events[-1]

    assert final_event.event_type == "CALL_COMPLETED"
    assert final_event.carrier_mc == "123456"
    assert final_event.load_id == "LOAD-001"
    assert final_event.agreed_rate == 1900.0
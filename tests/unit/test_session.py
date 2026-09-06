import pytest

from carrier_sales.domain.errors import InvalidStateTransitionError
from carrier_sales.domain.session import CallSession
from carrier_sales.domain.states import CallState


def test_new_session_starts_at_start():
    session = CallSession(call_id="call-001")

    assert session.state == CallState.START
    assert session.fmcsa_verified is False
    assert session.otp_verified is False


def test_session_can_move_to_valid_state():
    session = CallSession(call_id="call-001")

    session.move_to(CallState.FMCSA_PENDING)

    assert session.state == CallState.FMCSA_PENDING


def test_session_rejects_invalid_state_transition():
    session = CallSession(call_id="call-001")

    with pytest.raises(InvalidStateTransitionError):
        session.move_to(CallState.BOOKING)
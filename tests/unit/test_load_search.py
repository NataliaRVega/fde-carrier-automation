import pytest

from carrier_sales.domain.errors import AuthorizationError
from carrier_sales.domain.session import CallSession
from carrier_sales.domain.states import CallState
from carrier_sales.workflow.carrier_verification import run_fmcsa_verification
from carrier_sales.workflow.load_search import begin_load_search
from carrier_sales.workflow.otp_verification import run_otp_verification


def test_verified_carrier_can_begin_load_search():
    session = CallSession(call_id="call-001")

    run_fmcsa_verification(session, "123456")
    run_otp_verification(session, "123456")

    result = begin_load_search(session)

    assert result.state == CallState.LOAD_SEARCH


def test_unverified_carrier_cannot_begin_load_search():
    session = CallSession(call_id="call-002")

    with pytest.raises(AuthorizationError):
        begin_load_search(session)
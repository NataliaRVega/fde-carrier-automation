from carrier_sales.domain.session import CallSession
from carrier_sales.domain.states import CallState
from carrier_sales.workflow.carrier_verification import run_fmcsa_verification
from carrier_sales.workflow.otp_verification import run_otp_verification


def test_valid_otp_moves_to_verified():
    session = CallSession(call_id="call-001")

    run_fmcsa_verification(session, "123456")
    result = run_otp_verification(session, "123456")

    assert result.fmcsa_verified is True
    assert result.otp_verified is True
    assert result.state == CallState.VERIFIED


def test_invalid_otp_moves_to_failed():
    session = CallSession(call_id="call-002")

    run_fmcsa_verification(session, "123456")
    result = run_otp_verification(session, "000000")

    assert result.fmcsa_verified is True
    assert result.otp_verified is False
    assert result.state == CallState.FAILED

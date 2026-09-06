from carrier_sales.domain.session import CallSession
from carrier_sales.domain.states import CallState
from carrier_sales.workflow.carrier_verification import run_fmcsa_verification


def test_valid_fmcsa_moves_to_otp_pending():
    session = CallSession(call_id="call-001")

    result = run_fmcsa_verification(
        session,
        "123456",
    )

    assert result.carrier_mc == "123456"
    assert result.fmcsa_verified is True
    assert result.state == CallState.OTP_PENDING


def test_invalid_fmcsa_moves_to_failed():
    session = CallSession(call_id="call-002")

    result = run_fmcsa_verification(
        session,
        "999999",
    )

    assert result.carrier_mc == "999999"
    assert result.fmcsa_verified is False
    assert result.state == CallState.FAILED
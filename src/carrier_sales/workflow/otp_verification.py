from carrier_sales.domain.session import CallSession
from carrier_sales.domain.states import CallState
from carrier_sales.integrations.otp import verify_otp


def run_otp_verification(
    session: CallSession,
    code: str,
) -> CallSession:
    result = verify_otp(code)

    if result.verified:
        session.otp_verified = True
        session.log_event(
            "OTP_VERIFIED",
            outcome="SUCCESS",
        )
        session.move_to(CallState.VERIFIED)
    else:
        session.otp_verified = False
        session.log_event(
            "OTP_FAILED",
            outcome="FAILED",
        )
        session.move_to(CallState.FAILED)

    return session

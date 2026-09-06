from carrier_sales.domain.session import CallSession
from carrier_sales.domain.states import CallState
from carrier_sales.integrations.fmcsa import verify_carrier


def run_fmcsa_verification(
    session: CallSession,
    mc_number: str,
) -> CallSession:
    session.carrier_mc = mc_number
    session.log_event("FMCSA_CHECK_STARTED")

    session.move_to(CallState.FMCSA_PENDING)

    result = verify_carrier(mc_number)

    if result.active_authority:
        session.fmcsa_verified = True
        session.log_event(
            "FMCSA_VERIFIED",
            outcome="SUCCESS",
        )
        session.move_to(CallState.OTP_PENDING)
    else:
        session.fmcsa_verified = False
        session.log_event(
            "FMCSA_REJECTED",
            outcome="FAILED",
        )
        session.move_to(CallState.FAILED)

    return session
from carrier_sales.domain.session import CallSession


def can_search_loads(session: CallSession) -> bool:
    return (
        session.fmcsa_verified is True
        and session.otp_verified is True
    )
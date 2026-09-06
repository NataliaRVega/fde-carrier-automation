from carrier_sales.domain.session import CallSession
from carrier_sales.domain.states import CallState


def can_book_load(session: CallSession) -> bool:
    return (
        session.state == CallState.BOOKING
        and session.selected_load_id is not None
        and session.agreed_rate is not None
        and session.fmcsa_verified is True
        and session.otp_verified is True
    )
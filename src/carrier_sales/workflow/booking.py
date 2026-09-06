from carrier_sales.domain.errors import AuthorizationError
from carrier_sales.domain.session import CallSession
from carrier_sales.domain.states import CallState
from carrier_sales.integrations.tms.mock_tms import book_load
from carrier_sales.policy.booking import can_book_load


def complete_booking(session: CallSession) -> dict:
    if not can_book_load(session):
        raise AuthorizationError(
            "Booking requirements are not satisfied."
        )

    result = book_load(
        load_id=session.selected_load_id,
        carrier_mc=session.carrier_mc,
        agreed_rate=session.agreed_rate,
    )

    if not result.success:
        session.move_to(CallState.FAILED)
        return result.model_dump()

    session.move_to(CallState.HANDOFF)

    return result.model_dump()
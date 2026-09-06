from carrier_sales.domain.errors import AuthorizationError
from carrier_sales.domain.session import CallSession
from carrier_sales.domain.states import CallState
from carrier_sales.integrations.tms.mock_tms import MOCK_LOADS


def select_load(
    session: CallSession,
    load_id: str,
) -> CallSession:
    if session.state != CallState.LOAD_SEARCH:
        raise AuthorizationError(
            f"Load selection is not allowed from state {session.state.value}"
        )

    matching_load = next(
        (
            internal_load
            for internal_load in MOCK_LOADS
            if internal_load.load.load_id == load_id
        ),
        None,
    )

    if matching_load is None:
        raise ValueError(
            f"Load not found: {load_id}"
        )

    session.selected_load_id = load_id
    session.move_to(CallState.LOAD_PRESENTED)

    return session

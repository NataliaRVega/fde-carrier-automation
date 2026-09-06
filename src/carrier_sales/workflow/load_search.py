from carrier_sales.domain.errors import AuthorizationError
from carrier_sales.domain.session import CallSession
from carrier_sales.domain.states import CallState
from carrier_sales.policy.eligibility import can_search_loads


def begin_load_search(session: CallSession) -> CallSession:
    if not can_search_loads(session):
        raise AuthorizationError(
            "Load search requires FMCSA and OTP verification."
        )

    session.move_to(CallState.LOAD_SEARCH)

    return session
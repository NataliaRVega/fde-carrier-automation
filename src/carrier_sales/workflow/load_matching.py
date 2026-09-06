from carrier_sales.domain.models import PublicLoad
from carrier_sales.domain.session import CallSession
from carrier_sales.domain.states import CallState
from carrier_sales.integrations.tms.mock_tms import search_loads


def find_matching_loads(
    session: CallSession,
    *,
    origin: str | None = None,
    destination: str | None = None,
    equipment_type: str | None = None,
) -> list[PublicLoad]:
    if session.state != CallState.LOAD_SEARCH:
        raise ValueError(
            f"Load search is not allowed from state {session.state.value}"
        )

    internal_loads = search_loads(
        origin=origin,
        destination=destination,
        equipment_type=equipment_type,
    )

    return [internal_load.load for internal_load in internal_loads]
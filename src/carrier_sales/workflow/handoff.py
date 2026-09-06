from carrier_sales.domain.errors import AuthorizationError
from carrier_sales.domain.session import CallSession
from carrier_sales.domain.states import CallState
from carrier_sales.integrations.senior_rep import queue_for_senior_rep


def complete_handoff(session: CallSession) -> dict:
    if session.state != CallState.HANDOFF:
        raise AuthorizationError(
            f"Handoff is not allowed from state {session.state.value}"
        )

    if session.carrier_mc is None:
        raise AuthorizationError(
            "Handoff requires a carrier MC number."
        )

    if session.selected_load_id is None:
        raise AuthorizationError(
            "Handoff requires a selected load."
        )

    if session.agreed_rate is None:
        raise AuthorizationError(
            "Handoff requires an agreed rate."
        )

    result = queue_for_senior_rep(
        carrier_mc=session.carrier_mc,
        load_id=session.selected_load_id,
        agreed_rate=session.agreed_rate,
    )

    session.log_event(
    	"HANDOFF_QUEUED",
    	outcome="SUCCESS",
    	metadata={
        	"queue": result.queue,
    		},
	)

    session.log_event(
    	"CALL_COMPLETED",
    	outcome="SUCCESS",
	)

    session.move_to(CallState.COMPLETE)

    return result.model_dump()
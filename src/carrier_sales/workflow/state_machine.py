from carrier_sales.domain.states import CallState
from carrier_sales.domain.errors import InvalidStateTransitionError


ALLOWED_TRANSITIONS = {
    CallState.START: {
        CallState.FMCSA_PENDING,
    },

    CallState.FMCSA_PENDING: {
        CallState.OTP_PENDING,
        CallState.FAILED,
    },

    CallState.OTP_PENDING: {
        CallState.VERIFIED,
        CallState.FAILED,
    },

    CallState.VERIFIED: {
        CallState.LOAD_SEARCH,
    },

    CallState.LOAD_SEARCH: {
        CallState.LOAD_PRESENTED,
        CallState.FAILED,
    },

    CallState.LOAD_PRESENTED: {
        CallState.NEGOTIATING,
        CallState.FAILED,
    },

    CallState.NEGOTIATING: {
        CallState.BOOKING,
        CallState.FAILED,
    },

    CallState.BOOKING: {
        CallState.HANDOFF,
        CallState.FAILED,
    },

    CallState.HANDOFF: {
        CallState.COMPLETE,
        CallState.FAILED,
    },

    CallState.COMPLETE: set(),
    CallState.FAILED: set(),
}


def can_transition(
    current_state: CallState,
    next_state: CallState,
) -> bool:
    return next_state in ALLOWED_TRANSITIONS[current_state]

def transition(
	current_state: CallState,
	next_state: CallState,
) -> CallState:
	if not can_transition(current_state, next_state):
		raise InvalidStateTransitionError(
			f"Invalid state transition: "
			f"{current_state.value} -> {next_state.value}"
		)
	return next_state
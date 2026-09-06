from decimal import Decimal

from carrier_sales.domain.errors import AuthorizationError
from carrier_sales.domain.session import CallSession
from carrier_sales.domain.states import CallState
from carrier_sales.integrations.tms.mock_tms import get_load
from carrier_sales.policy.negotiation import evaluate_carrier_offer


def begin_negotiation(session: CallSession) -> CallSession:
    if session.state != CallState.LOAD_PRESENTED:
        raise AuthorizationError(
            f"Negotiation is not allowed from state {session.state.value}"
        )

    if session.selected_load_id is None:
        raise AuthorizationError(
            "Negotiation requires a selected load."
        )

    internal_load = get_load(session.selected_load_id)

    if internal_load is None:
        raise ValueError(
            f"Load not found: {session.selected_load_id}"
        )

    session.current_broker_offer = float(
        internal_load.load.loadboard_rate
    )
    session.negotiation_round = 0
    session.move_to(CallState.NEGOTIATING)

    return session


def handle_carrier_offer(
    session: CallSession,
    carrier_offer: Decimal,
) -> dict:
    if session.state != CallState.NEGOTIATING:
        raise AuthorizationError(
            f"Rate negotiation is not allowed from state {session.state.value}"
        )

    if session.selected_load_id is None:
        raise AuthorizationError(
            "No load selected."
        )

    internal_load = get_load(session.selected_load_id)

    if internal_load is None:
        raise ValueError(
            f"Load not found: {session.selected_load_id}"
        )

    if session.current_broker_offer is None:
        raise ValueError(
            "Current broker offer is not initialized."
        )

    decision = evaluate_carrier_offer(
        carrier_offer=carrier_offer,
        max_rate=internal_load.max_rate,
        current_broker_offer=Decimal(
            str(session.current_broker_offer)
        ),
        round_number=session.negotiation_round,
    )

    session.negotiation_round = decision.round_number

    if decision.decision == "ACCEPT":
        session.agreed_rate = float(carrier_offer)

        session.log_event(
            "NEGOTIATION_ACCEPTED",
            outcome="SUCCESS",
            metadata={
                "round": decision.round_number,
                "carrier_offer": float(carrier_offer),
            },
        )

        session.move_to(CallState.BOOKING)

    elif decision.decision == "COUNTER":
        session.current_broker_offer = float(
            decision.offer_to_carrier
        )

        session.log_event(
            "NEGOTIATION_COUNTER",
            outcome="CONTINUE",
            metadata={
                "round": decision.round_number,
                "offer_to_carrier": float(
                    decision.offer_to_carrier
                ),
            },
        )

    elif decision.decision == "FAILED_MAX_ROUNDS":
        session.log_event(
            "NEGOTIATION_FAILED",
            outcome="FAILED",
            metadata={
                "round": decision.round_number,
            },
        )

        session.move_to(CallState.FAILED)

    return decision.model_dump()
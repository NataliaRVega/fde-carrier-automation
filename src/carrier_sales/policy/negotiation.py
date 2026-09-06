from decimal import Decimal

from pydantic import BaseModel


MAX_COUNTER_ROUNDS = 3


class NegotiationDecision(BaseModel):
    decision: str
    offer_to_carrier: Decimal | None = None
    round_number: int


def evaluate_carrier_offer(
    *,
    carrier_offer: Decimal,
    max_rate: Decimal,
    current_broker_offer: Decimal,
    round_number: int,
) -> NegotiationDecision:
    """
    Deterministic negotiation policy.

    Important:
    - max_rate is internal only
    - max_rate is never returned
    - broker offers never exceed max_rate
    - maximum 3 counter rounds
    """

    if round_number >= MAX_COUNTER_ROUNDS:
        return NegotiationDecision(
            decision="FAILED_MAX_ROUNDS",
            offer_to_carrier=None,
            round_number=round_number,
        )

    next_round = round_number + 1

    if carrier_offer <= max_rate:
        return NegotiationDecision(
            decision="ACCEPT",
            offer_to_carrier=carrier_offer,
            round_number=next_round,
        )

    proposed_counter = min(
        current_broker_offer + Decimal("50"),
        max_rate,
    )

    if proposed_counter > max_rate:
        raise RuntimeError(
            "Negotiation policy exceeded max_rate"
        )

    return NegotiationDecision(
        decision="COUNTER",
        offer_to_carrier=proposed_counter,
        round_number=next_round,
    )
from decimal import Decimal

from carrier_sales.policy.negotiation import evaluate_carrier_offer


def test_counter_never_exceeds_max_rate():
    result = evaluate_carrier_offer(
        carrier_offer=Decimal("2200"),
        max_rate=Decimal("1950"),
        current_broker_offer=Decimal("1930"),
        round_number=1,
    )

    assert result.decision == "COUNTER"
    assert result.offer_to_carrier <= Decimal("1950")


def test_accepts_offer_at_or_below_max_rate():
    result = evaluate_carrier_offer(
        carrier_offer=Decimal("1900"),
        max_rate=Decimal("1950"),
        current_broker_offer=Decimal("1800"),
        round_number=0,
    )

    assert result.decision == "ACCEPT"
    assert result.offer_to_carrier == Decimal("1900")


def test_fails_after_three_rounds():
    result = evaluate_carrier_offer(
        carrier_offer=Decimal("2200"),
        max_rate=Decimal("1950"),
        current_broker_offer=Decimal("1950"),
        round_number=3,
    )

    assert result.decision == "FAILED_MAX_ROUNDS"
    assert result.offer_to_carrier is None


def test_many_counters_never_exceed_ceiling():
    max_rate = Decimal("1950")

    for carrier_offer in range(2000, 3000, 25):
        for current_offer in range(1700, 2000, 25):
            result = evaluate_carrier_offer(
                carrier_offer=Decimal(carrier_offer),
                max_rate=max_rate,
                current_broker_offer=Decimal(current_offer),
                round_number=1,
            )

            if result.offer_to_carrier is not None:
                assert result.offer_to_carrier <= max_rate
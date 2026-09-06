import pytest
from carrier_sales.domain.errors import InvalidStateTransitionError

from carrier_sales.domain.states import CallState
from carrier_sales.workflow.state_machine import transition


def test_valid_transition():
    result = transition(
        CallState.START,
        CallState.FMCSA_PENDING,
    )

    assert result == CallState.FMCSA_PENDING


def test_invalid_transition():
    with pytest.raises(InvalidStateTransitionError):
        transition(
            CallState.START,
            CallState.BOOKING,
        )
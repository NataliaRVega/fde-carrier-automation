from pydantic import BaseModel

from carrier_sales.domain.states import CallState
from carrier_sales.workflow.state_machine import transition

class CallSession(BaseModel):
	call_id: str
	carrier_mc: str | None = None
	state: CallState = CallState.START
	fmcsa_verified: bool = False
	otp_verified: bool = False
	selected_load_id: str | None = None
	agreed_rate: float | None = None
	negotiation_round: int = 0
	current_broker_offer: float | None = None

	def move_to(self, next_state: CallState) -> None:
		self.state = transition(self.state, next_state)
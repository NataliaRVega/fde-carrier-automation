from pydantic import BaseModel, Field

from carrier_sales.audit.events import AuditEvent
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
	audit_events: list[AuditEvent] = Field(default_factory=list)

	def move_to(self, next_state: CallState) -> None:
		self.state = transition(self.state, next_state)

	def log_event(
   		self,
    		event_type: str,
    		*,
    		outcome: str | None = None,
    		notes: str | None = None,
    		metadata: dict | None = None,
	) -> None:
    		self.audit_events.append(
        	AuditEvent(
            		event_type=event_type,
            		call_id=self.call_id,
            		carrier_mc=self.carrier_mc,
            		load_id=self.selected_load_id,
            		agreed_rate=self.agreed_rate,
            		outcome=outcome,
            		notes=notes,
            		metadata=metadata or {},
        	)
    	)
from pydantic import BaseModel


class HandoffResult(BaseModel):
    queued: bool
    queue: str
    carrier_mc: str
    load_id: str
    agreed_rate: float


def queue_for_senior_rep(
    carrier_mc: str,
    load_id: str,
    agreed_rate: float,
) -> HandoffResult:
    return HandoffResult(
        queued=True,
        queue="senior-rep",
        carrier_mc=carrier_mc,
        load_id=load_id,
        agreed_rate=agreed_rate,
    )

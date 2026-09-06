from fastapi import FastAPI
from pydantic import BaseModel

from carrier_sales.integrations.fmcsa import verify_carrier


app = FastAPI(
    title="Carrier Sales API",
    version="0.1.0",
)


class VerifyCarrierRequest(BaseModel):
    mc_number: str


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
    }


@app.post("/verify-carrier")
def verify_carrier_endpoint(
    request: VerifyCarrierRequest,
) -> dict:
    result = verify_carrier(request.mc_number)

    return {
        "eligible": result.active_authority,
        "status": (
            "ACTIVE"
            if result.active_authority
            else "INACTIVE"
        ),
    }
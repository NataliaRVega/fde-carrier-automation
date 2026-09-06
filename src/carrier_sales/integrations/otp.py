from pydantic import BaseModel


MOCK_OTP_CODE = "123456"


class OTPResult(BaseModel):
    verified: bool


def send_otp(destination: str) -> str:
    """
    Mock OTP sender.

    In production, HappyRobot SMS/email tooling would send the code.
    """
    return MOCK_OTP_CODE


def verify_otp(code: str) -> OTPResult:
    """
    Mock OTP verification.
    """
    return OTPResult(
        verified=(code == MOCK_OTP_CODE)
    )
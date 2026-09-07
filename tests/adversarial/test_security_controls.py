from fastapi.testclient import TestClient

from carrier_sales.api.app import app


client = TestClient(app)

HEADERS = {
    "Authorization": "Bearer happyrobot-fde-secret",
}


def test_booking_before_otp_is_blocked(
    monkeypatch,
):
    monkeypatch.setenv(
        "CARRIER_SALES_API_TOKEN",
        "happyrobot-fde-secret",
    )

    call_id = "SECURITY-BEFORE-OTP"

    response = client.post(
        "/verify-carrier",
        headers=HEADERS,
        json={
            "call_id": call_id,
            "mc_number": "123456",
        },
    )

    assert response.status_code == 200
    assert response.json()["state"] == "OTP_PENDING"

    booking = client.post(
        "/book-load",
        headers=HEADERS,
        json={
            "call_id": call_id,
            "carrier_confirmed": True,
        },
    )

    assert booking.status_code == 409
    assert (
        booking.json()["detail"]
        == "INVALID_STATE:OTP_PENDING"
    )


def test_booking_before_negotiation_is_blocked(
    monkeypatch,
):
    monkeypatch.setenv(
        "CARRIER_SALES_API_TOKEN",
        "happyrobot-fde-secret",
    )

    call_id = "SECURITY-BEFORE-NEGOTIATION"

    assert client.post(
        "/verify-carrier",
        headers=HEADERS,
        json={
            "call_id": call_id,
            "mc_number": "123456",
        },
    ).status_code == 200

    assert client.post(
        "/send-otp",
        headers=HEADERS,
        json={
            "call_id": call_id,
            "destination": "test@example.com",
        },
    ).status_code == 200

    assert client.post(
        "/verify-otp",
        headers=HEADERS,
        json={
            "call_id": call_id,
            "code": "123456",
        },
    ).status_code == 200

    assert client.post(
        "/search-loads",
        headers=HEADERS,
        json={
            "call_id": call_id,
            "origin": "Chicago",
            "destination": "Dallas",
            "equipment_type": "dry van",
        },
    ).status_code == 200

    assert client.post(
        "/select-load",
        headers=HEADERS,
        json={
            "call_id": call_id,
            "load_id": "LOAD-001",
        },
    ).status_code == 200

    booking = client.post(
        "/book-load",
        headers=HEADERS,
        json={
            "call_id": call_id,
            "carrier_confirmed": True,
        },
    )

    assert booking.status_code == 409
    assert (
        booking.json()["detail"]
        == "INVALID_STATE:LOAD_PRESENTED"
    )


def test_max_rate_is_never_exposed_in_public_load_response(
    monkeypatch,
):
    monkeypatch.setenv(
        "CARRIER_SALES_API_TOKEN",
        "happyrobot-fde-secret",
    )

    call_id = "SECURITY-MAX-RATE"

    client.post(
        "/verify-carrier",
        headers=HEADERS,
        json={
            "call_id": call_id,
            "mc_number": "123456",
        },
    )

    client.post(
        "/send-otp",
        headers=HEADERS,
        json={
            "call_id": call_id,
            "destination": "test@example.com",
        },
    )

    client.post(
        "/verify-otp",
        headers=HEADERS,
        json={
            "call_id": call_id,
            "code": "123456",
        },
    )

    response = client.post(
        "/search-loads",
        headers=HEADERS,
        json={
            "call_id": call_id,
            "origin": "Chicago",
            "destination": "Dallas",
            "equipment_type": "dry van",
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["count"] >= 1

    for load in payload["loads"]:
        assert "max_rate" not in load

    assert "1950" not in response.text


def test_fourth_counter_attempt_is_blocked(
    monkeypatch,
):
    monkeypatch.setenv(
        "CARRIER_SALES_API_TOKEN",
        "happyrobot-fde-secret",
    )

    call_id = "SECURITY-COUNTER-LIMIT"

    client.post(
        "/verify-carrier",
        headers=HEADERS,
        json={
            "call_id": call_id,
            "mc_number": "123456",
        },
    )

    client.post(
        "/send-otp",
        headers=HEADERS,
        json={
            "call_id": call_id,
            "destination": "test@example.com",
        },
    )

    client.post(
        "/verify-otp",
        headers=HEADERS,
        json={
            "call_id": call_id,
            "code": "123456",
        },
    )

    client.post(
        "/search-loads",
        headers=HEADERS,
        json={
            "call_id": call_id,
            "origin": "Chicago",
            "destination": "Dallas",
            "equipment_type": "dry van",
        },
    )

    client.post(
        "/select-load",
        headers=HEADERS,
        json={
            "call_id": call_id,
            "load_id": "LOAD-001",
        },
    )

    first = client.post(
        "/negotiate-rate",
        headers=HEADERS,
        json={
            "call_id": call_id,
            "carrier_offer": 2200,
        },
    )

    second = client.post(
        "/negotiate-rate",
        headers=HEADERS,
        json={
            "call_id": call_id,
            "carrier_offer": 2200,
        },
    )

    third = client.post(
        "/negotiate-rate",
        headers=HEADERS,
        json={
            "call_id": call_id,
            "carrier_offer": 2200,
        },
    )

    fourth = client.post(
        "/negotiate-rate",
        headers=HEADERS,
        json={
            "call_id": call_id,
            "carrier_offer": 2200,
        },
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert third.status_code == 200
    assert fourth.status_code == 200

    assert first.json()["decision"] == "COUNTER"
    assert second.json()["decision"] == "COUNTER"
    assert third.json()["decision"] == "COUNTER"
    assert (
        fourth.json()["decision"]
        == "FAILED_MAX_ROUNDS"
    )
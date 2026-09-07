from fastapi.testclient import TestClient

from carrier_sales.api.app import app


client = TestClient(app)

HEADERS = {
    "Authorization": "Bearer happyrobot-fde-secret",
}


def test_duplicate_booking_returns_idempotent_replay(
    monkeypatch,
):
    monkeypatch.setenv(
        "CARRIER_SALES_API_TOKEN",
        "happyrobot-fde-secret",
    )

    call_id = "TEST-IDEMPOTENCY-PYTEST"

    response = client.post(
        "/verify-carrier",
        headers=HEADERS,
        json={
            "call_id": call_id,
            "mc_number": "123456",
        },
    )
    assert response.status_code == 200

    response = client.post(
        "/send-otp",
        headers=HEADERS,
        json={
            "call_id": call_id,
            "destination": "test@example.com",
        },
    )
    assert response.status_code == 200

    response = client.post(
        "/verify-otp",
        headers=HEADERS,
        json={
            "call_id": call_id,
            "code": "123456",
        },
    )
    assert response.status_code == 200

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

    response = client.post(
        "/select-load",
        headers=HEADERS,
        json={
            "call_id": call_id,
            "load_id": "LOAD-001",
        },
    )
    assert response.status_code == 200

    response = client.post(
        "/negotiate-rate",
        headers=HEADERS,
        json={
            "call_id": call_id,
            "carrier_offer": 1700,
        },
    )
    assert response.status_code == 200
    assert response.json()["decision"] == "ACCEPT"

    first_booking = client.post(
        "/book-load",
        headers=HEADERS,
        json={
            "call_id": call_id,
            "carrier_confirmed": True,
        },
    )

    assert first_booking.status_code == 200
    first_payload = first_booking.json()

    assert first_payload["success"] is True
    assert first_payload["booking_id"] is not None

    second_booking = client.post(
        "/book-load",
        headers=HEADERS,
        json={
            "call_id": call_id,
            "carrier_confirmed": True,
        },
    )

    assert second_booking.status_code == 200
    second_payload = second_booking.json()

    assert second_payload["success"] is True
    assert (
        second_payload["booking_id"]
        == first_payload["booking_id"]
    )
    assert (
        second_payload["reason"]
        == "IDEMPOTENT_REPLAY"
    )
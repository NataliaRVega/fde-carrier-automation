import socket

import pytest

from carrier_sales.integrations.tms.legacy_tms import (
    LegacyTMSError,
    _parse_response,
)
from carrier_sales.integrations.tms.tcp_client import (
    LegacyTMSTCPClient,
    TCPClientConfig,
    TMSConnectionError,
    TMSMalformedResponseError,
)


def test_tcp_timeout_retries_then_fails(
    monkeypatch,
):
    attempts = 0

    def fake_create_connection(
        address,
        timeout=None,
    ):
        nonlocal attempts
        attempts += 1
        raise socket.timeout("simulated timeout")

    monkeypatch.setattr(
        socket,
        "create_connection",
        fake_create_connection,
    )

    client = LegacyTMSTCPClient(
        TCPClientConfig(
            host="fake-tms",
            port=9999,
            timeout_seconds=0.1,
            max_retries=2,
            backoff_seconds=0,
        )
    )

    with pytest.raises(TMSConnectionError):
        client.send(
            "CMD:LOAD_QUERY|AUTH:test\r\n"
        )

    assert attempts == 3


def test_malformed_response_without_end_fails():
    malformed_response = (
        "LOAD_ID:LOAD-001|"
        "ORIGIN:Chicago, IL\r\n"
    )

    with pytest.raises(
        TMSMalformedResponseError
    ):
        _parse_response(
            malformed_response
        )


def test_auth_failed_response_is_normalized():
    response = (
        "ERR|CODE:AUTH_FAILED|"
        "MSG:Invalid authentication token\r\n"
    )

    with pytest.raises(
        LegacyTMSError
    ) as exc_info:
        _parse_response(
            response
        )

    assert exc_info.value.code == "AUTH_FAILED"
    assert (
        exc_info.value.message
        == "Invalid authentication token"
    )
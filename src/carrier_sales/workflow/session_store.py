from carrier_sales.domain.session import CallSession


_sessions: dict[str, CallSession] = {}


def get_or_create_session(call_id: str) -> CallSession:
    session = _sessions.get(call_id)

    if session is None:
        session = CallSession(call_id=call_id)
        _sessions[call_id] = session

    return session


def get_session(call_id: str) -> CallSession | None:
    return _sessions.get(call_id)


def delete_session(call_id: str) -> None:
    _sessions.pop(call_id, None)
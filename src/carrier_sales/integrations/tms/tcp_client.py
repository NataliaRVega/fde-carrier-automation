import socket
import time
from dataclasses import dataclass


class TMSConnectionError(Exception):
    pass


class TMSMalformedResponseError(Exception):
    pass


@dataclass
class TCPClientConfig:
    host: str
    port: int
    timeout_seconds: float = 3.0
    max_retries: int = 2
    backoff_seconds: float = 0.5


class LegacyTMSTCPClient:
    def __init__(self, config: TCPClientConfig):
        self.config = config

    def send(
        self,
        payload: str,
        retry_safe: bool = True,
    ) -> str:
        last_error: Exception | None = None

        max_retries = (
            self.config.max_retries
            if retry_safe
            else 0
        )

        for attempt in range(max_retries + 1):
            try:
                return self._send_once(payload)

            except (
                socket.timeout,
                ConnectionError,
                OSError,
                TMSConnectionError,
            ) as exc:
                last_error = exc

                if attempt >= max_retries:
                    break

                sleep_seconds = (
                    self.config.backoff_seconds
                    * (2 ** attempt)
                )

                time.sleep(sleep_seconds)

        raise TMSConnectionError(
            "Legacy TMS request failed after retries"
            if retry_safe
            else "Legacy TMS request failed without retry"
        ) from last_error


    def _send_once(self, payload: str) -> str:
        try:
            encoded_payload = payload.encode("ascii")
        except UnicodeEncodeError as exc:
            raise TMSMalformedResponseError(
                "Legacy TMS request contains non-ASCII data"
            ) from exc

        with socket.create_connection(
            (
                self.config.host,
                self.config.port,
            ),
            timeout=self.config.timeout_seconds,
        ) as sock:
            sock.settimeout(
                self.config.timeout_seconds
            )

            sock.sendall(encoded_payload)

            chunks: list[bytes] = []
            total_bytes = 0

            while True:
                try:
                    chunk = sock.recv(4096)
                except socket.timeout as exc:
                    raise TMSConnectionError(
                        "Legacy TMS timed out while reading response"
                    ) from exc

                if not chunk:
                    break

                chunks.append(chunk)
                total_bytes += len(chunk)

                if total_bytes > 4096:
                    raise TMSMalformedResponseError(
                        "Legacy TMS response exceeded maximum frame size"
                    )

        if not chunks:
            raise TMSMalformedResponseError(
                "Legacy TMS returned an empty response"
            )

        raw_response = b"".join(chunks)

        try:
            response = raw_response.decode("ascii")
        except UnicodeDecodeError as exc:
            raise TMSMalformedResponseError(
                "Legacy TMS returned non-ASCII data"
            ) from exc

        response = response.strip()

        if not response:
            raise TMSMalformedResponseError(
                "Legacy TMS returned a blank response"
            )

        return response
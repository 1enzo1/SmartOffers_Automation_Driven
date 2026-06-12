import time
import urllib.request


class RealHttpClient:
    """Manual-only HTTP client for a future QA4 call.

    This class is intentionally isolated from package exports and tests.
    It performs no retry and records no raw request or response body.
    """

    is_real_manual_client = True

    def send(self, sanitized_request, runtime_secrets, timeout_seconds):
        if not timeout_seconds:
            raise ValueError("timeout_seconds is required")

        endpoint = runtime_secrets["endpoint"]
        body = runtime_secrets["body"]
        headers = dict(runtime_secrets["headers"])
        auth_value = runtime_secrets["auth"]
        if auth_value:
            headers["Authorization"] = auth_value

        started = time.monotonic()
        request = urllib.request.Request(
            endpoint,
            data=body,
            headers=headers,
            method=sanitized_request["method"],
        )
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            status_code = getattr(response, "status", response.getcode())
            response.read(0)
        elapsed_ms = int((time.monotonic() - started) * 1000)

        return {
            "status_code": status_code,
            "ok": 200 <= int(status_code) < 300,
            "elapsed_ms": elapsed_ms,
            "body_recorded": False,
        }

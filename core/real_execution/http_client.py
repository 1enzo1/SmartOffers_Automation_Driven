class FakeHttpClient:
    """Test double for the first QA4 call path. It never performs network I/O."""

    is_fake_client = True

    def __init__(self):
        self.sent_requests = []

    def send(self, sanitized_request):
        stored_request = _copy_dict(sanitized_request)
        self.sent_requests.append(stored_request)
        return {
            "client": "fake",
            "status_code": 202,
            "simulated": True,
            "request": stored_request,
        }


def is_fake_client(client):
    return bool(getattr(client, "is_fake_client", False))


def _copy_dict(value):
    if isinstance(value, dict):
        return {key: _copy_dict(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_copy_dict(item) for item in value]
    return value

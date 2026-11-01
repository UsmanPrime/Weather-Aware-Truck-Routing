import io
from unittest.mock import patch
from urllib.error import HTTPError, URLError

import pytest
from rest_framework.test import APIClient

from routing.api.errors import exception_handler
from routing.providers.errors import ProviderError
from routing.providers.http import MAX_RESPONSE_BYTES, HttpTransport, NoRedirect


def test_health_has_no_database_or_provider_dependency():
    with patch(
        "urllib.request.OpenerDirector.open", side_effect=AssertionError("Unexpected network")
    ):
        response = APIClient().get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_wrong_method_is_structured():
    response = APIClient().post("/api/v1/health", {}, format="json")
    assert response.status_code == 405
    assert response.json()["error"]["request_id"]


@pytest.mark.parametrize(
    "error,code,status,retryable",
    [
        (
            HTTPError("https://synthetic.invalid?apiKey=do-not-leak", 401, "secret", {}, None),
            "access_denied",
            503,
            False,
        ),
        (
            HTTPError("https://synthetic.invalid", 429, "secret", {"Retry-After": "10"}, None),
            "rate_limited",
            503,
            True,
        ),
        (
            HTTPError("https://synthetic.invalid", 503, "secret", {}, None),
            "upstream_http_error",
            503,
            True,
        ),
        (TimeoutError("secret"), "timeout", 504, True),
        (URLError("secret"), "unavailable", 503, True),
    ],
)
def test_transport_errors_are_sanitized(error, code, status, retryable):
    transport = HttpTransport()
    with patch.object(transport.opener, "open", side_effect=error):
        with pytest.raises(ProviderError) as caught:
            transport.get_json("here", "https://synthetic.invalid", {})
    exc = caught.value
    assert exc.code == code
    assert exc.http_status == status
    assert exc.retryable == retryable
    assert "secret" not in str(exc)
    assert "do-not-leak" not in str(exc)
    response = exception_handler(exc, {})
    assert response.status_code == status
    assert response.data["error"]["request_id"]


@pytest.mark.parametrize("body", [b"not json", b"x" * (MAX_RESPONSE_BYTES + 1)])
def test_invalid_and_oversized_json_is_structured(body):
    transport = HttpTransport()
    with patch.object(transport.opener, "open", return_value=io.BytesIO(body)):
        with pytest.raises(ProviderError, match="invalid_payload"):
            transport.get_json("here", "https://synthetic.invalid", {})


def test_redirects_do_not_forward_credentials():
    assert NoRedirect().redirect_request(None, None, 302, "", {}, "https://other.invalid") is None


def test_post_transport_uses_headers_and_sanitizes_provider_limit():
    transport = HttpTransport()
    error = HTTPError(
        "https://synthetic.invalid",
        400,
        "Bad Request",
        {},
        io.BytesIO(b'{"error":{"code":2004,"message":"not forwarded"}}'),
    )
    with patch.object(transport.opener, "open", side_effect=error) as opener:
        with pytest.raises(ProviderError, match="route_limit"):
            transport.post_json(
                "ors",
                "https://synthetic.invalid",
                {"coordinates": []},
                {"Authorization": "synthetic-test-key"},
            )
    request = opener.call_args.args[0]
    assert request.get_method() == "POST"
    assert "synthetic-test-key" not in request.full_url
    assert request.get_header("Authorization") == "synthetic-test-key"

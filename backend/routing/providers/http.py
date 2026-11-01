"""Small bounded JSON transport. Authenticated URLs and upstream bodies are never logged."""

import json
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .errors import ProviderError, invalid_payload

MAX_RESPONSE_BYTES = 5 * 1024 * 1024


class JsonTransport(Protocol):
    def get_json(
        self,
        provider: str,
        endpoint: str,
        params: dict[str, str],
        headers: dict[str, str] | None = None,
    ) -> object: ...

    def post_json(
        self, provider: str, endpoint: str, body: dict, headers: dict[str, str]
    ) -> object: ...


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class HttpTransport:
    def __init__(self, timeout_s: float = 8):
        self.timeout_s = timeout_s
        self.opener = build_opener(NoRedirect())
        self.last_response_bytes: int | None = None

    def get_json(self, provider, endpoint, params, headers=None) -> object:
        # Endpoints are adapter constants, never supplied by an API client.
        request = Request(
            endpoint + "?" + urlencode(params),
            headers={
                "Accept": "application/json",
                "User-Agent": "WeatherAwareRouting/0.1",
                **(headers or {}),
            },
        )
        return self._read(provider, request)

    def post_json(self, provider, endpoint, body, headers) -> object:
        request = Request(
            endpoint,
            data=json.dumps(body, allow_nan=False).encode(),
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "WeatherAwareRouting/0.1",
                **headers,
            },
        )
        return self._read(provider, request)

    def _read(self, provider: str, request: Request) -> object:
        try:
            with self.opener.open(request, timeout=self.timeout_s) as response:
                content = response.read(MAX_RESPONSE_BYTES + 1)
                self.last_response_bytes = len(content)
                if len(content) > MAX_RESPONSE_BYTES:
                    raise invalid_payload(provider)
                return json.loads(content)
        except HTTPError as exc:
            retry_after = exc.headers.get("Retry-After", "") if exc.headers else ""
            status = exc.code
            if provider == "ors" and status in (400, 404):
                try:
                    code = json.loads(exc.read(65536)).get("error", {}).get("code")
                except (ValueError, AttributeError):
                    code = None
                if code == 2004:
                    exc.close()
                    raise ProviderError(
                        provider, "route_limit", "Public routing distance limit exceeded.", 422
                    ) from None
                if code in (2009, 2010):
                    exc.close()
                    raise ProviderError(
                        provider, "no_routes", "No routable truck road near these locations.", 422
                    ) from None
            exc.close()
            if status == 429:
                raise ProviderError(
                    provider,
                    "rate_limited",
                    "Provider rate limit reached.",
                    503,
                    True,
                    min(int(retry_after), 3600) if retry_after.isdigit() else None,
                ) from None
            if status in (401, 403):
                raise ProviderError(
                    provider,
                    "access_denied",
                    "Provider access denied or daily quota exhausted.",
                    503,
                ) from None
            raise ProviderError(
                provider,
                "upstream_http_error",
                "Provider request failed.",
                503 if status >= 500 else 502,
                status >= 500,
                upstream_status=status,
            ) from None
        except TimeoutError:
            raise ProviderError(
                provider, "timeout", "Provider request timed out.", 504, True
            ) from None
        except (URLError, OSError):
            raise ProviderError(
                provider, "unavailable", "Provider could not be reached.", 503, True
            ) from None
        except (ValueError, UnicodeError):
            raise invalid_payload(provider) from None

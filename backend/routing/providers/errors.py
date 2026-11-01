from dataclasses import dataclass


@dataclass
class ProviderError(Exception):
    """Only controlled messages; never retain a credential-bearing URL or upstream body."""

    provider: str
    code: str
    message: str
    http_status: int = 502
    retryable: bool = False
    retry_after_s: int | None = None

    def __str__(self):
        return f"{self.provider}: {self.code}: {self.message}"

    def as_dict(self, request_id: str) -> dict:
        result = {
            "code": self.code,
            "message": self.message,
            "provider": self.provider,
            "retryable": self.retryable,
            "request_id": request_id,
        }
        if self.retry_after_s is not None:
            result["retry_after_s"] = self.retry_after_s
        return result


def invalid_payload(provider: str) -> ProviderError:
    return ProviderError(provider, "invalid_payload", "Provider returned an invalid response.")

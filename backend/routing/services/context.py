"""Uncompressed signed corridor context. All bounds apply before parsing large data."""

import json
from datetime import datetime

from django.core.signing import BadSignature, SignatureExpired, TimestampSigner, b64_decode

from routing.domain.types import Coordinate
from routing.domain.units import nonnegative
from routing.providers.errors import ProviderError

MAX_TOKEN = 128 * 1024
MAX_JSON = 96 * 1024
MAX_POINTS = 6000
SALT = "trip-corridor-v1"


def create_context(routes: list[dict], departure: str, load_lb: float) -> str:
    payload = {
        "version": 1,
        "routes": [
            [[round(p[0], 5), round(p[1], 5)] for p in r["geometry"]["coordinates"]] for r in routes
        ],
        "departure_at": departure,
        "load_lb": load_lb,
    }
    if (
        sum(len(line) for line in payload["routes"]) > MAX_POINTS
        or len(json.dumps(payload).encode()) > MAX_JSON
    ):
        raise ProviderError(
            "corridor",
            "context_limit",
            "This trip is too detailed for the bounded corridor layer.",
            422,
        )
    token = TimestampSigner(salt=SALT).sign_object(payload, compress=False)
    if len(token) > MAX_TOKEN:
        raise ProviderError(
            "corridor", "context_limit", "Corridor context size limit reached.", 422
        )
    return token


def read_context(token: str) -> dict:
    if not isinstance(token, str) or len(token) > MAX_TOKEN:
        raise ProviderError("corridor", "invalid_context", "Invalid corridor context.", 400)
    try:
        encoded = TimestampSigner(salt=SALT).unsign(token, max_age=1800)
        if encoded.startswith("."):
            raise ValueError("Compressed context is not accepted")
        decoded = b64_decode(encoded.encode("ascii"))
        if len(decoded) > MAX_JSON:
            raise ValueError("Decoded context too large")
        payload = json.loads(decoded)
        if payload["version"] != 1 or not 1 <= len(payload["routes"]) <= 3:
            raise ValueError("Invalid version/route count")
        count = 0
        for line in payload["routes"]:
            if not isinstance(line, list) or len(line) < 2:
                raise ValueError("Invalid geometry")
            count += len(line)
            for point in line:
                if not isinstance(point, list) or len(point) != 2:
                    raise ValueError("Invalid position")
                Coordinate(latitude=point[1], longitude=point[0])
        if (
            count > MAX_POINTS
            or nonnegative(payload["load_lb"]) is None
            or payload["load_lb"] > 200000
        ):
            raise ValueError("Invalid geometry/load bounds")
        if (
            datetime.fromisoformat(payload["departure_at"].replace("Z", "+00:00")).utcoffset()
            is None
        ):
            raise ValueError("Naive departure")
        return payload
    except SignatureExpired:
        raise ProviderError(
            "corridor", "expired_context", "This plan expired. Generate routes again.", 410
        ) from None
    except (
        BadSignature,
        ValueError,
        TypeError,
        KeyError,
        IndexError,
        OverflowError,
        UnicodeError,
        AttributeError,
    ):
        raise ProviderError(
            "corridor", "invalid_context", "Invalid corridor context.", 400
        ) from None

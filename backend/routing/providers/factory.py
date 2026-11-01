import os

from .here import HereRouting
from .ors import DEFAULT_BASE, OrsRouting


def routing_provider():
    provider = os.environ.get("ROUTING_PROVIDER", "ors")
    if provider == "ors":
        return OrsRouting(
            os.environ.get("ORS_API_KEY", ""), os.environ.get("ORS_BASE_URL", DEFAULT_BASE)
        )
    if provider == "here":
        return HereRouting(os.environ.get("HERE_API_KEY", ""))
    raise ValueError("Unsupported routing provider")

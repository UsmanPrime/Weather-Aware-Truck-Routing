from rest_framework.throttling import SimpleRateThrottle


class GeocodeThrottle(SimpleRateThrottle):
    scope = "geocode"

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}


class PlanThrottle(GeocodeThrottle):
    scope = "plans"


class CorridorThrottle(GeocodeThrottle):
    scope = "corridor"

import os

from rest_framework import serializers
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response

from routing.providers.ors import DEFAULT_GEOCODING, PeliasGeocoding
from routing.services.cache import cached_call
from routing.services.corridor import corridor_forecast
from routing.services.planning import plan_trip

from .serializers import CorridorSerializer, PlanSerializer
from .throttles import CorridorThrottle, GeocodeThrottle, PlanThrottle


@api_view(["GET"])
def health(request):
    """Process health only: deliberately no credentials, database or network dependency."""
    return Response({"status": "ok"})


@api_view(["GET"])
@throttle_classes([GeocodeThrottle])
def geocode(request):
    query = request.query_params.get("q", "").strip()
    if not 3 <= len(query) <= 200:
        raise serializers.ValidationError({"q": "Enter 3–200 characters."})
    adapter = PeliasGeocoding(
        os.environ.get("ORS_API_KEY", ""),
        os.environ.get("ORS_GEOCODING_BASE_URL", DEFAULT_GEOCODING),
    )
    places = cached_call("places", query.casefold(), 86400, lambda: adapter.search(query), "pelias")
    return Response({"places": places, "source": "HeiGIT Pelias"})


@api_view(["POST"])
@throttle_classes([PlanThrottle])
def plans(request):
    serializer = PlanSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    return Response(plan_trip(serializer.validated_data))


@api_view(["POST"])
@throttle_classes([CorridorThrottle])
def corridor(request):
    serializer = CorridorSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    return Response(corridor_forecast(serializer.validated_data["context"]))

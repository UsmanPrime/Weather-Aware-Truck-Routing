from datetime import UTC, datetime, timedelta
from math import isfinite
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from rest_framework import serializers


class AwareDateTime(serializers.DateTimeField):
    def to_internal_value(self, value):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if parsed.utcoffset() is None:
                raise ValueError()
        except (ValueError, AttributeError, TypeError):
            raise serializers.ValidationError(
                "An ISO timestamp with timezone offset is required."
            ) from None
        return super().to_internal_value(value)


class PlaceSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=200)
    label = serializers.CharField(max_length=300)
    position = serializers.ListField(child=serializers.FloatField(), min_length=2, max_length=2)

    def validate_position(self, value):
        lon, lat = value
        if not isfinite(lon) or not isfinite(lat) or not -180 <= lon <= 180 or not -90 <= lat <= 90:
            raise serializers.ValidationError("Use valid longitude, latitude coordinates.")
        return value


class PlanSerializer(serializers.Serializer):
    origin = PlaceSerializer()
    destination = PlaceSerializer()
    departure_at = AwareDateTime()
    departure_timezone = serializers.CharField(max_length=80)
    load_lb = serializers.FloatField(min_value=0, max_value=200000)
    checkpoint_interval_mi = serializers.ChoiceField(choices=[10, 25, 50])

    def validate_load_lb(self, value):
        if not isfinite(value):
            raise serializers.ValidationError("Enter a finite weight in pounds.")
        return value

    def validate_departure_timezone(self, value):
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError):
            raise serializers.ValidationError("Choose a valid IANA timezone.") from None
        return value

    def validate_departure_at(self, value):
        now = datetime.now(UTC)
        if value < now - timedelta(minutes=1) or value > now + timedelta(days=6):
            raise serializers.ValidationError("Departure must be in the next six days.")
        return value

    def validate(self, attrs):
        if attrs["origin"]["position"] == attrs["destination"]["position"]:
            raise serializers.ValidationError("Choose different origin and destination locations.")
        return attrs


class CorridorSerializer(serializers.Serializer):
    context = serializers.CharField(max_length=128 * 1024)

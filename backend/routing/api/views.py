from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(["GET"])
def health(request):
    """Process health only: deliberately no credentials, database or network dependency."""
    return Response({"status": "ok"})

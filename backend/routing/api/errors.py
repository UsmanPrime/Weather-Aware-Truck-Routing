import logging
from uuid import uuid4

from django.core.exceptions import RequestDataTooBig
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

from routing.providers.errors import ProviderError

from .parsers import PayloadTooLarge


def exception_handler(exc, context):
    request_id = str(uuid4())
    if isinstance(exc, ProviderError):
        return Response({"error": exc.as_dict(request_id)}, status=exc.http_status)
    # DRF also enforces Django's body limit before invoking our bounded parser.
    if isinstance(exc, RequestDataTooBig):
        exc = PayloadTooLarge()
    response = drf_exception_handler(exc, context)
    if response is not None:
        response.data = {
            "error": {
                "code": f"http_{response.status_code}",
                "message": "Request could not be processed.",
                "retryable": response.status_code == 429,
                "request_id": request_id,
                "fields": response.data,
            }
        }
    else:
        logging.getLogger(__name__).error(
            "api_failure request_id=%s type=%s", request_id, type(exc).__name__
        )
        response = Response(
            {
                "error": {
                    "code": "internal_error",
                    "message": "The service could not complete this request. Try again shortly.",
                    "retryable": False,
                    "request_id": request_id,
                }
            },
            status=500,
        )
    return response

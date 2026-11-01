import json

from rest_framework.exceptions import APIException, ParseError
from rest_framework.parsers import JSONParser


class PayloadTooLarge(APIException):
    status_code = 413
    default_detail = "Request body exceeds 256 KiB."


class BoundedJSONParser(JSONParser):
    def parse(self, stream, media_type=None, parser_context=None):
        raw = stream.read(256 * 1024 + 1)
        if len(raw) > 256 * 1024:
            raise PayloadTooLarge()
        try:
            return json.loads(raw)
        except (ValueError, UnicodeError):
            raise ParseError("Invalid JSON request.") from None

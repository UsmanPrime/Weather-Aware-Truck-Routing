import os
import re
import secrets
import subprocess
import sys

from django.test import override_settings
from rest_framework.test import APIClient


@override_settings(DEBUG=False, SECURE_SSL_REDIRECT=True)
def test_production_redirects_http_and_sets_security_headers():
    client = APIClient()
    assert client.get("/api/v1/health").status_code == 301
    response = client.get("/api/v1/health", secure=True)
    assert response.status_code == 200
    assert response["X-Content-Type-Options"] == "nosniff"
    assert response["X-Frame-Options"] == "DENY"


@override_settings(CORS_ALLOWED_ORIGINS=["https://web.example.test"])
def test_exact_origin_cors_and_preflight():
    client = APIClient()
    accepted = client.options(
        "/api/v1/plans",
        HTTP_ORIGIN="https://web.example.test",
        HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
    )
    assert accepted.status_code == 200
    assert accepted["Access-Control-Allow-Origin"] == "https://web.example.test"
    assert "Access-Control-Allow-Credentials" not in accepted
    blocked = client.get("/api/v1/health", HTTP_ORIGIN="https://other.example.test")
    assert "Access-Control-Allow-Origin" not in blocked


def test_actual_production_system_checks_have_only_intentional_hsts_warnings():
    environment = os.environ.copy()
    environment.update(
        DJANGO_DEBUG="false",
        DJANGO_SECRET_KEY=secrets.token_urlsafe(48),
        DJANGO_ALLOWED_HOSTS="api.example.test",
        CORS_ALLOWED_ORIGINS="https://web.example.test",
    )
    result = subprocess.run(
        [sys.executable, "manage.py", "check", "--deploy"],
        env=environment,
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr
    warnings = set(re.findall(r"security\.W\d+", result.stderr))
    assert warnings == {"security.W005", "security.W021"}

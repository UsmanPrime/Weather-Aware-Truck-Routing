"""Linux-only real Gunicorn startup check. No provider calls or credentials required."""

import json
import os
import secrets
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, Request, build_opener


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def main():
    if sys.platform != "linux":
        raise SystemExit("Run this production startup check on Linux (WSL or CI).")
    backend = Path(__file__).resolve().parents[1] / "backend"
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    environment = os.environ.copy()
    environment.update(
        DJANGO_DEBUG="false",
        DJANGO_SECRET_KEY=secrets.token_urlsafe(48),
        DJANGO_ALLOWED_HOSTS="127.0.0.1",
        RENDER_EXTERNAL_HOSTNAME="127.0.0.1",
        CORS_ALLOWED_ORIGINS="https://web.example.test",
        PORT=str(port),
    )
    opener = build_opener(NoRedirect())
    health = f"http://127.0.0.1:{port}/api/v1/health"
    with tempfile.TemporaryFile() as logs:
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "gunicorn",
                "config.wsgi:application",
                "--config",
                "gunicorn.conf.py",
            ],
            cwd=backend,
            env=environment,
            stdout=logs,
            stderr=logs,
        )
        try:
            deadline = time.monotonic() + 45
            while True:
                if process.poll() is not None:
                    raise RuntimeError("Gunicorn exited before becoming healthy.")
                try:
                    request = Request(health, headers={"X-Forwarded-Proto": "https"})
                    with opener.open(request, timeout=2) as response:
                        assert response.status == 200
                        assert json.load(response) == {"status": "ok"}
                        assert response.headers["X-Content-Type-Options"] == "nosniff"
                        assert response.headers["Strict-Transport-Security"] == "max-age=3600"
                    break
                except OSError:
                    if time.monotonic() >= deadline:
                        logs.seek(0)
                        print(logs.read().decode("utf-8", errors="replace"), file=sys.stderr)
                        raise RuntimeError("Gunicorn health startup deadline exceeded.") from None
                    time.sleep(0.1)
            try:
                opener.open(health, timeout=2)
                raise AssertionError("Production HTTP did not redirect to HTTPS.")
            except HTTPError as error:
                assert error.code == 301
                assert error.headers["Location"].startswith("https://")
            for origin, allowed in [
                ("https://web.example.test", True),
                ("https://other.example.test", False),
            ]:
                request = Request(health, headers={"X-Forwarded-Proto": "https", "Origin": origin})
                with opener.open(request, timeout=2) as response:
                    assert (
                        response.headers.get("Access-Control-Allow-Origin") == origin
                    ) == allowed
            request = Request(
                health.replace("/health", "/plans"),
                method="OPTIONS",
                headers={
                    "X-Forwarded-Proto": "https",
                    "Origin": "https://web.example.test",
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "content-type",
                },
            )
            with opener.open(request, timeout=2) as response:
                assert response.status == 200
                assert response.headers["Access-Control-Allow-Origin"] == "https://web.example.test"
            print(
                json.dumps(
                    {
                        "status": "passed",
                        "checks": 5,
                        "server": "real Linux Gunicorn, 1 process / 4 threads",
                        "note": (
                            "Loopback and simulated trusted-proxy header; "
                            "not public TLS or hosted verification. No provider requests."
                        ),
                    }
                )
            )
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


if __name__ == "__main__":
    main()

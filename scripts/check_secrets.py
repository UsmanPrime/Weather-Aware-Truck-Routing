"""Focused local/history scan. Reports locations/rules, never matched credential values."""

import argparse
import json
import os
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GIT = ["git", "-c", f"safe.directory={ROOT.as_posix()}"]
PATTERNS = {
    "private_key": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "aws_access_key": re.compile(rb"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "github_token": re.compile(rb"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b"),
    "jwt_credential": re.compile(
        rb"\beyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}\b"
    ),
    "quoted_key_assignment": re.compile(
        rb"""(?i)(?:ORS_API_KEY|HERE_API_KEY|DJANGO_SECRET_KEY)\s*[=:]\s*["']([^"'\r\n]+)["']"""
    ),
}


def git(*args):
    return subprocess.check_output(GIT + list(args), cwd=ROOT)


def run_scan():
    configured = []
    for key in ("ORS_API_KEY", "HERE_API_KEY", "DJANGO_SECRET_KEY"):
        value = os.environ.get(key, "")
        if value and len(value) > 12:
            configured.append(value.encode())
    env = ROOT / "backend/.env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            key, sep, value = line.partition("=")
            if sep and key.strip() in ("ORS_API_KEY", "HERE_API_KEY", "DJANGO_SECRET_KEY"):
                value = value.strip().strip('"').strip("'")
                if len(value) > 12:
                    configured.append(value.encode())
    findings = []

    def scan(content, location):
        for rule, pattern in PATTERNS.items():
            if pattern.search(content):
                findings.append({"location": location, "rule": rule})
        if any(value in content for value in configured):
            findings.append({"location": location, "rule": "configured_local_secret"})

    files = [name for name in git("ls-files", "-z").decode("utf-8").split("\0") if name]
    for name in files:
        path = ROOT / name
        if path.is_file():
            scan(path.read_bytes(), "working:" + name)
        if path.name == ".env":
            findings.append({"location": name, "rule": "tracked_environment"})
    objects = git("rev-list", "--objects", "--all").decode("utf-8").splitlines()
    process = subprocess.Popen(
        GIT + ["cat-file", "--batch"], cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE
    )
    blobs = 0
    try:
        for entry in objects:
            oid, _, name = entry.partition(" ")
            process.stdin.write((oid + "\n").encode())
            process.stdin.flush()
            header = process.stdout.readline().split()
            content = process.stdout.read(int(header[2]))
            process.stdout.read(1)
            if header[1] == b"blob":
                blobs += 1
                scan(content, "history:" + oid[:12] + ":" + name)
    finally:
        process.stdin.close()
        process.wait()
    return {
        "run_at": datetime.now(UTC).isoformat(),
        "scope": "tracked working files and all reachable Git-history blobs",
        "tracked_files": len(files),
        "history_blobs": blobs,
        "configured_secret_values_checked": len(set(configured)),
        "rules": list(PATTERNS),
        "findings": findings,
        "limitations": (
            "Focused patterns and exact configured local secrets; "
            "not a guarantee for every secret format."
        ),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    options = parser.parse_args()
    report = run_scan()
    encoded = json.dumps(report, indent=2) + "\n"
    if options.output:
        Path(options.output).write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    raise SystemExit(1 if report["findings"] else 0)

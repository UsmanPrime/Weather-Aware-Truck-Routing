"""Create local server configuration without overwriting credentials or printing secrets."""

import re
import secrets
from pathlib import Path

root = Path(__file__).resolve().parents[1]
template = root / "backend/.env.example"
destination = root / "backend/.env"
content = (
    destination.read_text(encoding="utf-8")
    if destination.exists()
    else template.read_text(encoding="utf-8")
)
if re.search(r"^DJANGO_SECRET_KEY=\s*$", content, re.MULTILINE):
    content = re.sub(
        r"^DJANGO_SECRET_KEY=[ \t]*$",
        lambda _: "=".join(("DJANGO_SECRET_KEY", secrets.token_urlsafe(48))),
        content,
        flags=re.MULTILINE,
    )
elif not re.search(r"^DJANGO_SECRET_KEY=", content, re.MULTILINE):
    content += "\n" + "=".join(("DJANGO_SECRET_KEY", secrets.token_urlsafe(48))) + "\n"
destination.write_text(content, encoding="utf-8")
print(
    "Local backend environment ready; existing credentials preserved. "
    "Configure ORS_API_KEY server-side."
)

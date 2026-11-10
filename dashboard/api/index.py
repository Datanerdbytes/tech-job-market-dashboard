"""Vercel Python serverless entry point.

Dash is Flask under the hood, so Vercel's Python runtime serves the WSGI app
directly. The dashboard is read-only (snapshot JSONs committed to the repo),
which is what makes a serverless deployment viable: no writable filesystem,
background workers, or session state are needed at request time.
"""

import sys
from pathlib import Path

# The function lives in api/, but the app package (app.py, pages/, layout/,
# callbacks, data) lives at the project root — make it importable.
ROOT = Path(__file__).resolve().parent.parent
for p in (str(ROOT), str(ROOT / "dashboard")):
    if p not in sys.path:
        sys.path.insert(0, p)

from app import server  # noqa: E402  (Dash's Flask WSGI server)

app = server

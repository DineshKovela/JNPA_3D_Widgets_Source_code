#!/bin/sh
# Serves the multi-file app (web/index.html + web/data) on http://localhost:8000
cd "$(dirname "$0")/web" && (sleep 1; (xdg-open http://localhost:8000/index.html || open http://localhost:8000/index.html) >/dev/null 2>&1) & python3 -m http.server 8000

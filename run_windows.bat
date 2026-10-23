@echo off
REM Serves the multi-file app (web/index.html + web/data) on http://localhost:8000
cd /d "%~dp0web"
start "" http://localhost:8000/index.html
python -m http.server 8000 || py -m http.server 8000

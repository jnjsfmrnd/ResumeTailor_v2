#!/usr/bin/env bash
set -euo pipefail

cd /home/site/wwwroot

# App Service startup command for Django/Gunicorn.
exec gunicorn --bind=0.0.0.0 --timeout 600 resumetailor.wsgi
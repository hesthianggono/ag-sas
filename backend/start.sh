#!/bin/bash
# Startup script untuk Render deployment
set -e

echo "==> Initializing database..."
python -c "from app.db.init_db import init_db; init_db()"

echo "==> Starting server..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}

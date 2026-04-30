#!/bin/sh
set -e

echo "→ Running migrations..."
uv run alembic upgrade head

echo "→ Checking seed status..."
SEEDED=$(uv run python -c "
import asyncio, os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def check():
    engine = create_async_engine(os.environ['DATABASE_URL'])
    async with engine.connect() as conn:
        result = await conn.execute(text('SELECT COUNT(*) FROM staff_user'))
        print('yes' if result.scalar() > 0 else 'no')
    await engine.dispose()

asyncio.run(check())
" 2>/dev/null || echo "no")

if [ "$SEEDED" = "no" ]; then
    echo "→ Seeding dev data..."
    uv run python scripts/seed/seed_dev.py
else
    echo "→ Already seeded, skipping."
fi

echo "→ Starting API on :3002"
exec uv run uvicorn apps.api.main:app --host 0.0.0.0 --port 3002

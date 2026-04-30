FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY apps/ apps/
COPY migrations/ migrations/
COPY scripts/ scripts/
COPY alembic.ini ./

RUN chmod +x apps/api/entrypoint.sh

EXPOSE 3002

ENTRYPOINT ["apps/api/entrypoint.sh"]

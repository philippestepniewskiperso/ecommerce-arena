# E-Commerce Sandbox

Vanilla e-commerce platform designed as a realistic sandbox for agentic use cases. No AI layer — all services run locally.

## Quick start (Docker only)

```bash
git clone <repo> && cd <repo>
docker compose up
```

- Storefront → http://localhost:3000
- Back-office → http://localhost:3001
- Mailpit UI → http://localhost:8025
- MinIO console → http://localhost:9001

Reset: `docker compose down -v && docker compose up`

## Dev setup (Node + pnpm + Python + uv)

**Prerequisites**: Node 20+, pnpm 9+, Python 3.12+, uv, Docker Desktop

```bash
cp .env.example .env
pnpm install        # TS deps
uv sync             # Python deps
pnpm setup          # docker up + migrations + seed:dev
pnpm dev            # storefront :3000 + backoffice :3001 + api :3002
```

## Commands

```bash
pnpm dev             # all apps in parallel
pnpm seed:dev        # ~30s: 20 products, 10 customers, 50 orders
pnpm seed:full       # ~5-10min: 500 products, 5k customers, 20k orders
pnpm reset           # truncate all tables + re-seed:dev
pnpm db:migrate      # apply pending Alembic migrations
pnpm lint
pnpm typecheck
pnpm test
pnpm e2e
```

## Demo accounts

| Email | Password | Role |
|---|---|---|
| admin@demo.local | demo1234 | admin |
| ops@demo.local | demo1234 | ops_manager |
| cs@demo.local | demo1234 | cs_agent |

## Architecture

```
apps/storefront/   Next.js 14 — public shop (port 3000)
apps/backoffice/   Next.js 14 — staff dashboard (port 3001)
apps/api/          FastAPI + Uvicorn — all business logic (port 3002)
packages/ui/       Shared React components
scripts/seed/      seed_dev.py + seed_full.py
scripts/etl/       Postgres → DuckDB
migrations/        Alembic
```

API docs: http://localhost:3002/api/docs

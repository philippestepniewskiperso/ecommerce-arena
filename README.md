# E-Commerce Sandbox

![CI](https://github.com/philippe-stepniewski/ecommerce-sandbox/actions/workflows/ci.yml/badge.svg)

Vanilla e-commerce platform designed as a realistic sandbox for agentic use cases. No AI layer — all services run locally.

## Quick start (Docker only)

**Requires**: Docker Desktop (or Docker Engine)

```bash
git clone <repo> && cd <repo>
docker compose up
```

First run builds images locally (~5 min). Subsequent starts take ~30s.

| Service | URL |
|---|---|
| Storefront | http://localhost:3000 |
| Back-office | http://localhost:3001 |
| API docs | http://localhost:3002/api/docs |
| Mailpit UI | http://localhost:8025 |
| MinIO console | http://localhost:9001 |

Reset everything: `docker compose down -v && docker compose up`

## Dev setup (Node + pnpm + Python + uv)

**Prerequisites**: Node 20+, pnpm 9+, Python 3.12+, uv, Docker Desktop

```bash
cp .env.example .env
pnpm install        # TS deps
uv sync             # Python deps
pnpm setup          # start infra (Docker) + run migrations + seed:dev
pnpm dev            # storefront :3000 + backoffice :3001 + api :3002
```

## Commands

```bash
pnpm dev             # all apps in parallel
pnpm seed:dev        # ~30s: 20 products, 50 customers, 200 orders
pnpm seed:full       # ~5-10min: 500 products, 5k customers, 20k orders
pnpm reset           # truncate all tables + re-seed:dev
pnpm db:migrate      # apply pending Alembic migrations
pnpm lint
pnpm typecheck
pnpm test            # pytest (Python API tests)
pnpm e2e             # Playwright — requires full stack running
```

## Demo accounts

| Email | Password | Role |
|---|---|---|
| admin@demo.local | demo1234 | admin |
| ops@demo.local | demo1234 | ops_manager |
| cs@demo.local | demo1234 | cs_agent |

## Features

- **Catalogue** — products, variants, stock levels, full-text search (Postgres tsvector)
- **Checkout** — cart, orders, mock payment, mock carrier with label + tracking
- **Customer account** — order history, support tickets
- **Live chat** — WebSocket-based customer ↔ staff chat; widget on storefront, panel in back-office
- **Back-office** — PIM, OMS, CRM, support queue, staff RBAC
- **Event bus** — `domain_event` table + SSE stream + outbound webhooks (HMAC-signed) for agents
- **Auth** — customer sessions, staff RBAC (5 roles), API keys for M2M agents

## Architecture

```
apps/storefront/   Next.js 14 — public shop (port 3000)
apps/backoffice/   Next.js 14 — staff dashboard (port 3001)
apps/api/          FastAPI + Uvicorn — all business logic (port 3002)
packages/ui/       Shared React components
scripts/seed/      seed_dev.py + seed_full.py
migrations/        Alembic
e2e/               Playwright tests
tests/             Python pytest (API integration tests)
```

API docs: http://localhost:3002/api/docs

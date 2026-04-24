# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

A vanilla e-commerce sandbox (no AI layer) designed as a realistic testbed for agentic use cases. Everything runs locally; no cloud services required.

## Dev style

- Avoid defensive code !
- Prioritize realism and business logic complexity over engineering best practices, performance optimizations, or edge cases.
- Prioritize clear and understandable code over clever or "elegant" solutions. Verbose, straightforward implementations are preferred.

## Setup

### Simulator user (monkey proof — Docker only)
```bash
git clone <repo> && cd <repo>
docker compose up
# Done. Storefront :3000, back-office :3001. Seeded automatically.
# Reset: docker compose down -v && docker compose up
```

### Contributor (Node + pnpm + Python + uv)
```bash
cp .env.example .env
pnpm install        # deps TS
uv sync             # deps Python (FastAPI, SQLAlchemy, Alembic, etc.)
pnpm setup          # docker up + alembic upgrade head + seed_dev.py
pnpm dev            # turbo: storefront + backoffice + uvicorn
```

## Commands

```bash
# Dev
pnpm dev                      # All apps in parallel via Turborepo

# Seed
pnpm seed:dev                 # Fast (~30s): 20 products, 10 customers, 50 orders
pnpm seed:full                # Realistic (~5-10 min): 500 products, 5k customers, 20k orders
pnpm reset                    # Truncate all tables + re-seed:dev

# Quality
pnpm lint
pnpm typecheck
pnpm test                     # Vitest (unit + integration)
pnpm test --filter=<pkg>      # Single package
pnpm e2e                      # Playwright

# DB
pnpm db:migrate               # Apply pending Drizzle migrations
pnpm db:studio                # Drizzle Studio

# Images
pnpm import:images ./path/    # Import user-supplied product images into MinIO
```

## Local ports

| Service | URL |
|---|---|
| Storefront | localhost:3000 |
| Back-office | localhost:3001 |
| Mailpit UI | localhost:8025 |
| MinIO console | localhost:9001 |

## Demo staff accounts (created by seed:dev)

| Email | Password | Role |
|---|---|---|
| admin@demo.local | demo1234 | admin |
| ops@demo.local | demo1234 | ops_manager |
| cs@demo.local | demo1234 | cs_agent |

## Architecture

pnpm workspaces + Turborepo monorepo (TS apps) + uv (Python backend):

```
apps/storefront/       Next.js 14 App Router — public-facing shop (port 3000) — TS
apps/backoffice/       Next.js 14 App Router — staff-only, RBAC-gated (port 3001) — TS
apps/api/              FastAPI + Uvicorn — all business logic (port 3002) — Python
  routers/             public/, customer/, admin/, events/, webhooks/
  models/              SQLAlchemy models (12 domains)
  schemas/             Pydantic schemas (request/response)
  auth/                sessions, api_keys, RBAC middleware
  mocks/               payment_mock.py, carrier_mock.py
packages/ui/           Shared React components — TS
packages/config/       TypeScript, ESLint — TS
scripts/seed/          seed_dev.py + seed_full.py — Python
scripts/etl/           etl.py Postgres → DuckDB — Python
migrations/            Alembic migrations
pyproject.toml         uv root — FastAPI + scripts + Alembic
```

Next.js apps are pure frontends that call FastAPI. No business logic in TS.

### Data layer

- **OLTP**: Postgres 16 via SQLAlchemy 2.0 async. Migrations Alembic. 12 domains: `auth`, `catalog`, `inventory`, `customer`, `order`, `payment`, `shipping`, `support`, `marketing`, `cms`, `audit`, `events`.
- **DWH**: DuckDB (local file). Fed by ETL scripts from Postgres. Back-office dashboards read it directly.
- **Object store**: MinIO — product images (user-supplied, never generate or use placeholders), PDFs, email attachments.
- **Event bus**: `domain_event` table (Postgres) + SSE stream at `/api/events/stream` + outbound webhooks via `webhook_subscription`. No external broker. Agents subscribe via `POST /api/webhooks`, receive HMAC-signed payloads.

### Search

Postgres full-text search (`tsvector`) on product `name` + `description` + `category`. No external search service.

### Payment

Default: internal mock (`packages/payment-mock`). Stripe test mode opt-in via `PAYMENT_PROVIDER=stripe` in `.env`.

### Auth (`apps/api/auth/` — Python)

Three auth modes:

- **Customer**: email+password, optional TOTP, 30-day sessions.
- **Staff**: invite-only, mandatory TOTP, 2h sessions + refresh token, RBAC with roles (`admin`, `ops_manager`, `cs_agent`, `marketer`, `finance`) and granular permissions (`products.write`, `orders.refund`, `customers.read`, …).
- **Agent (M2M)**: `Authorization: Bearer <key>` header, validated against `api_key.key_hash` + scopes. No session, no browser, no TOTP. `seed:dev` generates demo keys listed in README.

FastAPI dependencies: `require_customer()`, `require_staff(role | permission)`, `require_api_key(scopes[])`. All sensitive actions write to `audit_log`.

Dev bypasses (active by default via `.env.example`): `TOTP_SKIP=true`, `EMAIL_VERIFY_SKIP=true`.

### Event bus (agentic surface)

14 business events emitted after every significant mutation:
`order.placed`, `order.cancelled`, `order.shipped`, `order.delivered`, `payment.succeeded`, `payment.failed`, `return.requested`, `return.approved`, `stock.low`, `ticket.created`, `ticket.escalated`, `cart.abandoned`, `customer.signup`, `campaign.sent`.

External agents subscribe via `POST /api/webhooks` and receive HMAC-signed JSON payloads.

### External mocks (all local)

- **Payment**: internal mock by default, Stripe test mode opt-in.
- **Carrier**: mock generating label PDFs and simulating tracking state transitions.
- **Email**: all transactional mail via Mailpit (SMTP).

## Implementation phases (current status: not started)

Critical path: **0 → 1 → 2 → 3 → 3b → (4 ∥ 5) → 6 → 8 → 9 → 10**

| Phase | Scope |
|---|---|
| 0 | Monorepo foundations, Docker Compose + healthchecks, `.env.example`, `pnpm setup`, GitHub Actions CI |
| 1 | SQLAlchemy OLTP models + Alembic migrations (12 domains) |
| 2 | Auth Python (customer + staff RBAC), dev bypasses for TOTP + email verify |
| 3 | REST API (public + customer + admin), Pydantic, OpenAPI, bulk ops, recommendations |
| 3b | Event bus: `domain_event` table, SSE stream, outbound webhooks — primary agentic hook |
| 4 | Storefront: catalogue, PLP/PDP, Postgres FTS search, cart, checkout, account |
| 5 | Back-office: all 12 modules (PIM, OMS, CRM, Support, …) — ~30-40% of total effort |
| 6 | External mocks: payment mock (default), carrier, MailHog, MinIO + image import script |
| 7 | PDF generation (invoices, credit notes), MJML email templates |
| 8 | Realistic seed:full script |
| 9 | DuckDB DWH + Python ETL scripts |
| 10 | Structured logs, audit log UI, Playwright E2E, `pnpm reset`, public README |

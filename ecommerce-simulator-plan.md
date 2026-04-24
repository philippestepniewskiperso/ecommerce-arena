# E-Commerce Simulator — Implementation Plan

Vanilla e-commerce platform designed as a realistic sandbox for agentic use cases.
No AI/agent layer in the architecture — surfaces are clean, all services run locally.
Commit at each big phase. Keep simple and short commits message (one line)

**Public repo design constraints** (apply throughout all phases):

### Deux personas, deux entrées

| | Utilisateur simulateur | Contributeur |
|---|---|---|
| Profil | Dev agentique qui veut un e-commerce qui tourne | Dev qui travaille sur le simulateur lui-même |
| Prérequis | Docker Desktop uniquement | Node 20+, pnpm 9+, Docker Desktop |
| Commande | `docker compose up` | `pnpm install && pnpm setup && pnpm dev` |
| Seed | Automatique au premier démarrage | `pnpm seed:dev` ou `seed:full` |

**Règle** : `docker compose up` seul doit produire un simulateur complet, seedé, prêt à recevoir des agents. Zéro étape manuelle, zéro compte cloud, zéro connaissance Node/pnpm requise.

### Autres contraintes
- No ambiguous tech choices — one answer per layer
- `seed:dev` (≤ 30s) for CI and quick onboarding; `seed:full` (5-10 min) for realistic data
- All secrets pre-wired in `docker-compose.yml` env defaults — no `.env` file needed for simulator users
- Dev mode bypasses active by default (`TOTP_SKIP`, `EMAIL_VERIFY_SKIP`)

---

## Architecture Overview

```
┌────────────────────────────────┐    ┌─────────────────────────────┐
│      CLIENTS (front public)    │    │    STAFF (back-office)      │
│   navigateur web / mobile web  │    │  admins · ops · CS · market │
└──────────────┬─────────────────┘    └──────────────┬──────────────┘
               │                                     │
    ┌──────────▼───────────┐           ┌─────────────▼────────────┐
    │  STOREFRONT          │           │  BACK-OFFICE             │
    │  (Next.js public)    │           │  (Next.js privé, SSO)    │
    │  - catalogue         │           │  - dashboard KPI         │
    │  - PDP / PLP         │           │  - PIM (produits)        │
    │  - panier / checkout │           │  - OMS (commandes)       │
    │  - compte client     │           │  - CRM (clients)         │
    │  - blog / CMS pages  │           │  - support console       │
    └──────────┬───────────┘           │  - stock / entrepôt      │
               │                       │  - promo / pricing       │
               └────────┬──────────────│  - campagnes email       │
                        │              │  - CMS / merchandising   │
                        │              │  - rôles & permissions   │
                        │              │  - audit log             │
                        │              └─────────────┬────────────┘
                        │                            │
                        └──────────────┬─────────────┘
                                       │
               ┌───────────────────────▼────────────────────┐
               │                BACK API (Node)             │
               │   Public endpoints  +  Admin endpoints     │
               │   auth, RBAC, rate-limit, audit            │
               └──┬─────────────┬──────────────┬────────────┘
                  │             │              │
           ┌──────▼──┐   ┌──────▼───┐   ┌─────▼──────────────┐
           │  OLTP   │   │  OBJECT  │   │  SERVICES EXTERNES │
           │Postgres │   │  STORE   │   │  (mocks locaux)    │
           │         │   │  MinIO   │   │  - SMTP (MailHog)  │
           │         │   │  PDFs,   │   │  - Stripe mock     │
           │         │   │  images  │   │  - carrier mock    │
           └──────┬──┘   └──────────┘   └────────────────────┘
                  │ ETL nightly
           ┌──────▼─────────────────┐
           │  DWH (DuckDB)          │
           │  dim_* / fct_*         │
           │  consommé par BO       │
           └────────────────────────┘
```

---

## Tech Stack

| Couche | Choix | Raison |
|---|---|---|
| Monorepo | pnpm workspaces + Turborepo | |
| Front | Next.js 14 (App Router) — TypeScript | |
| Back API | **FastAPI + Uvicorn** — Python | Audience agentique = Python natif |
| ORM | **SQLAlchemy 2.0 async** — Python | |
| Migrations | **Alembic** — Python | |
| Auth | **passlib + python-jose + pyotp** — Python | |
| Validation | **Pydantic v2** — Python (inclus FastAPI) | |
| OLTP | Postgres 16 (Docker) | |
| DWH | DuckDB (fichier local) | Bindings Python first-class |
| ETL | **Scripts Python** (`scripts/etl/`) | |
| Seed | **Python + Faker** (`scripts/seed/`) | |
| Object store | MinIO (Docker) | |
| Mail | MailHog (Docker) | |
| Paiement | **Mock Python** (`apps/api/mocks/payment.py`) | Pas de compte Stripe requis. Stripe opt-in via `PAYMENT_PROVIDER=stripe` |
| Deps Python | **uv** (`pyproject.toml` racine) | |
| Tests back | **pytest + httpx** | |
| Tests front | Vitest + Playwright (E2E) | |
| CI | GitHub Actions | |

---

## Auth Design

Deux couches d'auth distinctes via **Lucia**, package partagé `packages/auth`.

### Customer auth
- Signup self-service, login email+password
- 2FA optionnelle (TOTP)
- Sessions longues (30j, cookie httpOnly)
- **Dev** : `EMAIL_VERIFY_SKIP=true` désactive la vérification email

### Staff auth
- Login sur invitation uniquement
- 2FA obligatoire (TOTP)
- Sessions courtes (2h + refresh token)
- RBAC : rôles `admin`, `ops_manager`, `cs_agent`, `marketer`, `finance`
- Permissions granulaires : `products.write`, `orders.refund`, `customers.read`, ...
- **Dev** : `TOTP_SKIP=true` désactive le 2FA — seed crée staff avec mot de passe connu

### Agent auth (machine-to-machine)
- API keys statiques, header `Authorization: Bearer <key>`
- Scope = sous-ensemble de permissions staff (`products.read`, `orders.write`, etc.)
- `seed:dev` génère clés de démo listées dans README
- Pas de session, pas de browser, pas de TOTP

### Modèle de données auth

```
customer
  id, email, password_hash, email_verified_at,
  mfa_enabled, created_at, last_login_at, status

staff_user
  id, email, password_hash, mfa_secret,
  status (active/suspended), last_login_at

role                      # admin, ops_manager, cs_agent, marketer, finance
permission                # products.write, orders.refund, customers.read, ...
role_permission           # N:N
staff_user_role           # N:N (cumul de rôles possible)

session
  id, principal_type ('customer'|'staff'),
  principal_id, token_hash, ip, ua,
  created_at, expires_at, revoked_at

api_key
  id, name, key_hash, scopes (text[]),
  created_at, last_used_at, revoked_at

audit_log
  id, actor_type, actor_id, action,
  resource_type, resource_id, payload, ip, created_at
```

---

## OLTP — Entités principales

```
customer ──< address
customer ──< order ──< order_item >── product >── category
                │                         │
                ├──< payment              ├──< review
                ├──< shipment             └──< stock_movement
                └──< return_request

customer ──< session ──< event
customer ──< support_ticket ──< ticket_message
campaign ──< campaign_recipient >── customer
```

Domaines SQLAlchemy : `auth`, `catalog`, `inventory`, `customer`, `order`,
`payment`, `shipping`, `support`, `marketing`, `cms`, `audit`, `events`

Domain `events` : `domain_event`, `webhook_subscription`, `webhook_delivery`

---

## Monorepo Structure

```
/
├── apps/
│   ├── storefront/        # Next.js (TS) — port 3000
│   ├── backoffice/        # Next.js (TS) — port 3001
│   └── api/               # FastAPI (Python) — port 3002
│       ├── package.json   # wrapper Turborepo: "dev": "uvicorn main:app --reload"
│       ├── main.py
│       ├── routers/       # public/, customer/, admin/, events/, webhooks/
│       ├── models/        # SQLAlchemy models par domaine
│       ├── schemas/       # Pydantic schemas (request/response)
│       ├── auth/          # sessions, api_keys, RBAC, middleware
│       └── mocks/         # payment_mock.py, carrier_mock.py
├── packages/
│   ├── ui/                # Shared React components (TS)
│   └── config/            # TypeScript, ESLint (TS)
├── scripts/
│   ├── seed/              # seed_dev.py + seed_full.py (Python)
│   └── etl/               # etl.py Postgres → DuckDB (Python)
├── migrations/            # Alembic (alembic.ini + versions/)
├── pyproject.toml         # Poetry racine — API + scripts + migrations
├── .env.example
├── docker-compose.yml     # Postgres + MailHog + MinIO + Adminer, avec healthchecks
└── turbo.json
```

---

## Back-office — Périmètre par module

| Module | Fonctionnalités clés |
|---|---|
| Dashboard | CA, AOV, conversion, top produits, alertes stock, SLA |
| PIM | CRUD produits/variantes/catégories, images, SEO, import CSV |
| OMS | Liste/détail commandes, valider/annuler/rembourser, facture PDF |
| Stock | Niveaux par SKU, mouvements, seuils réappro, picking list |
| CRM | Fiche client 360°, commandes, tickets, LTV, segments, notes |
| Support | File tickets, SLA, assignation, threading, templates, escalade |
| Retours | Validation, étiquettes, remise en stock, avoirs |
| Pricing | Règles de prix, codes promo, ventes flash |
| Marketing | Création campagne, segments, envoi SMTP, stats ouverture/clic |
| CMS | Pages statiques, bannières, carrousels, ordre merchandising |
| Reviews | Modération avis, réponse officielle, signalements |
| Admin | Utilisateurs staff, rôles, audit log, feature flags |

---

## Seed

Deux modes :

| Commande | Durée | Usage |
|---|---|---|
| `pnpm seed:dev` | ≤ 30s | CI, onboarding rapide, reset quotidien |
| `pnpm seed:full` | 5-10 min | Données réalistes, démo, benchmarks |

`seed:dev` produit : 20 produits (3 catégories), 10 clients, 50 commandes, 1 staff par rôle (mdp connu).

`seed:full` produit :

| Entité | Volume |
|---|---|
| Produits | 500, 20 catégories, variantes taille/couleur |
| Clients | 5 000 (cohorts : one-shot, récurrents, VIP, dormants, churned) |
| Commandes | 20 000 sur 12 mois avec saisonnalité (Noël, soldes) |
| Tickets support | ~2 000, corrélés aux commandes à problème |
| Retours | ~8% des commandes, motifs variés |
| Sessions web | Funnel avec drop-offs réalistes |
| Campagnes | ~30, taux ouverture/clic plausibles |

Script déterministe et reproductible. **Images produits non générées** — fournies par l'utilisateur via MinIO ou répertoire `public/images/products/`.

Idempotence via table `seed_meta (version text, seeded_at timestamptz)` — init container check version, skip si déjà seedé à la même version. `docker compose down -v` efface le volume = reset complet.

---

## DWH — Schéma dimensionnel (DuckDB)

```
dim_customer    dim_product    dim_date    dim_category
fct_orders      fct_order_items
fct_sessions    fct_events
fct_tickets     fct_campaigns
```

---

## Local Setup

### Utilisateur simulateur (monkey proof)

Prérequis : Docker Desktop uniquement.

```bash
git clone <repo> && cd <repo>
docker compose up
```

C'est tout. Docker Compose :
1. Démarre Postgres + MailHog + MinIO
2. Pull images pre-build depuis `ghcr.io/<repo>/storefront:latest` et `backoffice:latest` — pas de build local
3. Lance le seed automatiquement via init container (idempotent via table `seed_meta`)

Ports :
- `localhost:3000` — storefront
- `localhost:3001` — back-office
- `localhost:8025` — MailHog UI
- `localhost:9001` — MinIO console

Comptes démo (créés par seed) :

| Email | Mot de passe | Rôle |
|---|---|---|
| admin@demo.local | demo1234 | admin |
| ops@demo.local | demo1234 | ops_manager |
| cs@demo.local | demo1234 | cs_agent |
| customer@demo.local | demo1234 | customer |

Reset complet : `docker compose down -v && docker compose up`

---

### Contributeur

Prérequis : Node 20+, pnpm 9+, Python 3.12+, uv, Docker Desktop.

```bash
git clone <repo> && cd <repo>
cp .env.example .env
pnpm install        # deps TS (Next.js apps)
uv sync             # deps Python (FastAPI + scripts + migrations)
pnpm setup          # docker up + alembic upgrade head + seed_dev.py (~2 min)
pnpm dev            # turbo: storefront + backoffice + uvicorn
```

Aucun service cloud requis.

---

## Phases d'implémentation

### Phase 0 — Fondations monorepo

**Priorité absolue** : `docker compose up` seul produit un simulateur complet.

- Init pnpm workspaces + Turborepo
- Structure apps + packages + scripts
- Tooling : TypeScript strict, ESLint, Prettier, Vitest
- `.env.example` complet, valeurs Docker pré-remplies (pour contributeurs)
- `docker-compose.yml` :
  - Services infra : Postgres + MailHog + MinIO avec **healthchecks**
  - Services app : `storefront` + `backoffice` (Dockerfile multi-stage, prod-optimisé)
  - Service init : `seed` (runs once, exits 0 si DB déjà seedée — idempotent)
  - Toutes les vars d'env inline dans `docker-compose.yml`, pas de fichier `.env` requis
- Script `pnpm setup` pour contributeurs (docker up → wait healthy → migrate → seed:dev)
- GitHub Actions CI : lint + typecheck + test + `seed:dev` + build images + push `ghcr.io/<repo>/{storefront,backoffice}:latest`

**Livrable** :
- Utilisateur : `docker compose up` → pull images GHCR → simulateur complet, seedé, en < 3 min (pas de build local)
- Contributeur : `pnpm setup && pnpm dev` → env de dev fonctionnel

---

### Phase 1 — Modèle de données OLTP
- Models SQLAlchemy par domaine (12 domaines) dans `apps/api/models/`
- Migrations Alembic versionnées dans `migrations/versions/`
- `seed_dev.py` minimal (20 produits, 10 clients, 50 commandes)

**Livrable** : `alembic upgrade head` tourne, requêtes SQLAlchemy fonctionnelles, CI verte.

---

### Phase 2 — Auth Python (customer + staff + agent)
- `apps/api/auth/` — passlib (bcrypt), python-jose (JWT), pyotp (TOTP)
- Customer : signup, login, reset password, sessions Postgres
- Staff : login invitation-only, TOTP, RBAC via `staff_user_role` + `role_permission`
- **Agent (M2M)** : `require_api_key(scopes[])` FastAPI dependency — header `Authorization: Bearer <key>`, hash SHA-256 vérifié contre `api_key.key_hash`
- FastAPI dependencies : `require_customer`, `require_staff(role|permission)`, `require_api_key(scopes[])`
- `audit_log` branché sur actions sensibles
- Pages login sur storefront et BO (appellent FastAPI)
- `TOTP_SKIP=true` + `EMAIL_VERIFY_SKIP=true` lus par FastAPI au démarrage
- `seed_dev.py` génère clés API de démo listées dans README

**Livrable** : login customer/staff fonctionnel + agent peut appeler `/api/admin/orders` avec Bearer token sans browser.

---

### Phase 3 — Back API (socle REST)
- Endpoints publics : `/api/products`, `/api/categories`, `/api/search`, `/api/cart`, `/api/checkout`
- Endpoints client : `/api/account/*`, `/api/orders/*`, `/api/returns/*`, `/api/tickets/*`
- Endpoints admin : `/api/admin/*` tous modules
- Validation Zod, rate-limit, pagination/tri/filtres standardisés
- OpenAPI généré (`/api/openapi.json`)
- **Bulk operations** : `/api/admin/products/bulk`, `/api/admin/orders/bulk` — agents opèrent à l'échelle
- **Recommendation surface** : `/api/products/recommended` (scoré par popularité + historique client)

**Livrable** : toutes les routes documentées OpenAPI, testables curl/Postman, tests d'intégration sur flows critiques.

---

### Phase 3b — Event bus interne (agentic surface)

Bus d'événements léger, sans dépendance externe. Agents écoutent et réagissent aux événements métier.

**Émetteurs** : API émet un événement après chaque mutation significative.

**Événements** :
```
order.placed          order.cancelled       order.shipped
order.delivered       payment.succeeded     payment.failed
return.requested      return.approved       stock.low
ticket.created        ticket.escalated      cart.abandoned
customer.signup       campaign.sent
```

**Transport** : table Postgres `domain_event` + SSE (`/api/events/stream`) + webhook outbound configurable.

```
domain_event
  id, type, aggregate_type, aggregate_id,
  payload (jsonb), created_at, processed_at

webhook_subscription
  id, url, events (text[]), secret, created_at
```

Agents s'enregistrent via `POST /api/webhooks`. Livraison avec signature HMAC + retry.

**Livrable** : agent externe `curl`able peut s'abonner à `order.placed` et recevoir payload JSON signé.

---

### Phase 4 — Storefront (front public)
- Homepage, PLP filtres/tri, PDP
- **Search** : Postgres full-text search (`tsvector`) sur `name` + `description` + `category` — pas de service externe
- Panier persisté (localStorage + sync DB si connecté)
- Checkout multi-étapes (adresse → livraison → paiement mock)
- Espace client : commandes, adresses, retours, tickets, préférences
- Pages CMS statiques (CGV, FAQ, politique retour)
- SEO, responsive

**Livrable** : parcours achat complet depuis navigation jusqu'à confirmation commande.

---

### Phase 5 — Back-office (staff)
- Layout admin, navigation par module, gardes RBAC
- Dashboard KPIs (lecture DWH)
- Tous les modules listés dans le tableau ci-dessus

**Livrable** : un ops peut gérer toute la boutique sans toucher à la DB.

> Note : cette phase représente ~30-40% du travail total.

---

### Phase 6 — Services externes mockés
- **Paiement** : mock interne (`packages/payment-mock`) actif par défaut. Stripe test mode opt-in via `PAYMENT_PROVIDER=stripe`.
- Carrier mock : génération label PDF, tracking avec transitions d'état simulées
- Emails transactionnels via MailHog
- MinIO : PDFs, avoirs. **Images produits fournies par l'utilisateur** — script d'import `pnpm import:images ./mes-images/`

**Livrable** : commande bout-en-bout avec mail reçu dans MailHog, tracking évoluant, facture PDF.

---

### Phase 7 — Génération de documents
- Factures PDF (React-PDF) à la validation commande
- Avoirs PDF sur remboursement
- Templates emails MJML (confirmation, expédition, retour, campagne)

**Livrable** : `storage/documents/` se remplit au fil de l'usage.

---

### Phase 8 — Seed réaliste
- `seed:full` avec Faker + logique métier
- Volumes et cohorts décrits ci-dessus
- Saisonnalité, cohérence temporelle, reproductible
- `seed:dev` renforcé pour couvrir tous les états métier (commandes annulées, tickets escaladés, etc.)

**Livrable** : `pnpm seed:full` produit boutique vivante et crédible.

---

### Phase 9 — DWH (DuckDB) + ETL
- Schéma dimensionnel complet
- Script ETL Node `scripts/etl/` : Postgres → DuckDB (déclenchable manuellement + cron)
- Dashboards BO pointent sur DuckDB en lecture seule

**Livrable** : `warehouse.duckdb` requêtable, dashboards alimentés.

---

### Phase 10 — Observabilité & finitions
- Logs structurés (pino), request IDs propagés
- Audit log consultable dans le BO
- Healthchecks API (`/api/health`)
- README public : architecture, setup, comptes démo, structure événements
- Tests E2E Playwright (achat, retour, gestion admin)
- `pnpm reset` : truncate toutes les tables + re-seed:dev (utile pour démo)

**Livrable** : repo prêt pour publication publique. Contributeur opérationnel en < 5 min.

---

## Ordre de réalisation

**Chemin critique** : 0 → 1 → 2 → 3 → 3b → (4 ∥ 5) → 6 → 8 → 9 → 10

Phase 7 s'insère entre 5 et 6. Phase 3b débloque les use cases agentiques dès Phase 4.

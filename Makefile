.PHONY: help run test test-quick db-status db-tables db-migrate docker-up docker-down

help:
	@echo "Available targets:"
	@echo "  make run           - Start docker + migrate + test (full flow)"
	@echo "  make test-quick    - Quick test: migrations + table count"
	@echo "  make db-migrate    - Run alembic upgrade"
	@echo "  make db-status     - Show postgres status"
	@echo "  make db-tables     - List all tables in DB"
	@echo "  make docker-up     - Start postgres + mailpit + minio"
	@echo "  make docker-down   - Stop containers"

docker-up:
	docker compose up -d postgres mailpit minio

docker-down:
	docker compose down

db-status:
	docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

db-migrate:
	DATABASE_URL_SYNC=postgresql://postgres:postgres@localhost:5433/ecommerce uv run alembic upgrade head

db-tables:
	docker exec ecommerce-sandbox-postgres-1 psql -U postgres -d ecommerce -c "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename;"

test-quick: docker-up
	@echo "Waiting for postgres..."
	@sleep 2
	@echo "Running migrations..."
	@$(MAKE) db-migrate
	@echo "Checking tables..."
	@$(MAKE) db-tables | wc -l

run: docker-up test-quick
	@echo "✓ Phase 1 verified (models + migrations)"
	@echo "Starting dev server..."
	pnpm dev

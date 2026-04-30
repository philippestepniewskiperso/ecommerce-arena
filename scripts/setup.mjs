import { execSync } from "child_process";

function run(cmd, label) {
  console.log(`\n→ ${label}...`);
  execSync(cmd, { stdio: "inherit" });
}

try {
  run("docker compose up -d postgres mailpit minio --wait", "Starting infrastructure (Postgres, Mailpit, MinIO)");
  run("uv sync", "Installing Python dependencies");
  run("uv run alembic upgrade head", "Running database migrations");
  run("uv run python scripts/seed/seed_dev.py", "Seeding development data");
  console.log("\n✓ Setup complete! Run 'pnpm dev' to start development.");
} catch (e) {
  console.error("\n✗ Setup failed:", e.message);
  process.exit(1);
}

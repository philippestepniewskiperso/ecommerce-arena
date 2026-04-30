FROM node:20-alpine

RUN corepack enable pnpm

WORKDIR /app

# Install dependencies (all workspaces — pnpm requires all package.json files)
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/storefront/package.json apps/storefront/
COPY apps/backoffice/package.json apps/backoffice/
COPY apps/api/package.json apps/api/
COPY packages/ui/package.json packages/ui/
COPY packages/config/package.json packages/config/
RUN pnpm install --frozen-lockfile

# Copy source and build
COPY apps/backoffice/ apps/backoffice/
COPY packages/ packages/
ENV NEXT_TELEMETRY_DISABLED=1
RUN pnpm --filter=@ecommerce/backoffice build

EXPOSE 3001

CMD ["pnpm", "--filter=@ecommerce/backoffice", "start"]

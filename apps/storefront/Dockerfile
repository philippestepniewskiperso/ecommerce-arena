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
COPY apps/storefront/ apps/storefront/
COPY packages/ packages/
ENV NEXT_TELEMETRY_DISABLED=1
RUN pnpm --filter=@ecommerce/storefront build

EXPOSE 3000

CMD ["pnpm", "--filter=@ecommerce/storefront", "start"]

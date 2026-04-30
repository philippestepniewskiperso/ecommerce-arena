"""FastAPI application entry point."""
from dotenv import load_dotenv
load_dotenv()

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.api.routers import public, customer, admin, events, chat


async def _webhook_delivery_loop():
    from apps.api.dependencies import AsyncSessionLocal
    from apps.api.events import deliver_webhooks
    while True:
        await asyncio.sleep(30)
        try:
            async with AsyncSessionLocal() as db:
                await deliver_webhooks(db)
        except Exception:
            pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_webhook_delivery_loop())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="ecommerce-arena",
    description="Realistic e-commerce sandbox for agent testing",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(public.router)
app.include_router(customer.router)
app.include_router(admin.router)
app.include_router(events.router)
app.include_router(chat.router)


@app.get("/health")
async def health():
    return {"status": "ok"}

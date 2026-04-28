"""FastAPI application entry point."""
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.api.routers import public, customer, admin, events

app = FastAPI(
    title="ecommerce-arena",
    description="Realistic e-commerce sandbox for agent testing",
    version="0.1.0",
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


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/docs")
async def docs():
    """OpenAPI documentation."""
    return {"message": "See /docs for interactive API docs"}

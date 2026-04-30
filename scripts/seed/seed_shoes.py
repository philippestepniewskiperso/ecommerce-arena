"""Seed shoe products and categories for KICKS storefront."""
import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, delete
import uuid

from apps.api.models import Category, Product

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5433/ecommerce")

async def seed_shoes():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Clear existing
        await session.execute(delete(Product))
        await session.execute(delete(Category))

        # Categories
        categories_data = [
            {"name": "Running", "slug": "running", "description": "Performance running shoes", "position": 0},
            {"name": "Basketball", "slug": "basketball", "description": "Basketball court shoes", "position": 1},
            {"name": "Casual", "slug": "casual", "description": "Everyday casual sneakers", "position": 2},
            {"name": "Streetwear", "slug": "streetwear", "description": "Premium lifestyle footwear", "position": 3},
        ]

        categories = []
        for cat_data in categories_data:
            cat = Category(
                id=uuid.uuid4(),
                name=cat_data["name"],
                slug=cat_data["slug"],
                description=cat_data["description"],
                position=cat_data["position"]
            )
            categories.append(cat)
            session.add(cat)

        await session.flush()

        # Products
        products_data = [
            {
                "category": "Running",
                "name": "Air Velocity Pro",
                "slug": "air-velocity-pro",
                "description": "High-performance running shoe engineered for speed and distance comfort",
                "short_description": "Performance running shoe",
                "base_price": 120.00
            },
            {
                "category": "Running",
                "name": "Velocity Ultra V2",
                "slug": "velocity-ultra-v2",
                "description": "Lightweight racing flat for marathon runners",
                "short_description": "Lightweight racing flat",
                "base_price": 150.00
            },
            {
                "category": "Basketball",
                "name": "Court Storm X",
                "slug": "court-storm-x",
                "description": "Professional basketball court shoe with ankle support",
                "short_description": "Basketball court shoe",
                "base_price": 140.00
            },
            {
                "category": "Basketball",
                "name": "Slam Elite",
                "slug": "slam-elite",
                "description": "Streetwear basketball-inspired sneaker",
                "short_description": "Basketball-inspired sneaker",
                "base_price": 95.00
            },
            {
                "category": "Casual",
                "name": "Urban Stride",
                "slug": "urban-stride",
                "description": "Minimalist everyday casual sneaker",
                "short_description": "Everyday casual sneaker",
                "base_price": 85.00
            },
            {
                "category": "Casual",
                "name": "Classic Canvas",
                "slug": "classic-canvas",
                "description": "Timeless canvas casual shoe",
                "short_description": "Classic canvas sneaker",
                "base_price": 65.00
            },
            {
                "category": "Streetwear",
                "name": "Prestige X Collab",
                "slug": "prestige-x-collab",
                "description": "Limited edition collaborative design with premium materials",
                "short_description": "Limited edition collab",
                "base_price": 200.00
            },
            {
                "category": "Streetwear",
                "name": "Street Legend",
                "slug": "street-legend",
                "description": "Premium lifestyle sneaker with heritage",
                "short_description": "Premium lifestyle sneaker",
                "base_price": 180.00
            },
        ]

        cat_map = {cat.name: cat.id for cat in categories}

        for prod_data in products_data:
            prod = Product(
                id=uuid.uuid4(),
                category_id=cat_map[prod_data["category"]],
                name=prod_data["name"],
                slug=prod_data["slug"],
                description=prod_data["description"],
                short_description=prod_data["short_description"],
                base_price=prod_data["base_price"],
                status="active"
            )
            session.add(prod)

        await session.commit()

        # Verify
        result = await session.execute(select(Product))
        products = result.scalars().all()

        result = await session.execute(select(Category))
        cats = result.scalars().all()

        print(f"✓ Seeded {len(cats)} shoe categories")
        print(f"✓ Seeded {len(products)} shoe products")

if __name__ == "__main__":
    asyncio.run(seed_shoes())

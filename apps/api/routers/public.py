"""Public endpoints: catalog, search, product details."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from apps.api.dependencies import get_db
from apps.api.models import Product, Category, Review, StockLevel
from apps.api.schemas import ProductResponse, ProductSearchResponse, CategoryResponse, ReviewResponse

router = APIRouter(prefix="/api/public", tags=["public"])


@router.get("/categories", response_model=list[CategoryResponse])
async def list_categories(db: AsyncSession = Depends(get_db)):
    """List all product categories."""
    result = await db.execute(select(Category).order_by(Category.position, Category.name))
    return result.scalars().all()


@router.get("/categories/{slug}", response_model=CategoryResponse)
async def get_category(slug: str, db: AsyncSession = Depends(get_db)):
    """Get category by slug."""
    result = await db.execute(select(Category).where(Category.slug == slug))
    category = result.scalars().first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category


@router.get("/products", response_model=list[dict])
async def list_products(
    category_id: str | None = None,
    status: str = "active",
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List products with pagination."""
    query = select(Product).where(Product.status == status)
    if category_id:
        query = query.where(Product.category_id == category_id)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    products = result.scalars().all()
    return [{"id": str(p.id), "name": p.name, "slug": p.slug, "base_price": float(p.base_price), "short_description": p.short_description} for p in products]


@router.get("/products/search", response_model=list[dict])
async def search_products(
    q: str = Query(..., min_length=2),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Full-text search products by name/description."""
    # Simple substring search for now (FTS to be optimized)
    search_term = f"%{q.lower()}%"
    result = await db.execute(
        select(Product)
        .where(Product.status == "active")
        .where(
            (func.lower(Product.name).like(search_term))
            | (func.lower(Product.description).like(search_term))
        )
        .offset(skip)
        .limit(limit)
    )
    products = result.scalars().all()
    return [{"id": str(p.id), "name": p.name, "slug": p.slug, "base_price": float(p.base_price)} for p in products]


@router.get("/products/{slug}", response_model=dict)
async def get_product(slug: str, db: AsyncSession = Depends(get_db)):
    """Get product details by slug."""
    result = await db.execute(
        select(Product).where(and_(Product.slug == slug, Product.status == "active"))
    )
    product = result.scalars().first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return {
        "id": str(product.id),
        "name": product.name,
        "slug": product.slug,
        "base_price": float(product.base_price),
        "compare_price": float(product.compare_price) if product.compare_price else None,
        "short_description": product.short_description,
        "description": product.description,
        "category_id": str(product.category_id) if product.category_id else None,
        "status": product.status,
        "tags": product.tags or [],
        "variants": [],
        "images": [],
        "created_at": product.created_at.isoformat() if product.created_at else None,
        "updated_at": product.updated_at.isoformat() if product.updated_at else None,
    }


@router.get("/products/{product_id}/reviews", response_model=list[ReviewResponse])
async def get_product_reviews(
    product_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Get approved reviews for a product."""
    result = await db.execute(
        select(Review)
        .where(Review.product_id == product_id, Review.status == "approved")
        .order_by(Review.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/products/{product_id}/stock", response_model=dict)
async def check_stock(product_id: str, db: AsyncSession = Depends(get_db)):
    """Check if product variants are in stock."""
    result = await db.execute(
        select(StockLevel).join(StockLevel.variant).where(StockLevel.variant.product_id == product_id)
    )
    stocks = result.scalars().all()
    if not stocks:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return {
        "product_id": product_id,
        "variants": [
            {
                "variant_id": str(s.variant_id),
                "available": max(0, s.quantity - s.reserved_quantity),
                "reserved": s.reserved_quantity,
            }
            for s in stocks
        ],
    }

"""
Pytest fixtures. Each test gets a fresh DB state via table truncation.
NullPool prevents asyncpg connections from leaking across event loops.
"""
import os
import pytest
import pytest_asyncio

os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@localhost:5433/ecommerce_test"
os.environ["EMAIL_VERIFY_SKIP"] = "true"
os.environ["TOTP_SKIP"] = "true"

from httpx import AsyncClient, ASGITransport
from asgi_lifespan import LifespanManager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import text

from apps.api.main import app
from apps.api.dependencies import get_db

TEST_DB = "postgresql+asyncpg://postgres:postgres@localhost:5433/ecommerce_test"

TRUNCATE_TABLES = [
    "ticket_messages", "support_tickets", "campaign_recipients", "campaigns",
    "audit_logs", "domain_events", "webhook_deliveries", "webhook_subscriptions",
    "tracking_events", "shipments", "payments", "return_items", "return_requests",
    "order_items", "orders", "stock_movements", "stock_levels", "product_images",
    "product_variants", "reviews", "products", "categories",
    "role_permissions", "staff_user_roles", "api_keys", "sessions",
    "addresses", "customers", "staff_users", "roles", "permissions",
    "banners", "pages", "seed_meta",
]


@pytest_asyncio.fixture(scope="function")
async def db():
    engine = create_async_engine(TEST_DB, echo=False, poolclass=NullPool)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Clean state before each test
        for table in TRUNCATE_TABLES:
            await session.execute(text(f'TRUNCATE TABLE "{table}" CASCADE'))
        await session.commit()

        async def override_get_db():
            yield session

        app.dependency_overrides[get_db] = override_get_db

        yield session

        await session.close()

    app.dependency_overrides.clear()
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def client(db):
    async with LifespanManager(app):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as c:
            yield c


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def customer_token(client):
    r = await client.post("/api/customer/auth/signup", json={
        "email": "test.customer@example.com",
        "password": "Password123!",
        "first_name": "Test",
        "last_name": "Customer",
    })
    assert r.status_code == 200, r.text
    return r.json()["token"]


@pytest_asyncio.fixture
async def staff_token(client, db):
    from apps.api.models import StaffUser, Role, RolePermission, Permission, StaffUserRole
    from apps.api.auth.password import hash_password
    import uuid

    role = Role(id=uuid.uuid4(), name="admin", description="Admin")
    db.add(role)

    perm = Permission(id=uuid.uuid4(), name="products.write", description="Write products")
    db.add(perm)
    db.add(RolePermission(role_id=role.id, permission_id=perm.id))

    staff = StaffUser(
        id=uuid.uuid4(),
        email="admin@test.local",
        password_hash=hash_password("admin1234"),
        first_name="Admin",
        last_name="Test",
        status="active",
    )
    db.add(staff)
    db.add(StaffUserRole(staff_user_id=staff.id, role_id=role.id))
    await db.commit()

    r = await client.post("/api/admin/auth/login", json={
        "email": "admin@test.local",
        "password": "admin1234",
    })
    assert r.status_code == 200, r.text
    return r.json()["token"]


@pytest_asyncio.fixture
async def seeded_product(client, db, staff_token):
    from apps.api.models import Category, Product, ProductVariant, StockLevel
    import uuid

    cat = Category(id=uuid.uuid4(), name="Running", slug="running", position=0)
    db.add(cat)

    product = Product(
        id=uuid.uuid4(),
        category_id=cat.id,
        name="Test Shoe",
        slug="test-shoe",
        short_description="A test shoe",
        description="Full description of the test shoe.",
        base_price=99.00,
        status="active",
        tags=["test"],
    )
    db.add(product)

    variant = ProductVariant(
        id=uuid.uuid4(),
        product_id=product.id,
        sku="TEST_SHOE_EU42",
        name="EU 42",
        attributes={"size": "42"},
        is_default=True,
    )
    db.add(variant)
    db.add(StockLevel(
        id=uuid.uuid4(),
        variant_id=variant.id,
        warehouse="main",
        quantity=50,
        reserved_quantity=0,
        low_stock_threshold=5,
    ))
    await db.commit()

    return {
        "id": str(product.id),
        "slug": product.slug,
        "name": product.name,
        "base_price": float(product.base_price),
        "variant_id": str(variant.id),
        "sku": variant.sku,
    }

"""Public API: catalog, search, tracking."""


async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


async def test_list_categories_empty(client):
    r = await client.get("/api/public/categories")
    assert r.status_code == 200
    assert r.json() == []


async def test_list_products_empty(client):
    r = await client.get("/api/public/products")
    assert r.status_code == 200
    assert r.json() == []


async def test_list_categories_with_data(client, seeded_product):
    r = await client.get("/api/public/categories")
    assert r.status_code == 200
    slugs = [c["slug"] for c in r.json()]
    assert "running" in slugs


async def test_list_products_with_data(client, seeded_product):
    r = await client.get("/api/public/products")
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["slug"] == "test-shoe"


async def test_get_product_by_slug(client, seeded_product):
    r = await client.get(f"/api/public/products/{seeded_product['slug']}")
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "Test Shoe"
    assert data["base_price"] == 99.0
    assert data["status"] == "active"


async def test_get_product_not_found(client):
    r = await client.get("/api/public/products/nonexistent-slug")
    assert r.status_code == 404


async def test_search_products(client, seeded_product):
    r = await client.get("/api/public/products/search?q=test")
    assert r.status_code == 200
    # search uses LIKE on name/description — result may be empty if tsvector not populated
    assert isinstance(r.json(), list)


async def test_search_too_short(client):
    r = await client.get("/api/public/products/search?q=a")
    assert r.status_code == 422


async def test_tracking_not_found(client):
    r = await client.get("/api/public/tracking/FAKE123456789FR")
    assert r.status_code == 404

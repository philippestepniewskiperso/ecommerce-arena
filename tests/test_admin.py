"""Admin API: staff auth, orders, shipping, support."""


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Staff auth
# ---------------------------------------------------------------------------

async def test_staff_login(client, staff_token):
    assert isinstance(staff_token, str)
    assert len(staff_token) > 10


async def test_staff_login_wrong_password(client, db):
    from apps.api.models import StaffUser
    from apps.api.auth.password import hash_password
    import uuid

    staff = StaffUser(
        id=uuid.uuid4(), email="bad@test.local",
        password_hash=hash_password("correct"), first_name="X", last_name="Y", status="active",
    )
    db.add(staff)
    await db.flush()

    r = await client.post("/api/admin/auth/login", json={"email": "bad@test.local", "password": "wrong"})
    assert r.status_code == 401


async def test_staff_me(client, staff_token):
    r = await client.get("/api/admin/auth/me", headers=auth_headers(staff_token))
    assert r.status_code == 200
    data = r.json()
    assert data["email"] == "admin@test.local"


async def test_admin_requires_auth(client):
    r = await client.get("/api/admin/orders")
    assert r.status_code == 401


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

async def test_dashboard(client, staff_token):
    r = await client.get("/api/admin/dashboard", headers=auth_headers(staff_token))
    assert r.status_code == 200
    data = r.json()
    assert "total_orders" in data
    assert "revenue" in data
    assert "open_tickets" in data


# ---------------------------------------------------------------------------
# Orders + shipping
# ---------------------------------------------------------------------------

async def test_list_orders_empty(client, staff_token):
    r = await client.get("/api/admin/orders", headers=auth_headers(staff_token))
    assert r.status_code == 200
    assert r.json() == []


async def test_list_orders_filter_by_status(client, staff_token, customer_token, seeded_product):
    # Place an order first
    await client.post("/api/customer/checkout", json={
        "items": [{"product_id": seeded_product["id"], "name_snapshot": seeded_product["name"],
                   "sku_snapshot": seeded_product["sku"], "unit_price": seeded_product["base_price"], "quantity": 1}],
        "shipping_address": {"first_name": "T", "last_name": "T", "line1": "1 rue", "city": "Paris",
                             "postal_code": "75001", "country_code": "FR"},
        "card_token": "tok_test",
    }, headers={"Authorization": f"Bearer {customer_token}"})

    r = await client.get("/api/admin/orders?status=confirmed", headers=auth_headers(staff_token))
    assert r.status_code == 200
    # Newly placed order is "confirmed" if payment succeeded
    for o in r.json():
        assert o["status"] == "confirmed"


async def test_ship_order(client, staff_token, customer_token, seeded_product):
    r = await client.post("/api/customer/checkout", json={
        "items": [{"product_id": seeded_product["id"], "name_snapshot": seeded_product["name"],
                   "sku_snapshot": seeded_product["sku"], "unit_price": seeded_product["base_price"], "quantity": 1}],
        "shipping_address": {"first_name": "T", "last_name": "T", "line1": "1 rue", "city": "Paris",
                             "postal_code": "75001", "country_code": "FR"},
        "card_token": "tok_test",
    }, headers={"Authorization": f"Bearer {customer_token}"})
    assert r.status_code == 200
    assert r.json()["payment_status"] == "succeeded"
    order_number = r.json()["order_number"]

    # find the order by listing all orders
    all_orders = await client.get("/api/admin/orders", headers=auth_headers(staff_token))
    order_id = next(o["id"] for o in all_orders.json() if o["number"] == order_number)

    ship = await client.post(f"/api/admin/orders/{order_id}/ship", headers=auth_headers(staff_token), json={})
    assert ship.status_code == 200
    data = ship.json()
    assert "tracking_number" in data
    assert data["status"] == "picked_up"

    tr = await client.get(f"/api/public/tracking/{data['tracking_number']}")
    assert tr.status_code == 200
    assert tr.json()["status"] == "picked_up"


async def _place_and_get_order_id(client, customer_token, staff_token, seeded_product):
    r = await client.post("/api/customer/checkout", json={
        "items": [{"product_id": seeded_product["id"], "name_snapshot": seeded_product["name"],
                   "sku_snapshot": seeded_product["sku"], "unit_price": seeded_product["base_price"], "quantity": 1}],
        "shipping_address": {"first_name": "T", "last_name": "T", "line1": "1 rue", "city": "Paris",
                             "postal_code": "75001", "country_code": "FR"},
        "card_token": "tok_test",
    }, headers={"Authorization": f"Bearer {customer_token}"})
    assert r.json()["payment_status"] == "succeeded"
    order_number = r.json()["order_number"]
    all_orders = await client.get("/api/admin/orders", headers=auth_headers(staff_token))
    return next(o["id"] for o in all_orders.json() if o["number"] == order_number)


async def test_advance_shipment(client, staff_token, customer_token, seeded_product):
    order_id = await _place_and_get_order_id(client, customer_token, staff_token, seeded_product)
    ship = await client.post(f"/api/admin/orders/{order_id}/ship", headers=auth_headers(staff_token), json={})
    shipment_id = ship.json()["shipment_id"]

    adv = await client.post(f"/api/admin/shipments/{shipment_id}/advance", headers=auth_headers(staff_token), json={})
    assert adv.status_code == 200
    assert adv.json()["status"] == "in_transit"


async def test_cannot_ship_already_shipped_order(client, staff_token, customer_token, seeded_product):
    order_id = await _place_and_get_order_id(client, customer_token, staff_token, seeded_product)
    await client.post(f"/api/admin/orders/{order_id}/ship", headers=auth_headers(staff_token), json={})
    r2 = await client.post(f"/api/admin/orders/{order_id}/ship", headers=auth_headers(staff_token), json={})
    assert r2.status_code == 400


# ---------------------------------------------------------------------------
# Support tickets
# ---------------------------------------------------------------------------

async def test_list_support_tickets_empty(client, staff_token):
    r = await client.get("/api/admin/support/tickets", headers=auth_headers(staff_token))
    assert r.status_code == 200
    assert r.json() == []


# ---------------------------------------------------------------------------
# API keys
# ---------------------------------------------------------------------------

async def test_create_and_list_api_keys(client, staff_token):
    r = await client.post("/api/admin/api-keys", headers=auth_headers(staff_token), json={
        "name": "test-agent",
        "scopes": ["orders.read", "customers.read"],
    })
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "test-agent"
    assert "key" in data
    assert data["key"].startswith("sk_")

    r2 = await client.get("/api/admin/api-keys", headers=auth_headers(staff_token))
    assert r2.status_code == 200
    names = [k["name"] for k in r2.json()]
    assert "test-agent" in names

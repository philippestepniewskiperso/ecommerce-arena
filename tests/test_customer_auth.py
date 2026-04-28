"""Customer auth: signup, login, duplicate email."""
import pytest


async def test_signup(client):
    r = await client.post("/api/customer/auth/signup", json={
        "email": "new@example.com",
        "password": "Password123!",
        "first_name": "New",
        "last_name": "User",
    })
    assert r.status_code == 200
    data = r.json()
    assert "token" in data
    assert "expires_at" in data


async def test_signup_duplicate_email(client, customer_token):
    r = await client.post("/api/customer/auth/signup", json={
        "email": "test.customer@example.com",
        "password": "Password123!",
        "first_name": "Dup",
        "last_name": "User",
    })
    assert r.status_code == 409


async def test_login(client, customer_token):
    r = await client.post("/api/customer/auth/login", json={
        "email": "test.customer@example.com",
        "password": "Password123!",
    })
    assert r.status_code == 200
    assert "token" in r.json()


async def test_login_wrong_password(client, customer_token):
    r = await client.post("/api/customer/auth/login", json={
        "email": "test.customer@example.com",
        "password": "WrongPassword!",
    })
    assert r.status_code == 401


async def test_login_unknown_email(client):
    r = await client.post("/api/customer/auth/login", json={
        "email": "nobody@example.com",
        "password": "Password123!",
    })
    assert r.status_code == 401


async def test_protected_requires_auth(client):
    r = await client.get("/api/customer/orders")
    assert r.status_code == 401


async def test_protected_with_bad_token(client):
    r = await client.get("/api/customer/orders", headers={"Authorization": "Bearer badtoken"})
    assert r.status_code == 401


async def test_protected_with_valid_token(client, customer_token):
    r = await client.get("/api/customer/orders", headers={"Authorization": f"Bearer {customer_token}"})
    assert r.status_code == 200

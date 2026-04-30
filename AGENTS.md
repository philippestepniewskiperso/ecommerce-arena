# Agent Integration Guide

This sandbox exposes four surfaces for AI agents: a REST API, an SSE event stream, outbound webhooks, and a WebSocket chat channel. All agent auth uses API keys (M2M — no browser, no TOTP).

Interactive API docs: **http://localhost:3002/api/docs**

---

## Authentication

All agent endpoints require `Authorization: Bearer <api_key>`.

Two demo keys are printed to stdout when the stack first starts (or when `pnpm seed:dev` runs). Retrieve them from the API container logs:

```bash
docker compose logs api | grep "agent-"
```

| Key name | Scopes |
|---|---|
| `agent-readonly` | `orders.read` `customers.read` `products.read` `support.read` `inventory.read` |
| `agent-ops` | `orders.read/write/cancel/refund` `support.read/write` `inventory.read/write` |

```bash
export API_KEY="sk_..."   # from logs above
export API="http://localhost:3002"
```

---

## REST API

Full OpenAPI spec at `/api/docs`. Key agent-relevant endpoints:

```
GET  /api/public/products          List products (paginated, search ?q=)
GET  /api/public/products/:slug    Product detail + variants

GET  /api/admin/orders             List orders (?status=pending|shipped|…)
GET  /api/admin/orders/:id         Order detail with items + shipping
POST /api/admin/orders/:id/ship    Ship order (creates carrier label)

GET  /api/admin/customers          List customers
GET  /api/admin/customers/:id      Customer profile + order history

GET  /api/admin/support/tickets    List tickets (?status=open|in_progress|…)
GET  /api/admin/support/tickets/:id/messages   Ticket message history

GET  /api/admin/inventory          Current stock levels
PATCH /api/admin/inventory/:sku/adjust   Adjust stock

GET  /api/events                   Last 100 domain events (?event_type=…)
```

---

## SSE Event Stream

Consume all domain events in real time. No auth required.

```bash
curl -N "$API/api/events/stream"
```

```python
import httpx

with httpx.stream("GET", "http://localhost:3002/api/events/stream") as r:
    for line in r.iter_lines():
        if line.startswith("data: "):
            event = json.loads(line[6:])
            print(event["type"], event["aggregate_id"])
```

**Event payload shape:**
```json
{
  "id": "uuid",
  "type": "order.placed",
  "aggregate_type": "order",
  "aggregate_id": "uuid",
  "payload": { ... },
  "created_at": "2026-04-30T10:00:00+00:00"
}
```

**Emitted event types:**

| Event | Trigger |
|---|---|
| `customer.signup` | New customer registers |
| `order.placed` | Customer completes checkout |
| `order.shipped` | Staff marks order shipped |
| `order.delivered` | Carrier delivers (simulation) |
| `payment.succeeded` | Payment captured |
| `payment.failed` | Payment declined |
| `ticket.created` | Customer opens support ticket |
| `shipment.created` | Carrier label generated |
| `shipment.delivered` | Carrier marks delivered |

---

## Webhooks

Register a URL to receive events via HTTP POST. The server retries up to 3 times with 5-minute backoff. Deliveries run every 30 seconds.

### Register

```bash
curl -X POST "$API/api/events/webhooks" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-agent.example.com/hook",
    "events": ["order.placed", "order.shipped", "ticket.created"],
    "secret": "my-webhook-secret"
  }'
```

Subscribe to all events: `"events": ["*"]` is not supported — list each event type explicitly.

### Payload

```json
{
  "event_id": "uuid",
  "type": "order.placed",
  "aggregate_type": "order",
  "aggregate_id": "uuid",
  "payload": { ... },
  "created_at": "2026-04-30T10:00:00+00:00"
}
```

### Verify HMAC signature

Every request includes `X-Webhook-Signature: sha256=<hex>`. Verify with the secret you registered:

```python
import hmac, hashlib

def verify(secret: str, body: bytes, signature_header: str) -> bool:
    expected = "sha256=" + hmac.new(
        secret.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header)
```

### Check delivery history

```bash
curl "$API/api/events/webhooks/{subscription_id}/deliveries" \
  -H "Authorization: Bearer $API_KEY"
```

### Test locally with a receiver

```bash
# Receive webhooks in a terminal (requires Python)
python3 -m http.server 9999

# Or use a public tunnel
npx localtunnel --port 9999
```

---

## WebSocket Chat

Agents can join support ticket chat rooms as staff (with a staff session token, not an API key).

```
ws://localhost:3002/ws/chat/{ticket_id}?token={staff_token}
```

**Message format (send):**
```json
{ "body": "Hello, how can I help?" }
```

**Message format (receive):**
```json
{
  "type": "message",
  "sender_type": "customer",
  "sender_name": "Jean Dupont",
  "body": "My order hasn't arrived",
  "created_at": "2026-04-30T10:00:00+00:00"
}
```

Other received message types: `joined`, `left`.

Get a staff token:
```bash
curl -X POST "$API/api/admin/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"cs@demo.local","password":"demo1234"}'
```

---

## Trigger realistic activity

Use the seed scripts to populate or reset data:

```bash
pnpm seed:dev    # 20 products, 50 customers, 200 orders, 30 tickets (~30s)
pnpm seed:full   # 500 products, 5k customers, 20k orders (~5-10 min)
pnpm reset       # truncate all tables + re-seed:dev
```

"""
Dev seed: staff accounts, 50 customers, 20 products w/ variants + stock,
200 orders (mixed statuses), 30 support tickets, 2 demo API keys.
Run: uv run python scripts/seed/seed_dev.py
"""
import asyncio
import os
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from apps.api.auth.apikey import generate_api_key
from apps.api.auth.password import hash_password
from apps.api.models import (
    Address,
    ApiKey,
    Category,
    Customer,
    Order,
    OrderItem,
    Payment,
    Permission,
    Product,
    ProductVariant,
    Role,
    RolePermission,
    StaffUser,
    StaffUserRole,
    StockLevel,
    SupportTicket,
    TicketMessage,
)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5433/ecommerce")

rng = random.Random(42)

# ---------------------------------------------------------------------------
# Data fixtures
# ---------------------------------------------------------------------------

FIRST_NAMES = [
    "Alice", "Baptiste", "Camille", "David", "Emma",
    "François", "Gabrielle", "Hugo", "Isabelle", "Julien",
    "Karim", "Laura", "Mathieu", "Nathalie", "Olivier",
    "Pauline", "Quentin", "Rachel", "Sébastien", "Théo",
    "Ursula", "Vincent", "Wendy", "Xavier", "Yasmine",
    "Zoé", "Antoine", "Béatrice", "Cédric", "Delphine",
    "Éric", "Fatima", "Guillaume", "Hélène", "Ivan",
    "Jade", "Kevin", "Lucie", "Marc", "Nina",
    "Omar", "Patricia", "Romain", "Sophie", "Thomas",
    "Valérie", "William", "Axelle", "Benjamin", "Charlotte",
]

LAST_NAMES = [
    "Martin", "Bernard", "Thomas", "Petit", "Robert",
    "Richard", "Durand", "Dubois", "Moreau", "Laurent",
    "Simon", "Michel", "Lefebvre", "Leroy", "Roux",
    "David", "Bertrand", "Morel", "Fournier", "Girard",
    "Bonnet", "Dupont", "Lambert", "Fontaine", "Rousseau",
    "Vincent", "Muller", "Lefevre", "Faure", "Andre",
    "Mercier", "Blanc", "Guerin", "Boyer", "Garnier",
    "Chevalier", "François", "Legrand", "Gauthier", "Garcia",
    "Perrin", "Robin", "Clement", "Morin", "Nicolas",
    "Henry", "Roussel", "Mathieu", "Gautier", "Masson",
]

CITIES = [
    ("Paris", "75001", "FR"),
    ("Lyon", "69001", "FR"),
    ("Marseille", "13001", "FR"),
    ("Toulouse", "31000", "FR"),
    ("Nice", "06000", "FR"),
    ("Nantes", "44000", "FR"),
    ("Strasbourg", "67000", "FR"),
    ("Montpellier", "34000", "FR"),
    ("Bordeaux", "33000", "FR"),
    ("Lille", "59000", "FR"),
    ("Berlin", "10115", "DE"),
    ("Munich", "80331", "DE"),
    ("Madrid", "28001", "ES"),
    ("Barcelona", "08001", "ES"),
    ("Milan", "20121", "IT"),
    ("London", "EC1A 1BB", "GB"),
    ("Amsterdam", "1011 AB", "NL"),
]

PRODUCTS_DATA = [
    {
        "name": "Air Velocity Pro",
        "slug": "air-velocity-pro",
        "short_description": "Elite performance running shoe",
        "description": "Engineered for serious runners. Carbon fibre plate, responsive foam stack, and precision-fit upper deliver race-day performance for every training session.",
        "base_price": 189.00,
        "compare_price": 220.00,
        "category_slug": "running",
        "tags": ["performance", "carbon", "marathon"],
        "sizes": ["38", "39", "40", "41", "42", "43", "44", "45"],
    },
    {
        "name": "CloudStride X",
        "slug": "cloudstride-x",
        "short_description": "All-day comfort trainer",
        "description": "Plush cushioning meets lightweight construction. The CloudStride X is built for high-mileage training days when comfort is non-negotiable.",
        "base_price": 145.00,
        "compare_price": None,
        "category_slug": "running",
        "tags": ["training", "comfort", "daily"],
        "sizes": ["38", "39", "40", "41", "42", "43", "44", "45", "46"],
    },
    {
        "name": "Pace Elite 3",
        "slug": "pace-elite-3",
        "short_description": "Tempo run specialist",
        "description": "Stiff propulsion plate and dual-density foam for efficient energy return. The go-to for tempo sessions and race simulations.",
        "base_price": 165.00,
        "compare_price": 180.00,
        "category_slug": "running",
        "tags": ["tempo", "race", "performance"],
        "sizes": ["39", "40", "41", "42", "43", "44", "45"],
    },
    {
        "name": "Court Storm X",
        "slug": "court-storm-x",
        "short_description": "Dominate the hardwood",
        "description": "Low-profile stability, lateral lockdown, and herringbone outsole optimised for hardwood courts. Worn by pros, built for anyone who plays hard.",
        "base_price": 159.00,
        "compare_price": None,
        "category_slug": "basketball",
        "tags": ["basketball", "court", "low-top"],
        "sizes": ["40", "41", "42", "43", "44", "45", "46", "47"],
    },
    {
        "name": "Rise High GT",
        "slug": "rise-high-gt",
        "short_description": "High-top ankle support",
        "description": "Full ankle collar for maximum support on the drive. Cushioned midsole absorbs landing impact. Built for power forwards who attack the rim.",
        "base_price": 175.00,
        "compare_price": 200.00,
        "category_slug": "basketball",
        "tags": ["basketball", "high-top", "ankle-support"],
        "sizes": ["41", "42", "43", "44", "45", "46"],
    },
    {
        "name": "Urban Stride",
        "slug": "urban-stride",
        "short_description": "Street-ready everyday sneaker",
        "description": "Clean silhouette, premium leather upper, and memory foam insole. Transitions effortlessly from morning commute to evening dinner.",
        "base_price": 119.00,
        "compare_price": None,
        "category_slug": "casual",
        "tags": ["casual", "leather", "everyday"],
        "sizes": ["38", "39", "40", "41", "42", "43", "44", "45"],
    },
    {
        "name": "Canvas Classic",
        "slug": "canvas-classic",
        "short_description": "Timeless canvas sneaker",
        "description": "Vulcanised rubber sole, 100% cotton canvas upper. A wardrobe staple that pairs with everything. Available in 6 colourways.",
        "base_price": 69.00,
        "compare_price": None,
        "category_slug": "casual",
        "tags": ["casual", "canvas", "classic"],
        "sizes": ["36", "37", "38", "39", "40", "41", "42", "43", "44", "45"],
    },
    {
        "name": "Luxe Suede Low",
        "slug": "luxe-suede-low",
        "short_description": "Premium suede loafer-sneaker hybrid",
        "description": "Italian suede upper, hand-stitched detailing, and crepe rubber sole. The intersection of sneaker culture and luxury footwear.",
        "base_price": 249.00,
        "compare_price": 280.00,
        "category_slug": "casual",
        "tags": ["premium", "suede", "luxury"],
        "sizes": ["39", "40", "41", "42", "43", "44"],
    },
    {
        "name": "Phantom Street",
        "slug": "phantom-street",
        "short_description": "Bold streetwear statement",
        "description": "Exaggerated sole unit, oversized tongue, and reflective panelling. Turn heads on every block — whether you're skating, walking, or just standing.",
        "base_price": 139.00,
        "compare_price": None,
        "category_slug": "streetwear",
        "tags": ["streetwear", "chunky", "bold"],
        "sizes": ["39", "40", "41", "42", "43", "44", "45"],
    },
    {
        "name": "Retro Wave 90",
        "slug": "retro-wave-90",
        "short_description": "90s basketball silhouette reborn",
        "description": "Vintage basketball proportions, updated with modern materials. Full-grain leather, translucent outsole, and OG colourways faithful to the original.",
        "base_price": 155.00,
        "compare_price": 170.00,
        "category_slug": "streetwear",
        "tags": ["retro", "streetwear", "heritage"],
        "sizes": ["38", "39", "40", "41", "42", "43", "44", "45"],
    },
    {
        "name": "Drift Runner",
        "slug": "drift-runner",
        "short_description": "Technical outdoor runner",
        "description": "Trail-inspired lugs, waterproof TPU overlay, and stretch-woven upper. Wears as well in the city as on gravel paths.",
        "base_price": 129.00,
        "compare_price": None,
        "category_slug": "streetwear",
        "tags": ["outdoor", "technical", "waterproof"],
        "sizes": ["39", "40", "41", "42", "43", "44", "45"],
    },
    {
        "name": "Micro Boost Z",
        "slug": "micro-boost-z",
        "short_description": "Ultra-light speed trainer",
        "description": "Featherweight knit upper and nitrogen-infused foam. At 185g per shoe, the Micro Boost Z disappears on your foot — all you feel is the road.",
        "base_price": 199.00,
        "compare_price": 230.00,
        "category_slug": "running",
        "tags": ["lightweight", "knit", "speed"],
        "sizes": ["38", "39", "40", "41", "42", "43", "44", "45"],
    },
    {
        "name": "Trail Blazer Pro",
        "slug": "trail-blazer-pro",
        "short_description": "Off-road performance trail shoe",
        "description": "Aggressive multi-directional lugs, rock plate, and Vibram outsole. Built for technical singletrack and mountain ultras.",
        "base_price": 179.00,
        "compare_price": None,
        "category_slug": "running",
        "tags": ["trail", "off-road", "vibram"],
        "sizes": ["39", "40", "41", "42", "43", "44", "45"],
    },
    {
        "name": "React Cushion 5",
        "slug": "react-cushion-5",
        "short_description": "Max cushion recovery shoe",
        "description": "Thick stack of zoned foam for post-run recovery or easy miles. The React Cushion 5 is for days when your legs need a break.",
        "base_price": 135.00,
        "compare_price": 150.00,
        "category_slug": "running",
        "tags": ["cushion", "recovery", "easy"],
        "sizes": ["38", "39", "40", "41", "42", "43", "44", "45", "46"],
    },
    {
        "name": "Force Low GTX",
        "slug": "force-low-gtx",
        "short_description": "Waterproof basketball sneaker",
        "description": "Gore-Tex inner bootie keeps feet dry in any weather. Court-tested traction and full-length cushioning for outdoor play.",
        "base_price": 195.00,
        "compare_price": None,
        "category_slug": "basketball",
        "tags": ["waterproof", "gore-tex", "outdoor"],
        "sizes": ["40", "41", "42", "43", "44", "45", "46"],
    },
    {
        "name": "Slide Pro Recovery",
        "slug": "slide-pro-recovery",
        "short_description": "Post-workout recovery sandal",
        "description": "Contoured footbed with arch support and pressure point cushioning. The essential post-training companion for serious athletes.",
        "base_price": 55.00,
        "compare_price": None,
        "category_slug": "casual",
        "tags": ["slides", "recovery", "sport"],
        "sizes": ["38", "39", "40", "41", "42", "43", "44", "45"],
    },
    {
        "name": "Neon Grid 2",
        "slug": "neon-grid-2",
        "short_description": "Eye-catching mesh runner",
        "description": "Engineered mesh upper in bold neon colourways, flexible outsole, and responsive foam midsole. Fast looks, fast feel.",
        "base_price": 109.00,
        "compare_price": 125.00,
        "category_slug": "running",
        "tags": ["neon", "mesh", "training"],
        "sizes": ["38", "39", "40", "41", "42", "43", "44"],
    },
    {
        "name": "Heritage Hiker Low",
        "slug": "heritage-hiker-low",
        "short_description": "Urban hiking boot silhouette",
        "description": "Nubuck leather and ballistic nylon upper, cushioned EVA midsole, rubber lug outsole. Hiking heritage meets street credibility.",
        "base_price": 169.00,
        "compare_price": None,
        "category_slug": "streetwear",
        "tags": ["hiking", "nubuck", "boot"],
        "sizes": ["39", "40", "41", "42", "43", "44", "45"],
    },
    {
        "name": "Stealth Runner",
        "slug": "stealth-runner",
        "short_description": "All-black performance trainer",
        "description": "Full monochrome aesthetic — black on black on black. High-rebound foam, seamless upper, and matte outsole. Serious training, serious looks.",
        "base_price": 149.00,
        "compare_price": 165.00,
        "category_slug": "running",
        "tags": ["black", "monochrome", "training"],
        "sizes": ["38", "39", "40", "41", "42", "43", "44", "45"],
    },
    {
        "name": "Plush Walk Mule",
        "slug": "plush-walk-mule",
        "short_description": "Cozy slip-on sneaker mule",
        "description": "Shearling-lined collar, memory foam insole, and flexible rubber sole. Slips on in seconds, comfortable all day.",
        "base_price": 89.00,
        "compare_price": None,
        "category_slug": "casual",
        "tags": ["mule", "slip-on", "cozy"],
        "sizes": ["36", "37", "38", "39", "40", "41", "42", "43"],
    },
]

TICKET_SUBJECTS = [
    ("Where is my order?", "I placed an order 5 days ago but have not received any shipping confirmation. Order number: {order_number}.", "open", "medium"),
    ("Wrong size delivered", "I ordered size 42 but received size 40. Please help me exchange.", "open", "high"),
    ("Shoe defect after 2 weeks", "The sole of my shoes started peeling after only 2 weeks of use. Totally unacceptable for this price point.", "open", "high"),
    ("Return request", "I'd like to return my purchase. The shoes don't fit as expected. How do I proceed?", "in_progress", "medium"),
    ("Refund not received", "My return was approved 10 days ago but I still haven't received the refund on my card.", "open", "urgent"),
    ("Discount code not working", "The code KICKS20 is not being accepted at checkout. It says it expired but the email I received says it's valid until next month.", "in_progress", "low"),
    ("Order cancelled without reason", "My order was cancelled without any explanation. I want to know why and get a refund immediately.", "open", "high"),
    ("Sizing question before purchase", "Before I order, can you tell me if the Air Velocity Pro runs true to size or should I size up?", "resolved", "low"),
    ("Damaged packaging", "The box arrived completely crushed. The shoes seem ok but I'm not sure. Should I return them?", "resolved", "medium"),
    ("Invoice needed for business", "I need a proper VAT invoice for my last order for business expense purposes. How do I get one?", "open", "low"),
    ("Tracking link broken", "The tracking link in my shipping email gives a 404 error. Can you provide a working one?", "in_progress", "medium"),
    ("Loyalty points missing", "I've made 3 purchases but don't see any loyalty points in my account. Am I enrolled in the programme?", "open", "low"),
    ("Product arrived dirty", "The shoes I received look like they've been tried on in a store. There's dirt on the sole and the laces are untied.", "open", "high"),
    ("Wrong item in package", "I ordered the Urban Stride in black but received the Canvas Classic in white. Please send the correct item.", "in_progress", "high"),
    ("Shipping to PO box", "Can I have my order shipped to a PO box? The checkout doesn't seem to accept it.", "resolved", "low"),
    ("Payment declined but charged", "My payment was declined at checkout but I can see a pending charge on my bank account. Please clarify.", "open", "urgent"),
    ("Gift wrapping option", "Do you offer gift wrapping? I'm ordering as a birthday present.", "resolved", "low"),
    ("Stock notification request", "The Phantom Street in size 43 is out of stock. Can you notify me when it's back?", "resolved", "low"),
    ("Colourway not as pictured", "The colour of the shoes I received is significantly different from the website photos. The product page shows bright orange but these are more of a rust/brown.", "open", "medium"),
    ("Exchange for different model", "I bought the CloudStride X but it's not cushioned enough for me. Can I exchange for the React Cushion 5?", "in_progress", "medium"),
    ("Laces broke first day", "The laces on my Canvas Classic snapped on the very first day. Can you send replacement laces?", "resolved", "low"),
    ("Account password reset issue", "I'm not receiving the password reset email. I've checked spam. My account email is correct.", "in_progress", "medium"),
    ("Delivery to neighbour", "My package was delivered to a neighbour according to tracking but I haven't been able to retrieve it. What do I do?", "open", "high"),
    ("Size chart accuracy", "Your size chart says I should order a 41 based on my measurements but the shoes are too small. The chart needs updating.", "resolved", "low"),
    ("Multiple orders merge", "I placed two orders 10 minutes apart. Can they be combined into one shipment to save packaging?", "resolved", "low"),
    ("Return label never arrived", "I requested a return 5 days ago but never received the prepaid label by email.", "open", "medium"),
    ("Worn shoes return policy", "I wore the shoes twice before realising they're not right for me. Can I still return them?", "in_progress", "medium"),
    ("Bank dispute query", "My bank has opened a dispute for this charge. Can your team contact my bank to resolve this?", "open", "urgent"),
    ("Delivery instructions ignored", "I left specific delivery instructions to leave the package at the back door but the courier attempted delivery to the front.", "resolved", "low"),
    ("Subscription box enquiry", "Do you have any subscription or monthly shoe box service? I'd be interested in signing up.", "resolved", "low"),
]

ORDER_STATUSES_WEIGHTED = [
    ("pending", 5),
    ("confirmed", 10),
    ("shipped", 30),
    ("delivered", 40),
    ("cancelled", 10),
    ("refunded", 5),
]


def weighted_choice(weighted_list):
    items = [item for item, w in weighted_list for _ in range(w)]
    return rng.choice(items)


def random_past_datetime(days_min=1, days_max=180):
    delta = timedelta(days=rng.randint(days_min, days_max), hours=rng.randint(0, 23), minutes=rng.randint(0, 59))
    return datetime.now(timezone.utc) - delta


# ---------------------------------------------------------------------------
# Seeding functions
# ---------------------------------------------------------------------------

async def clear_tables(session: AsyncSession):
    for table in [
        "ticket_messages", "support_tickets", "campaign_recipients", "campaigns",
        "audit_logs", "domain_events", "webhook_deliveries", "webhook_subscriptions",
        "tracking_events", "shipments", "payments", "return_items", "return_requests",
        "order_items", "orders", "stock_movements", "stock_levels", "product_images",
        "product_variants", "reviews", "products", "categories",
        "role_permissions", "staff_user_roles", "api_keys", "sessions",
        "addresses", "customers", "staff_users", "roles", "permissions",
        "banners", "pages", "seed_meta",
    ]:
        await session.execute(text(f'TRUNCATE TABLE "{table}" CASCADE'))
    await session.commit()
    print("  tables cleared")


async def seed_roles_permissions(session: AsyncSession):
    perms_data = [
        ("products.read", "Read product catalog"),
        ("products.write", "Create/update products"),
        ("products.delete", "Delete products"),
        ("orders.read", "View orders"),
        ("orders.write", "Update order status"),
        ("orders.refund", "Issue refunds"),
        ("orders.cancel", "Cancel orders"),
        ("customers.read", "View customer data"),
        ("customers.write", "Edit customer data"),
        ("support.read", "View support tickets"),
        ("support.write", "Reply to / resolve tickets"),
        ("support.assign", "Assign tickets to agents"),
        ("inventory.read", "View stock levels"),
        ("inventory.write", "Adjust stock"),
        ("marketing.read", "View campaigns"),
        ("marketing.write", "Create/send campaigns"),
        ("finance.read", "View payments and revenue"),
        ("finance.write", "Issue refunds, manage payouts"),
        ("cms.read", "View pages and banners"),
        ("cms.write", "Edit pages and banners"),
        ("staff.read", "View staff accounts"),
        ("staff.write", "Create/edit staff accounts"),
        ("api_keys.read", "View API keys"),
        ("api_keys.write", "Create/revoke API keys"),
        ("audit.read", "View audit logs"),
    ]

    perms = {}
    for name, desc in perms_data:
        p = Permission(id=uuid.uuid4(), name=name, description=desc)
        session.add(p)
        perms[name] = p

    roles_data = {
        "admin": list(perms.keys()),
        "ops_manager": [
            "products.read", "products.write",
            "orders.read", "orders.write", "orders.cancel",
            "inventory.read", "inventory.write",
            "customers.read",
            "support.read",
            "finance.read",
        ],
        "cs_agent": [
            "orders.read", "orders.write",
            "customers.read",
            "support.read", "support.write",
        ],
        "marketer": [
            "products.read",
            "customers.read",
            "marketing.read", "marketing.write",
            "cms.read", "cms.write",
        ],
        "finance": [
            "orders.read",
            "finance.read", "finance.write",
            "orders.refund",
        ],
    }

    roles = {}
    for role_name, perm_names in roles_data.items():
        r = Role(id=uuid.uuid4(), name=role_name, description=f"{role_name.replace('_', ' ').title()} role")
        session.add(r)
        roles[role_name] = r
        for pname in perm_names:
            session.add(RolePermission(role_id=r.id, permission_id=perms[pname].id))

    await session.flush()
    print("  roles + permissions seeded")
    return roles


async def seed_staff(session: AsyncSession, roles: dict):
    staff_data = [
        ("admin@demo.local", "demo1234", "Admin", "User", "admin"),
        ("ops@demo.local", "demo1234", "Ops", "Manager", "ops_manager"),
        ("cs@demo.local", "demo1234", "CS", "Agent", "cs_agent"),
    ]

    staff_users = []
    for email, password, first, last, role_name in staff_data:
        s = StaffUser(
            id=uuid.uuid4(),
            email=email,
            password_hash=hash_password(password),
            first_name=first,
            last_name=last,
            status="active",
        )
        session.add(s)
        session.add(StaffUserRole(staff_user_id=s.id, role_id=roles[role_name].id))
        staff_users.append(s)

    await session.flush()
    print("  staff users seeded")
    return staff_users


async def seed_api_keys(session: AsyncSession):
    keys_config = [
        ("agent-readonly", ["orders.read", "customers.read", "products.read", "support.read", "inventory.read"]),
        ("agent-ops", ["orders.read", "orders.write", "orders.cancel", "orders.refund", "support.read", "support.write", "inventory.read", "inventory.write"]),
    ]

    printed_keys = []
    for name, scopes in keys_config:
        key, key_hash = generate_api_key()
        ak = ApiKey(id=uuid.uuid4(), name=name, key_hash=key_hash, scopes=scopes)
        session.add(ak)
        printed_keys.append((name, key))

    await session.flush()
    print("  API keys seeded")
    return printed_keys


async def seed_categories(session: AsyncSession):
    cats_data = [
        ("Running", "running", "Performance running shoes for every distance", 0),
        ("Basketball", "basketball", "Court shoes built for speed and stability", 1),
        ("Casual", "casual", "Everyday sneakers for the urban explorer", 2),
        ("Streetwear", "streetwear", "Bold silhouettes for street culture", 3),
    ]
    cats = {}
    for name, slug, desc, pos in cats_data:
        c = Category(id=uuid.uuid4(), name=name, slug=slug, description=desc, position=pos)
        session.add(c)
        cats[slug] = c
    await session.flush()
    print("  categories seeded")
    return cats


async def seed_products(session: AsyncSession, cats: dict):
    products = []
    for p_data in PRODUCTS_DATA:
        cat = cats[p_data["category_slug"]]
        p = Product(
            id=uuid.uuid4(),
            category_id=cat.id,
            name=p_data["name"],
            slug=p_data["slug"],
            short_description=p_data["short_description"],
            description=p_data["description"],
            base_price=p_data["base_price"],
            compare_price=p_data.get("compare_price"),
            status="active",
            tags=p_data["tags"],
        )
        session.add(p)

        for size in p_data["sizes"]:
            sku = f"{p_data['slug'].upper().replace('-', '_')}_EU{size}"
            v = ProductVariant(
                id=uuid.uuid4(),
                product_id=p.id,
                sku=sku,
                name=f"EU {size}",
                attributes={"size": size},
                is_default=(size == p_data["sizes"][len(p_data["sizes"]) // 2]),
            )
            session.add(v)

            qty = rng.randint(0, 80)
            sl = StockLevel(
                id=uuid.uuid4(),
                variant_id=v.id,
                warehouse="main",
                quantity=qty,
                reserved_quantity=rng.randint(0, min(5, qty)),
                low_stock_threshold=5,
            )
            session.add(sl)

        products.append(p)

    await session.flush()
    print(f"  {len(products)} products + variants + stock seeded")
    return products


async def seed_customers(session: AsyncSession, count=50):
    customers = []

    def normalize(s):
        replacements = {"é": "e", "è": "e", "ê": "e", "ë": "e", "ç": "c",
                        "ô": "o", "î": "i", "â": "a", "û": "u", "à": "a",
                        "ù": "u", "ï": "i", "É": "e", "È": "e", "Ê": "e"}
        for k, v in replacements.items():
            s = s.replace(k, v)
        return s.lower()

    for i in range(count):
        first = FIRST_NAMES[i % len(FIRST_NAMES)]
        last = LAST_NAMES[(i * 3 + 7) % len(LAST_NAMES)]
        email = f"{normalize(first)}.{normalize(last)}{i}@example.com"

        c = Customer(
            id=uuid.uuid4(),
            email=email,
            password_hash=hash_password("password123"),
            first_name=first,
            last_name=last,
            status="active",
            email_verified_at=datetime.now(timezone.utc),
            created_at=random_past_datetime(30, 365),
        )
        session.add(c)
        customers.append(c)

    await session.flush()
    print(f"  {len(customers)} customers seeded")
    return customers


async def seed_orders(session: AsyncSession, customers: list, products: list, count=200):
    variant_rows = await session.execute(
        text("SELECT id, product_id, sku, name, price_override FROM product_variants")
    )
    all_variants = variant_rows.fetchall()

    variants_by_product = {}
    for row in all_variants:
        pid = str(row[1])
        variants_by_product.setdefault(pid, []).append(row)

    price_by_product = {str(p.id): float(p.base_price) for p in products}

    orders = []
    order_counter = 1

    for _ in range(count):
        customer = rng.choice(customers)
        status = weighted_choice(ORDER_STATUSES_WEIGHTED)
        placed_at = random_past_datetime(1, 150)

        city_data = rng.choice(CITIES)
        addr = Address(
            id=uuid.uuid4(),
            customer_id=customer.id,
            first_name=customer.first_name,
            last_name=customer.last_name,
            line1=f"{rng.randint(1, 200)} rue {rng.choice(['de la Paix', 'du Faubourg', 'de Rivoli', 'Saint-Michel', 'de la République'])}",
            city=city_data[0],
            postal_code=city_data[1],
            country_code=city_data[2],
        )
        session.add(addr)

        order_products = rng.sample(products, k=rng.randint(1, 3))
        item_rows = []
        subtotal = 0.0

        for prod in order_products:
            pid = str(prod.id)
            variants = variants_by_product.get(pid, [])
            if not variants:
                continue
            variant = rng.choice(variants)
            qty = rng.randint(1, 3)
            unit_price = float(variant[4]) if variant[4] else price_by_product[pid]
            total_price = round(unit_price * qty, 2)
            subtotal += total_price
            item_rows.append((variant, qty, unit_price, total_price, prod))

        subtotal = round(subtotal, 2)
        shipping = 0.0 if subtotal >= 100 else 5.99
        tax = round(subtotal * 0.20, 2)
        total = round(subtotal + shipping + tax, 2)

        order_number = f"ORD-{placed_at.year}-{order_counter:05d}"
        order_counter += 1

        order = Order(
            id=uuid.uuid4(),
            number=order_number,
            customer_id=customer.id,
            shipping_address_id=addr.id,
            status=status,
            subtotal=subtotal,
            shipping_amount=shipping,
            tax_amount=tax,
            total=total,
            currency="EUR",
            placed_at=placed_at,
        )
        session.add(order)

        for variant, qty, unit_price, total_price, prod in item_rows:
            session.add(OrderItem(
                id=uuid.uuid4(),
                order_id=order.id,
                variant_id=variant[0],
                product_id=prod.id,
                sku_snapshot=variant[2],
                name_snapshot=prod.name,
                variant_name_snapshot=variant[3],
                unit_price=unit_price,
                quantity=qty,
                total_price=total_price,
            ))

        if status != "cancelled":
            pay_status = "succeeded" if status != "refunded" else "refunded"
            session.add(Payment(
                id=uuid.uuid4(),
                order_id=order.id,
                amount=total,
                currency="EUR",
                status=pay_status,
                provider="mock",
                provider_ref=f"txn_{uuid.uuid4().hex[:16]}",
                created_at=placed_at,
            ))

        orders.append(order)

    await session.flush()
    print(f"  {len(orders)} orders seeded")
    return orders


async def seed_tickets(session: AsyncSession, customers: list, orders: list, staff_users: list, count=30):
    cs_agents = [s for s in staff_users if "cs" in s.email or "admin" in s.email]
    ticket_counter = 1

    for i in range(min(count, len(TICKET_SUBJECTS))):
        subject_template, body_template, status, priority = TICKET_SUBJECTS[i]

        customer = rng.choice(customers)
        order = rng.choice(orders) if rng.random() > 0.3 else None

        order_number = order.number if order else "N/A"
        body = body_template.replace("{order_number}", order_number)

        ticket = SupportTicket(
            id=uuid.uuid4(),
            number=f"TKT-{ticket_counter:05d}",
            customer_id=customer.id,
            order_id=order.id if order else None,
            subject=subject_template,
            status=status,
            priority=priority,
            assigned_to_id=rng.choice(cs_agents).id if status in ("in_progress", "resolved") else None,
            created_at=random_past_datetime(1, 60),
            resolved_at=random_past_datetime(1, 30) if status == "resolved" else None,
        )
        session.add(ticket)
        ticket_counter += 1

        session.add(TicketMessage(
            id=uuid.uuid4(),
            ticket_id=ticket.id,
            author_type="customer",
            author_id=customer.id,
            body=body,
            is_internal=False,
            created_at=ticket.created_at,
        ))

        if status in ("in_progress", "resolved") and cs_agents:
            agent = rng.choice(cs_agents)
            replies = [
                "Thank you for contacting us. I'm looking into this right now and will update you shortly.",
                "I've reviewed your order and I'm escalating this to our warehouse team. You'll hear back within 24 hours.",
                "I can confirm we've initiated the return process. Please expect the prepaid label within 1-2 business days.",
                "I've flagged this to our quality team. We'll send a replacement immediately at no charge.",
                "Your refund has been processed and should appear on your statement within 3-5 business days.",
            ]
            session.add(TicketMessage(
                id=uuid.uuid4(),
                ticket_id=ticket.id,
                author_type="staff",
                author_id=agent.id,
                body=rng.choice(replies),
                is_internal=False,
                created_at=ticket.created_at + timedelta(hours=rng.randint(1, 8)),
            ))

    await session.flush()
    print(f"  {count} support tickets seeded")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main():
    print("seed:dev starting...")
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        print("clearing tables...")
        await clear_tables(session)

        print("seeding...")
        roles = await seed_roles_permissions(session)
        staff_users = await seed_staff(session, roles)
        printed_keys = await seed_api_keys(session)
        cats = await seed_categories(session)
        products = await seed_products(session, cats)
        customers = await seed_customers(session, count=50)
        await session.commit()

        orders = await seed_orders(session, customers, products, count=200)
        await session.commit()

        await seed_tickets(session, customers, orders, staff_users, count=30)
        await session.commit()

    print()
    print("seed:dev complete.")
    print()
    print("Demo staff accounts:")
    print("  admin@demo.local  / demo1234  (admin)")
    print("  ops@demo.local    / demo1234  (ops_manager)")
    print("  cs@demo.local     / demo1234  (cs_agent)")
    print()
    print("Demo API keys (save these — shown once):")
    for name, key in printed_keys:
        print(f"  {name}: {key}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())

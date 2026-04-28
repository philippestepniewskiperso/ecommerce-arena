"""
Mock carrier: generates tracking numbers and simulates state transitions.
State machine: pending → picked_up → in_transit → out_for_delivery → delivered
Failure path: any state → failed (rare, ~5%)
"""
import random
import secrets
import string
from datetime import datetime, timedelta, timezone


CARRIER_PREFIXES = {
    "colissimo": "6C",
    "chronopost": "CP",
    "mock": "MK",
}

TRACKING_STATES = [
    "pending",
    "picked_up",
    "in_transit",
    "out_for_delivery",
    "delivered",
]

STATE_DESCRIPTIONS = {
    "pending": "Label created — parcel awaiting collection",
    "picked_up": "Parcel collected from sender",
    "in_transit": "Parcel in transit at sorting facility",
    "out_for_delivery": "Parcel out for delivery — expected today",
    "delivered": "Parcel delivered successfully",
    "failed": "Delivery attempt failed — card left",
    "returned": "Parcel returned to sender",
}

STATE_LOCATIONS = {
    "pending": "Sender",
    "picked_up": "Roissy CDG Hub",
    "in_transit": "Lyon Sorting Centre",
    "out_for_delivery": "Local Delivery Depot",
    "delivered": "Recipient address",
    "failed": "Local Delivery Depot",
    "returned": "Return Hub",
}

CARRIERS = ["colissimo", "chronopost", "mock"]


def generate_tracking_number(carrier: str = "mock") -> str:
    prefix = CARRIER_PREFIXES.get(carrier, "MK")
    digits = "".join(random.choices(string.digits, k=11))
    suffix = "FR"
    return f"{prefix}{digits}{suffix}"


def estimated_delivery_date(days: int = 3) -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=days)


def next_state(current: str) -> str | None:
    """Return next state in the state machine. None if already terminal."""
    try:
        idx = TRACKING_STATES.index(current)
    except ValueError:
        return None
    if idx >= len(TRACKING_STATES) - 1:
        return None
    return TRACKING_STATES[idx + 1]


def create_label(order_number: str, carrier: str = "mock") -> dict:
    """Simulate label creation. Returns label metadata."""
    tracking_number = generate_tracking_number(carrier)
    return {
        "tracking_number": tracking_number,
        "carrier": carrier,
        "label_url": f"/mock-labels/{tracking_number}.pdf",
        "estimated_delivery": estimated_delivery_date(days=random.randint(2, 5)),
    }


def advance_tracking(current_status: str, force_fail: bool = False) -> dict:
    """Return next tracking event data."""
    if force_fail or (random.random() < 0.04 and current_status == "out_for_delivery"):
        new_status = "failed"
    else:
        new_status = next_state(current_status)
        if new_status is None:
            return {"status": current_status, "advanced": False}

    return {
        "status": new_status,
        "description": STATE_DESCRIPTIONS.get(new_status, new_status),
        "location": STATE_LOCATIONS.get(new_status, "Unknown"),
        "occurred_at": datetime.now(timezone.utc),
        "advanced": True,
    }

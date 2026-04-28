"""Payment mock — simulates a payment processor locally."""
import random
import uuid
from datetime import datetime


def charge(amount: float, currency: str = "EUR", card_token: str = "tok_test") -> dict:
    """
    Simulate a card charge.
    Returns success 95% of the time; declines 5% to exercise error paths.
    """
    transaction_id = f"mock_txn_{uuid.uuid4().hex[:16]}"

    if card_token == "tok_decline":
        return {
            "success": False,
            "transaction_id": transaction_id,
            "amount": amount,
            "currency": currency,
            "error": "card_declined",
            "error_message": "Your card was declined.",
            "charged_at": datetime.utcnow().isoformat(),
        }

    if random.random() < 0.05:
        return {
            "success": False,
            "transaction_id": transaction_id,
            "amount": amount,
            "currency": currency,
            "error": "insufficient_funds",
            "error_message": "Insufficient funds.",
            "charged_at": datetime.utcnow().isoformat(),
        }

    return {
        "success": True,
        "transaction_id": transaction_id,
        "amount": amount,
        "currency": currency,
        "error": None,
        "error_message": None,
        "charged_at": datetime.utcnow().isoformat(),
    }


def refund(transaction_id: str, amount: float, currency: str = "EUR") -> dict:
    """Simulate a refund."""
    return {
        "success": True,
        "refund_id": f"mock_ref_{uuid.uuid4().hex[:16]}",
        "original_transaction_id": transaction_id,
        "amount": amount,
        "currency": currency,
        "refunded_at": datetime.utcnow().isoformat(),
    }

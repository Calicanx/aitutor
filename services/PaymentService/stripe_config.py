"""
Stripe Configuration for Payment Processing
"""

import stripe
import os

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
stripe_webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

# Payment options (same as pricing page)
PAYMENT_OPTIONS = {
    "starter": {
        "price_id": "price_starter",  # Get from Stripe dashboard
        "credits": 100,
        "amount_cents": 999  # $9.99
    },
    "pro": {
        "price_id": "price_pro",
        "credits": 250,
        "amount_cents": 1999  # $19.99
    },
    "premium": {
        "price_id": "price_premium",
        "credits": 600,
        "amount_cents": 3999  # $39.99
    }
}

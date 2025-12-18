"""
Stripe Payment Handler - Handles payment processing and webhooks
"""

import stripe
import os
from datetime import datetime
from managers.mongodb_manager import mongo_db
from services.PaymentService.stripe_config import PAYMENT_OPTIONS
from shared.logging_config import get_logger

logger = get_logger(__name__)


class StripePaymentHandler:
    """Handle Stripe payment operations"""

    @staticmethod
    def create_checkout_session(user_id: str, plan: str):
        """Create Stripe checkout session"""

        if plan not in PAYMENT_OPTIONS:
            raise ValueError(f"Invalid plan: {plan}")

        plan_details = PAYMENT_OPTIONS[plan]

        # Get frontend URL from environment
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price": plan_details["price_id"],
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url=f"{frontend_url}/app/payment/success",
            cancel_url=f"{frontend_url}/app/payment/cancel",
            client_reference_id=user_id,
            metadata={
                "user_id": user_id,
                "plan": plan,
                "credits": plan_details["credits"]
            }
        )

        logger.info(f"[STRIPE] Created checkout session for user {user_id}, plan {plan}")
        return session

    @staticmethod
    def handle_payment_success(event: dict):
        """Handle successful payment webhook"""

        session = event["data"]["object"]
        user_id = session.get("client_reference_id")
        plan = session.get("metadata", {}).get("plan")
        credits = int(session.get("metadata", {}).get("credits", 0))

        logger.info(f"[STRIPE] Processing successful payment for user {user_id}")

        # Update user credits in MongoDB
        mongo_db.users.update_one(
            {"user_id": user_id},
            {
                "$inc": {"credits.balance": credits},
                "$push": {
                    "payment_history": {
                        "payment_id": session.get("payment_intent"),
                        "plan": plan,
                        "credits": credits,
                        "amount": session.get("amount_total") / 100,
                        "status": "completed",
                        "timestamp": datetime.utcnow()
                    }
                }
            }
        )

        # Log payment to payments collection
        mongo_db.payments.insert_one({
            "user_id": user_id,
            "payment_id": session.get("payment_intent"),
            "plan": plan,
            "credits": credits,
            "amount": session.get("amount_total") / 100,
            "status": "completed",
            "timestamp": datetime.utcnow(),
            "stripe_session_id": session.get("id")
        })

        logger.info(f"[STRIPE] Updated credits for user {user_id}: +{credits} credits")

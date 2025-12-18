"""
Payment API Endpoints
"""

import os
import stripe
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from managers.mongodb_manager import mongo_db
from shared.auth_middleware import get_current_user
from services.PaymentService.stripe_handler import StripePaymentHandler
from shared.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/payment", tags=["payment"])


class CheckoutSessionRequest(BaseModel):
    plan: str


@router.post("/create-checkout-session")
async def create_checkout_session(request: Request, body: CheckoutSessionRequest):
    """Create Stripe checkout session"""

    user_id = get_current_user(request)
    plan = body.plan

    try:
        session = StripePaymentHandler.create_checkout_session(
            user_id=user_id,
            plan=plan
        )

        return {
            "checkout_url": session.url,
            "session_id": session.id
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[PAYMENT] Error creating checkout session: {e}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")


@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events"""

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    stripe_webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            stripe_webhook_secret
        )
    except ValueError:
        logger.error("[STRIPE] Invalid payload")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        logger.error("[STRIPE] Invalid signature")
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle events
    if event["type"] == "checkout.session.completed":
        StripePaymentHandler.handle_payment_success(event)

    return {"status": "success"}


@router.get("/success")
async def payment_success():
    """Payment success redirect page"""
    return {"message": "Payment successful! Your credits have been added."}


@router.get("/cancel")
async def payment_cancel():
    """Payment cancelled redirect page"""
    return {"message": "Payment cancelled."}

import stripe
from app.core.config import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

PLANS = {
    "free": {
        "nombre": "Free",
        "precio_mxn": 0,
        "queries": 50,
        "clientes": 5,
        "stripe_price_id": None,
    },
    "pro": {
        "nombre": "Pro",
        "precio_mxn": 499,
        "queries": 1000,
        "clientes": 50,
        "stripe_price_id": settings.STRIPE_PRICE_PRO,
    },
    "agencia": {
        "nombre": "Agencia",
        "precio_mxn": 999,
        "queries": -1,
        "clientes": -1,
        "stripe_price_id": settings.STRIPE_PRICE_AGENCIA,
    },
}


def create_checkout_session(
    plan: str,
    user_email: str,
    user_id: int,
    success_url: str,
    cancel_url: str,
) -> str:
    price_id = PLANS[plan]["stripe_price_id"]
    if not price_id:
        raise ValueError(f"Plan '{plan}' no tiene precio Stripe configurado")

    session = stripe.checkout.Session.create(
        mode="subscription",
        payment_method_types=["card"],
        customer_email=user_email,
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"user_id": str(user_id), "plan": plan},
        subscription_data={"metadata": {"user_id": str(user_id), "plan": plan}},
    )
    return session.url


def create_portal_session(customer_id: str, return_url: str) -> str:
    session = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=return_url,
    )
    return session.url


def handle_webhook(payload: bytes, sig_header: str) -> dict | None:
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        return None

    return {"type": event["type"], "data": event["data"]["object"]}

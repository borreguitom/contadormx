from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.core.database import get_db, User
from app.core.deps import get_current_user
from app.core.config import settings
from app.services.billing import PLANS, create_checkout_session, create_portal_session, handle_webhook

router = APIRouter()

FRONTEND_URL = settings.FRONTEND_URL


class CheckoutRequest(BaseModel):
    plan: str


@router.get("/plans")
def get_plans():
    return {"plans": [{"id": k, **{kk: vv for kk, vv in v.items() if kk != "stripe_price_id"}} for k, v in PLANS.items()]}


@router.get("/status")
async def get_billing_status(current_user: User = Depends(get_current_user)):
    plan = current_user.plan or "free"
    limits = PLANS.get(plan, PLANS["free"])
    return {
        "plan": plan,
        "queries_used": current_user.queries_this_month or 0,
        "queries_limit": limits["queries"],
        "clientes_limit": limits["clientes"],
        "stripe_customer_id": current_user.stripe_customer_id,
    }


@router.post("/checkout")
async def create_checkout(
    req: CheckoutRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if req.plan not in PLANS or req.plan == "free":
        raise HTTPException(400, "Plan no válido")
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(503, "Stripe no configurado en este entorno")

    try:
        url = create_checkout_session(
            plan=req.plan,
            user_email=current_user.email,
            user_id=current_user.id,
            success_url=f"{FRONTEND_URL}/billing?success=1",
            cancel_url=f"{FRONTEND_URL}/billing?canceled=1",
        )
    except Exception:
        raise HTTPException(503, "Error al procesar el pago. Intenta de nuevo o contacta soporte.")

    return {"checkout_url": url}


@router.post("/portal")
async def customer_portal(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.stripe_customer_id:
        raise HTTPException(400, "No tienes una suscripción activa")
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(503, "Stripe no configurado en este entorno")

    url = create_portal_session(
        customer_id=current_user.stripe_customer_id,
        return_url=f"{FRONTEND_URL}/billing",
    )
    return {"portal_url": url}


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    event = handle_webhook(payload, sig)

    if not event:
        raise HTTPException(400, "Webhook inválido")

    obj = event["data"]

    if event["type"] == "checkout.session.completed":
        user_id = int(obj.get("metadata", {}).get("user_id", 0))
        plan = obj.get("metadata", {}).get("plan", "free")
        customer_id = obj.get("customer")
        subscription_id = obj.get("subscription")

        if user_id:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if user:
                user.plan = plan
                user.stripe_customer_id = customer_id
                user.stripe_subscription_id = subscription_id
                await db.commit()

    elif event["type"] in ("customer.subscription.deleted", "customer.subscription.paused"):
        customer_id = obj.get("customer")
        if customer_id:
            result = await db.execute(select(User).where(User.stripe_customer_id == customer_id))
            user = result.scalar_one_or_none()
            if user:
                user.plan = "free"
                await db.commit()

    elif event["type"] == "customer.subscription.updated":
        customer_id = obj.get("customer")
        status = obj.get("status")
        if customer_id and status == "active":
            plan = obj.get("metadata", {}).get("plan", "pro")
            result = await db.execute(select(User).where(User.stripe_customer_id == customer_id))
            user = result.scalar_one_or_none()
            if user:
                user.plan = plan
                await db.commit()

    return {"received": True}

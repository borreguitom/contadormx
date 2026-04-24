from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db, User, Cliente, Conversation
from app.core.deps import get_current_user, PLAN_LIMITS
from app.services.fiscal_calendar import proximas_obligaciones

router = APIRouter()


@router.get("/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    total_clientes = (await db.execute(
        select(func.count()).select_from(Cliente).where(Cliente.user_id == current_user.id)
    )).scalar_one()

    recientes = (await db.execute(
        select(Conversation)
        .where(Conversation.user_id == current_user.id)
        .order_by(Conversation.created_at.desc())
        .limit(5)
    )).scalars().all()

    plan = current_user.plan or "free"
    limits = PLAN_LIMITS[plan]
    queries_used = current_user.queries_this_month or 0

    return {
        "user_nombre": current_user.nombre or current_user.email.split("@")[0],
        "plan": plan,
        "queries_used": queries_used,
        "queries_limit": limits["queries"],
        "total_clientes": total_clientes,
        "clientes_limit": limits["clientes"],
        "conversaciones_recientes": [
            {
                "id": c.id,
                "titulo": c.title,
                "fecha": c.created_at.strftime("%d %b %Y") if c.created_at else "",
            }
            for c in recientes
        ],
        "proximas_obligaciones": proximas_obligaciones(5),
    }

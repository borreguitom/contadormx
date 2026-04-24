"""
Endpoints de gestión de base de conocimiento legal.
GET  /api/laws/recent-updates     — últimas reformas detectadas
GET  /api/laws/stats              — estado de la colección Qdrant
POST /api/laws/search             — búsqueda manual en la base vectorial
POST /api/laws/trigger-scrape     — ejecutar scrapers manualmente
GET  /api/laws/inpc               — INPC y UMA actuales
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel, Field

from app.core.database import get_db, LawUpdate
from app.core.deps import get_current_user
from app.scrapers.inegi import fetch_inpc_actual, get_uma_2025

router = APIRouter(dependencies=[Depends(get_current_user)])


class SearchRequest(BaseModel):
    query: str
    fuente: str = "todas"
    top_k: int = Field(5, ge=1, le=50)


@router.get("/recent-updates")
async def recent_updates(limit: int = Query(20, ge=1, le=100), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(LawUpdate)
        .order_by(desc(LawUpdate.created_at))
        .limit(limit)
    )
    updates = result.scalars().all()
    return [
        {
            "id": u.id,
            "ley": u.ley,
            "tipo": u.tipo,
            "titulo": u.titulo,
            "url": u.url,
            "fecha_publicacion": u.fecha_publicacion,
            "indexado": u.indexado,
            "created_at": u.created_at,
        }
        for u in updates
    ]


@router.get("/stats")
async def rag_stats():
    try:
        from app.services.rag import collection_stats
        stats = await collection_stats()
        return {"status": "ok", **stats}
    except Exception as e:
        return {"status": "error", "mensaje": str(e), "accion": "Asegúrate de que Qdrant esté corriendo y la colección inicializada."}


@router.post("/search")
async def search_laws(req: SearchRequest):
    try:
        from app.services.rag import search
        articulos = await search(query=req.query, fuente=req.fuente, top_k=req.top_k)
        return {"query": req.query, "articulos": articulos, "total": len(articulos)}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"RAG no disponible: {e}")


@router.post("/trigger-scrape")
async def trigger_scrape(fuente: str = "dof"):
    """Dispara un scrape manual (no espera resultado — tarea async)."""
    from celery_app import celery_app
    fuente = fuente.lower()

    task_map = {
        "dof": "app.scrapers.tasks.scrape_dof",
        "sat": "app.scrapers.tasks.scrape_sat",
        "inpc": "app.scrapers.tasks.actualizar_inpc",
    }
    if fuente not in task_map:
        raise HTTPException(status_code=400, detail=f"Fuente desconocida. Opciones: {', '.join(task_map)}")

    try:
        task = celery_app.send_task(task_map[fuente])
        return {"status": "enqueued", "task_id": task.id, "fuente": fuente}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Celery no disponible: {e}")


@router.get("/inpc")
async def get_inpc():
    inpc = await fetch_inpc_actual()
    uma = get_uma_2025()
    return {
        "inpc": inpc,
        "uma_2025": uma,
    }

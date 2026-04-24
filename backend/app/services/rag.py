"""
RAG service — Qdrant vector store para legislación fiscal mexicana.
Crea la colección si no existe, upserta documentos, busca por similitud.
"""
import uuid
import asyncio
from typing import Optional

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    SearchRequest,
)

from app.core.config import settings
from app.services.embeddings import embed_query, embed_texts, get_embedding_dim

# Chunk de ley indexado
LawChunk = dict  # {ley, articulo, titulo, texto, fuente_url, fecha_actualizacion, vigente}

_client: Optional[AsyncQdrantClient] = None


def get_qdrant() -> AsyncQdrantClient:
    global _client
    if _client is None:
        _client = AsyncQdrantClient(url=settings.QDRANT_URL)
    return _client


async def ensure_collection() -> None:
    client = get_qdrant()
    collections = await client.get_collections()
    existing = {c.name for c in collections.collections}

    if settings.QDRANT_COLLECTION not in existing:
        await client.create_collection(
            collection_name=settings.QDRANT_COLLECTION,
            vectors_config=VectorParams(
                size=get_embedding_dim(),
                distance=Distance.COSINE,
            ),
        )
        print(f"Colección '{settings.QDRANT_COLLECTION}' creada ({get_embedding_dim()} dims).")
    else:
        print(f"Colección '{settings.QDRANT_COLLECTION}' ya existe.")


async def upsert_chunks(chunks: list[LawChunk]) -> int:
    """
    Inserta o actualiza chunks en Qdrant.
    El ID se genera como UUID determinístico de (ley, articulo) para evitar duplicados.
    Retorna el número de chunks insertados.
    """
    if not chunks:
        return 0

    client = get_qdrant()
    texts = [c["texto"] for c in chunks]
    embeddings = await embed_texts(texts)

    points = []
    for chunk, vector in zip(chunks, embeddings):
        # ID determinístico para upsert idempotente
        chunk_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{chunk['ley']}:{chunk['articulo']}"))
        points.append(
            PointStruct(
                id=chunk_id,
                vector=vector,
                payload={
                    "ley": chunk["ley"],
                    "articulo": chunk["articulo"],
                    "titulo": chunk.get("titulo", ""),
                    "texto": chunk["texto"],
                    "fuente_url": chunk.get("fuente_url", ""),
                    "fecha_actualizacion": chunk.get("fecha_actualizacion", ""),
                    "vigente": chunk.get("vigente", True),
                },
            )
        )

    # Qdrant upsert en batches de 100
    BATCH = 100
    for i in range(0, len(points), BATCH):
        await client.upsert(
            collection_name=settings.QDRANT_COLLECTION,
            points=points[i : i + BATCH],
        )

    return len(points)


async def search(
    query: str,
    fuente: str = "todas",
    top_k: int = 5,
    solo_vigentes: bool = True,
) -> list[dict]:
    """
    Búsqueda semántica en la base de conocimiento legal.
    Retorna artículos relevantes con texto textual y metadatos.
    """
    client = get_qdrant()
    query_vector = await embed_query(query)

    query_filter = None
    conditions = []

    if solo_vigentes:
        conditions.append(FieldCondition(key="vigente", match=MatchValue(value=True)))
    if fuente != "todas":
        conditions.append(FieldCondition(key="ley", match=MatchValue(value=fuente.upper())))

    if conditions:
        query_filter = Filter(must=conditions)

    results = await client.search(
        collection_name=settings.QDRANT_COLLECTION,
        query_vector=query_vector,
        query_filter=query_filter,
        limit=top_k,
        with_payload=True,
    )

    articulos = []
    for r in results:
        p = r.payload
        articulos.append(
            {
                "ley": p.get("ley"),
                "articulo": p.get("articulo"),
                "titulo": p.get("titulo"),
                "texto": p.get("texto"),
                "fuente_url": p.get("fuente_url"),
                "fecha_actualizacion": p.get("fecha_actualizacion"),
                "score": round(r.score, 4),
                "cita": f"Art. {p.get('articulo')} {p.get('ley')}",
            }
        )

    return articulos


async def marcar_superseded(ley: str, articulo: str) -> None:
    """Marca un artículo como no vigente cuando es reemplazado por reforma."""
    client = get_qdrant()
    chunk_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{ley}:{articulo}"))
    await client.set_payload(
        collection_name=settings.QDRANT_COLLECTION,
        payload={"vigente": False},
        points=[chunk_id],
    )


async def collection_stats() -> dict:
    client = get_qdrant()
    info = await client.get_collection(settings.QDRANT_COLLECTION)
    return {
        "coleccion": settings.QDRANT_COLLECTION,
        "total_vectores": info.points_count,
        "dimension": info.config.params.vectors.size,
        "status": info.status,
    }

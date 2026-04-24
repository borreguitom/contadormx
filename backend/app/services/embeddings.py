"""
Servicio de embeddings — soporta Voyage AI (voyage-3-large, 1024 dims)
y OpenAI (text-embedding-3-large, 3072 dims) como fallback.
Dimension debe coincidir con la configurada en Qdrant al crear la colección.
"""
import asyncio
from typing import Union
import httpx

from app.core.config import settings

VOYAGE_DIM = 1024
OPENAI_DIM = 3072
BATCH_SIZE = 128


def get_embedding_dim() -> int:
    return VOYAGE_DIM if settings.EMBEDDING_PROVIDER == "voyage" else OPENAI_DIM


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embeds a list of texts. Batches automatically if > BATCH_SIZE."""
    if not texts:
        return []
    all_embeddings = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        if settings.EMBEDDING_PROVIDER == "voyage":
            batch_emb = await _embed_voyage(batch)
        else:
            batch_emb = await _embed_openai(batch)
        all_embeddings.extend(batch_emb)
    return all_embeddings


async def embed_query(text: str) -> list[float]:
    results = await embed_texts([text])
    return results[0]


async def _embed_voyage(texts: list[str]) -> list[list[float]]:
    if not settings.VOYAGE_API_KEY:
        raise ValueError("VOYAGE_API_KEY no configurada en .env")

    async with httpx.AsyncClient(timeout=60) as client:
        res = await client.post(
            "https://api.voyageai.com/v1/embeddings",
            headers={"Authorization": f"Bearer {settings.VOYAGE_API_KEY}"},
            json={"model": "voyage-3-large", "input": texts},
        )
        res.raise_for_status()
        data = res.json()
        return [item["embedding"] for item in sorted(data["data"], key=lambda x: x["index"])]


async def _embed_openai(texts: list[str]) -> list[list[float]]:
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY no configurada en .env")

    async with httpx.AsyncClient(timeout=60) as client:
        res = await client.post(
            "https://api.openai.com/v1/embeddings",
            headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
            json={"model": "text-embedding-3-large", "input": texts},
        )
        res.raise_for_status()
        data = res.json()
        return [item["embedding"] for item in sorted(data["data"], key=lambda x: x["index"])]

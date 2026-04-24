from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Any
import io

from app.services.doc_generator import generate_pdf, DOC_TYPES
from app.core.deps import get_current_user
from app.core.database import User

router = APIRouter()


class DocRequest(BaseModel):
    tipo: str
    datos: dict[str, Any]
    formato: str = "pdf"  # pdf | base64


@router.get("/templates")
def list_templates(_: User = Depends(get_current_user)):
    return {
        "templates": [
            {"id": k, **v}
            for k, v in DOC_TYPES.items()
        ]
    }


@router.post("/generate")
async def generate_document(req: DocRequest, _: User = Depends(get_current_user)):
    if req.tipo not in DOC_TYPES:
        raise HTTPException(400, f"Tipo '{req.tipo}' no válido. Opciones: {list(DOC_TYPES.keys())}")

    try:
        pdf_bytes = generate_pdf(req.tipo, req.datos)
    except Exception as e:
        raise HTTPException(500, "Error al generar el documento. Verifica los datos enviados.")

    rfc = req.datos.get("contribuyente_rfc") or req.datos.get("emisor_rfc") or "doc"
    safe_rfc = "".join(c for c in str(rfc) if c.isalnum() or c in "-_")[:20]
    filename = f"{req.tipo}_{safe_rfc}.pdf"

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=\"{filename}\""},
    )

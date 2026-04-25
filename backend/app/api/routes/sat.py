"""SAT integration routes — credential management and CFDI bulk download."""
from __future__ import annotations

from datetime import date
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, User, SatCredential, SatDownloadJob, CfdiDownloaded
from app.core.deps import get_current_user
from app.services.crypto import encrypt_bytes, encrypt_str, decrypt_str

router = APIRouter(dependencies=[Depends(get_current_user)])


# ── Credential endpoints ──────────────────────────────────────────────────────

@router.post("/credentials", status_code=201)
async def upload_credential(
    cer_file: UploadFile = File(...),
    key_file: UploadFile = File(...),
    key_password: str = Form(...),
    alias: str = Form(""),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload e.firma (.cer + .key) and store encrypted."""
    cer_bytes = await cer_file.read()
    key_bytes = await key_file.read()

    # Extract RFC from certificate
    try:
        from cryptography.x509 import load_der_x509_certificate
        from cryptography.hazmat.primitives.serialization import load_der_private_key
        cert = load_der_x509_certificate(cer_bytes)
        # RFC is in the subject CN or serialNumber
        cn = cert.subject.get_attributes_for_oid(
            __import__("cryptography.x509.oid", fromlist=["NameOID"]).NameOID.COMMON_NAME
        )
        rfc = cn[0].value.split("/")[0].strip().upper() if cn else "DESCONOCIDO"
        valid_to = cert.not_valid_after_utc
    except Exception:
        rfc = alias.upper() or "RFC_DESCONOCIDO"
        valid_to = None

    # Verify password decrypts the key
    try:
        from cryptography.hazmat.primitives.serialization import load_der_private_key
        load_der_private_key(key_bytes, key_password.encode())
    except Exception:
        raise HTTPException(400, "Contraseña incorrecta para la llave privada (.key)")

    cred = SatCredential(
        user_id=current_user.id,
        rfc=rfc,
        alias=alias or rfc,
        cer_enc=encrypt_bytes(cer_bytes),
        key_enc=encrypt_bytes(key_bytes),
        pwd_enc=encrypt_str(key_password),
        valid_to=valid_to,
    )
    db.add(cred)
    await db.commit()
    await db.refresh(cred)
    return {
        "id": cred.id,
        "rfc": cred.rfc,
        "alias": cred.alias,
        "valid_to": cred.valid_to.isoformat() if cred.valid_to else None,
    }


@router.get("/credentials")
async def list_credentials(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(SatCredential).where(SatCredential.user_id == current_user.id)
    )
    creds = result.scalars().all()
    return [
        {
            "id": c.id,
            "rfc": c.rfc,
            "alias": c.alias,
            "valid_to": c.valid_to.isoformat() if c.valid_to else None,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in creds
    ]


@router.delete("/credentials/{cred_id}", status_code=204)
async def delete_credential(
    cred_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cred = await db.get(SatCredential, cred_id)
    if not cred or cred.user_id != current_user.id:
        raise HTTPException(404, "Credencial no encontrada")
    await db.delete(cred)
    await db.commit()


# ── Download job endpoints ────────────────────────────────────────────────────

class DownloadRequest(BaseModel):
    credential_id: int
    date_from: date
    date_to: date
    tipo_comprobante: Optional[Literal["I", "E", "T", "N", "P"]] = None
    tipo_solicitud: Literal["CFDI", "Metadata"] = "CFDI"


@router.post("/download", status_code=202)
async def request_download(
    req: DownloadRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Queue a SAT bulk download job."""
    cred = await db.get(SatCredential, req.credential_id)
    if not cred or cred.user_id != current_user.id:
        raise HTTPException(404, "Credencial no encontrada")

    if (req.date_to - req.date_from).days > 365:
        raise HTTPException(400, "El rango máximo por solicitud es 12 meses")

    job = SatDownloadJob(
        user_id=current_user.id,
        credential_id=cred.id,
        rfc=cred.rfc,
        date_from=req.date_from,
        date_to=req.date_to,
        tipo_comprobante=req.tipo_comprobante,
        tipo_solicitud=req.tipo_solicitud,
        status="pending",
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    try:
        from celery_app import celery_app as _celery
        _celery.send_task("app.tasks.sat_download.ejecutar_descarga", args=[job.id])
    except Exception as e:
        job.status = "error"
        job.error_msg = f"No se pudo encolar tarea: {e}"
        await db.commit()

    return {"job_id": job.id, "status": job.status}


@router.get("/jobs")
async def list_jobs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(SatDownloadJob)
        .where(SatDownloadJob.user_id == current_user.id)
        .order_by(SatDownloadJob.created_at.desc())
        .limit(20)
    )
    jobs = result.scalars().all()
    return [
        {
            "id": j.id,
            "rfc": j.rfc,
            "status": j.status,
            "date_from": j.date_from.isoformat(),
            "date_to": j.date_to.isoformat(),
            "tipo_comprobante": j.tipo_comprobante,
            "total_cfdi": j.total_cfdi,
            "packages_total": j.packages_total,
            "packages_downloaded": j.packages_downloaded,
            "progress": round(j.packages_downloaded / j.packages_total * 100) if j.packages_total else 0,
            "error_msg": j.error_msg,
            "created_at": j.created_at.isoformat() if j.created_at else None,
        }
        for j in jobs
    ]


@router.get("/jobs/{job_id}")
async def get_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = await db.get(SatDownloadJob, job_id)
    if not job or job.user_id != current_user.id:
        raise HTTPException(404, "Job no encontrado")
    return {
        "id": job.id,
        "rfc": job.rfc,
        "status": job.status,
        "sat_request_id": job.sat_request_id,
        "date_from": job.date_from.isoformat(),
        "date_to": job.date_to.isoformat(),
        "tipo_solicitud": job.tipo_solicitud,
        "tipo_comprobante": job.tipo_comprobante,
        "total_cfdi": job.total_cfdi,
        "packages_total": job.packages_total,
        "packages_downloaded": job.packages_downloaded,
        "progress": round(job.packages_downloaded / job.packages_total * 100) if job.packages_total else 0,
        "error_msg": job.error_msg,
        "created_at": job.created_at.isoformat() if job.created_at else None,
    }


# ── CFDI list endpoint ────────────────────────────────────────────────────────

@router.get("/cfdis")
async def list_cfdis(
    tipo: Optional[str] = None,
    rfc_contraparte: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = select(CfdiDownloaded).where(CfdiDownloaded.user_id == current_user.id)
    if tipo:
        q = q.where(CfdiDownloaded.tipo_comprobante == tipo)
    if rfc_contraparte:
        q = q.where(
            (CfdiDownloaded.rfc_emisor == rfc_contraparte) |
            (CfdiDownloaded.rfc_receptor == rfc_contraparte)
        )
    q = q.order_by(CfdiDownloaded.fecha_emision.desc()).limit(limit).offset(offset)
    result = await db.execute(q)
    cfdis = result.scalars().all()

    count_result = await db.execute(
        select(func.count()).where(CfdiDownloaded.user_id == current_user.id)
    )
    total = count_result.scalar()

    return {
        "total": total,
        "items": [
            {
                "id": c.id,
                "uuid": c.uuid,
                "rfc_emisor": c.rfc_emisor,
                "nombre_emisor": c.nombre_emisor,
                "rfc_receptor": c.rfc_receptor,
                "nombre_receptor": c.nombre_receptor,
                "total": float(c.total) if c.total else None,
                "fecha_emision": c.fecha_emision.isoformat() if c.fecha_emision else None,
                "tipo_comprobante": c.tipo_comprobante,
                "metodo_pago": c.metodo_pago,
                "moneda": c.moneda,
                "estatus": c.estatus,
            }
            for c in cfdis
        ],
    }


@router.get("/cfdis/{uuid}/xml")
async def get_cfdi_xml(
    uuid: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(CfdiDownloaded).where(
            CfdiDownloaded.uuid == uuid.upper(),
            CfdiDownloaded.user_id == current_user.id,
        )
    )
    cfdi = result.scalar_one_or_none()
    if not cfdi:
        raise HTTPException(404, "CFDI no encontrado")
    from fastapi.responses import Response
    return Response(content=cfdi.xml_data, media_type="application/xml")

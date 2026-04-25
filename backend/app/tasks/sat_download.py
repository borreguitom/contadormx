"""Celery task: execute SAT bulk CFDI download job asynchronously."""
from __future__ import annotations
import logging
import time

from celery_app import celery_app

logger = logging.getLogger(__name__)

STATUS_TERMINADA = "3"
STATUS_ERROR = {"4", "5", "6", "7"}
POLL_INTERVAL = 15   # seconds between polls
MAX_POLLS = 120      # 120 * 15s = 30 min max


@celery_app.task(
    name="app.tasks.sat_download.ejecutar_descarga",
    bind=True,
    max_retries=0,
    time_limit=2000,
    soft_time_limit=1900,
)
def ejecutar_descarga(self, job_id: int) -> dict:
    import asyncio
    return asyncio.run(_run(job_id))


async def _run(job_id: int) -> dict:
    from sqlalchemy import select
    from app.core.database import AsyncSessionLocal, SatDownloadJob, SatCredential, CfdiDownloaded
    from app.services.crypto import decrypt_bytes, decrypt_str
    from app.services import sat_ws

    async with AsyncSessionLocal() as db:
        job = await db.get(SatDownloadJob, job_id)
        if not job:
            return {"error": "job not found"}

        try:
            job.status = "processing"
            await db.flush()

            cred = await db.get(SatCredential, job.credential_id)
            cer_bytes = decrypt_bytes(cred.cer_enc)
            key_bytes = decrypt_bytes(cred.key_enc)
            key_pwd = decrypt_str(cred.pwd_enc)

            fiel, token = sat_ws.authenticate(cer_bytes, key_bytes, key_pwd)
            logger.info(f"[SAT] job={job_id} autenticado rfc={cred.rfc}")

            request_id = sat_ws.request_download(
                fiel, token, cred.rfc,
                job.date_from, job.date_to,
                tipo_comprobante=job.tipo_comprobante,
                tipo_solicitud=job.tipo_solicitud,
            )
            job.sat_request_id = request_id
            await db.flush()
            logger.info(f"[SAT] job={job_id} request_id={request_id}")

            # Poll for completion
            packages = []
            for poll in range(MAX_POLLS):
                time.sleep(POLL_INTERVAL)
                status = sat_ws.verify_download(fiel, token, cred.rfc, request_id)
                estado = str(status.get("EstadoSolicitud", ""))
                logger.info(f"[SAT] job={job_id} poll={poll} estado={estado}")

                if estado == STATUS_TERMINADA:
                    packages = status.get("IdsPaquetes", [])
                    job.packages_total = len(packages)
                    await db.flush()
                    break
                elif estado in STATUS_ERROR:
                    raise Exception(f"SAT error estado={estado}: {status.get('CodigoEstadoSolicitud', '')}")

                # Re-authenticate every 20 polls (token expires in ~5 min)
                if poll > 0 and poll % 18 == 0:
                    try:
                        _, token = sat_ws.authenticate(cer_bytes, key_bytes, key_pwd)
                    except Exception:
                        pass

            if not packages:
                job.status = "completed"
                job.total_cfdi = 0
                await db.commit()
                return {"status": "completed", "total": 0}

            # Download packages
            total = 0
            for pkg_id in packages:
                try:
                    cfdis = sat_ws.download_package(fiel, token, cred.rfc, pkg_id)
                    for c in cfdis:
                        # Upsert by UUID
                        existing = await db.execute(
                            select(CfdiDownloaded).where(CfdiDownloaded.uuid == c.uuid)
                        )
                        if existing.scalar_one_or_none():
                            continue
                        db.add(CfdiDownloaded(
                            user_id=job.user_id,
                            job_id=job.id,
                            uuid=c.uuid,
                            rfc_emisor=c.rfc_emisor,
                            nombre_emisor=c.nombre_emisor,
                            rfc_receptor=c.rfc_receptor,
                            nombre_receptor=c.nombre_receptor,
                            total=c.total,
                            subtotal=c.subtotal,
                            impuestos_trasladados=c.impuestos_trasladados,
                            fecha_emision=c.fecha_emision,
                            fecha_timbrado=c.fecha_timbrado,
                            tipo_comprobante=c.tipo_comprobante,
                            metodo_pago=c.metodo_pago,
                            forma_pago=c.forma_pago,
                            moneda=c.moneda,
                            serie=c.serie,
                            folio=c.folio,
                            xml_data=c.xml_data,
                        ))
                        total += 1
                    job.packages_downloaded += 1
                    await db.flush()
                except Exception as e:
                    logger.warning(f"[SAT] job={job_id} paquete={pkg_id} error: {e}")

            job.status = "completed"
            job.total_cfdi = total
            await db.commit()
            logger.info(f"[SAT] job={job_id} completado total={total}")
            return {"status": "completed", "total": total}

        except Exception as exc:
            logger.error(f"[SAT] job={job_id} FALLÓ: {exc}")
            job.status = "error"
            job.error_msg = str(exc)[:500]
            await db.commit()
            return {"status": "error", "error": str(exc)}

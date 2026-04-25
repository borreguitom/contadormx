from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "contadormx",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.scrapers.tasks", "app.tasks.fiscal_reminders", "app.tasks.emails", "app.tasks.sat_download"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Mexico_City",
    enable_utc=True,
    task_track_started=True,
    # Reintentos automáticos en fallo
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# Tareas programadas
celery_app.conf.beat_schedule = {
    # DOF: todos los días a las 7am (el DOF publica de madrugada)
    "scrape-dof-diario": {
        "task": "app.scrapers.tasks.scrape_dof",
        "schedule": crontab(hour=7, minute=0),
    },
    # SAT novedades: lunes, miércoles, viernes a las 9am
    "scrape-sat-novedades": {
        "task": "app.scrapers.tasks.scrape_sat",
        "schedule": crontab(hour=9, minute=0, day_of_week="1,3,5"),
    },
    # INPC: el 10 de cada mes (INEGI publica alrededor del día 9-10)
    "actualizar-inpc": {
        "task": "app.scrapers.tasks.actualizar_inpc",
        "schedule": crontab(hour=10, minute=0, day_of_month=10),
    },
    # Recordatorios fiscales: todos los días a las 8am
    "recordatorios-fiscales": {
        "task": "app.tasks.fiscal_reminders.enviar_recordatorios",
        "schedule": crontab(hour=8, minute=0),
    },
}

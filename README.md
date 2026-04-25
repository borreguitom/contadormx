# ContadorMX

Agente fiscal y contable con IA para contadores mexicanos. FastAPI + Next.js 15 + Claude Sonnet.

---

## Stack

| Capa | Tecnología |
|---|---|
| Frontend | Next.js 15, TypeScript, Tailwind CSS |
| Backend | FastAPI, SQLAlchemy async, Alembic |
| Base de datos | PostgreSQL 16 |
| Cache / broker | Redis 7 |
| Vector DB | Qdrant |
| IA | Anthropic Claude (claude-sonnet-4-6) |
| Embeddings | VoyageAI |
| Pagos | Stripe |
| Email | Resend + Celery |
| Tareas async | Celery + Redis |
| SAT | cfdiclient (SOAP Descarga Masiva) |

---

## Inicio rápido (Windows)

**Requisitos:** Docker Desktop, Python 3.11+, Node 18+

```powershell
# Clona y entra al proyecto
git clone https://github.com/borreguitom/contadormx.git
cd contadormx

# Arranca todo (Docker + backend + frontend)
.\start.ps1
```

El script hace automáticamente:
1. Verifica Docker, Python y Node
2. Crea `backend/.env` desde `.env.example` si no existe
3. Crea el venv de Python e instala dependencias
4. Instala dependencias de Node
5. Levanta Postgres (puerto 5433), Redis (6379) y Qdrant (6333) en Docker
6. Inicia el backend FastAPI en una ventana nueva (puerto 8000)
7. Inicia el frontend Next.js en una ventana nueva (puerto 3000)

Para detener:
```powershell
.\stop.ps1
```

---

## Variables de entorno

Copia `backend/.env.example` a `backend/.env` y configura:

```env
# Requerido para que el chat funcione
ANTHROPIC_API_KEY=sk-ant-api03-...

# Postgres — usa puerto 5433 porque el 5432 puede estar ocupado por Postgres nativo
DATABASE_URL=postgresql://contadormx:contadormx_dev@localhost:5433/contadormx

REDIS_URL=redis://localhost:6379/0
QDRANT_URL=http://localhost:6333

# JWT — cambia esto antes de producción (mínimo 32 caracteres)
JWT_SECRET=genera-un-secreto-aleatorio-largo-aqui
JWT_EXPIRE_MINUTES=10080

# Embeddings (elige uno)
VOYAGE_API_KEY=pa-...
EMBEDDING_PROVIDER=voyage

# Email transaccional
RESEND_API_KEY=re_...

# Stripe (opcional para facturación)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_PRO=price_...
STRIPE_PRICE_AGENCIA=price_...

FRONTEND_URL=http://localhost:3000
CORS_ORIGINS=["http://localhost:3000"]
APP_ENV=development
```

---

## Estructura del proyecto

```
contadormx/
├── backend/
│   ├── app/
│   │   ├── api/routes/      # Endpoints REST
│   │   │   ├── auth.py      # Registro, login, logout, reset password
│   │   │   ├── chat.py      # Agente fiscal (Claude + tools)
│   │   │   ├── calc.py      # Calculadoras: ISR, IVA, IMSS, nómina, finiquito
│   │   │   ├── cfdi.py      # Validador de CFDI XML
│   │   │   ├── clients.py   # CRUD de clientes
│   │   │   ├── dashboard.py # Stats del usuario
│   │   │   ├── documentos.py# Upload/análisis de facturas + DIOT
│   │   │   ├── laws.py      # Búsqueda semántica en leyes fiscales
│   │   │   ├── billing.py   # Planes y checkout Stripe
│   │   │   ├── docs.py      # Generador de documentos (PDF/DOCX)
│   │   │   └── sat.py       # Descarga masiva de CFDIs del SAT
│   │   ├── calculators/     # Lógica fiscal: ISR PF/PM, IVA, IMSS, nómina
│   │   ├── core/
│   │   │   ├── config.py    # Settings (pydantic-settings)
│   │   │   ├── database.py  # Modelos SQLAlchemy + AsyncSession
│   │   │   ├── deps.py      # Dependencias FastAPI (auth, límites de plan)
│   │   │   └── limiter.py   # Rate limiting (slowapi)
│   │   ├── scrapers/        # DOF, SAT novedades, INPC (tareas Celery)
│   │   ├── services/
│   │   │   ├── agent.py     # Orquestador del agente Claude
│   │   │   ├── crypto.py    # Fernet AES-128 para credenciales SAT
│   │   │   ├── doc_extractor.py # Extracción de datos de XML/PDF
│   │   │   ├── doc_generator.py # Generación de PDF/DOCX con Jinja2
│   │   │   ├── embeddings.py    # VoyageAI / OpenAI embeddings
│   │   │   ├── rag.py       # Búsqueda semántica en Qdrant
│   │   │   ├── sat_ws.py    # Cliente SOAP SAT (Descarga Masiva)
│   │   │   └── tools.py     # Herramientas del agente (Claude tool_use)
│   │   └── tasks/
│   │       ├── emails.py        # Emails transaccionales (Celery)
│   │       ├── fiscal_reminders.py # Recordatorios de obligaciones
│   │       └── sat_download.py  # Tarea de descarga masiva SAT
│   ├── alembic/versions/    # Migraciones de DB
│   ├── celery_app.py        # Configuración de Celery
│   └── requirements.txt
├── frontend/
│   ├── app/(app)/           # Rutas autenticadas
│   │   ├── dashboard/       # Panel principal
│   │   ├── chat/            # Chat con el agente fiscal
│   │   ├── clientes/        # Gestión de clientes
│   │   ├── calculadoras/    # Calculadoras fiscales
│   │   ├── cfdi/            # Validador de CFDI
│   │   ├── documentos/      # Generador de documentos
│   │   ├── sat/             # Descarga masiva SAT (e.firma)
│   │   ├── declaracion-anual/
│   │   ├── calendario/      # Calendario fiscal
│   │   └── billing/         # Planes y suscripción
│   ├── app/(auth)/          # Login, registro, reset
│   ├── components/
│   │   └── layout/Sidebar.tsx
│   └── lib/
│       ├── api.ts           # Cliente HTTP + tipos TypeScript
│       └── auth.tsx         # Contexto de autenticación
├── docker-compose.yml       # Postgres 16, Redis 7, Qdrant
├── start.ps1                # Script de inicio (Windows)
└── stop.ps1                 # Script de parada
```

---

## API

Base URL: `http://localhost:8000`  
Documentación interactiva: `http://localhost:8000/docs`

### Auth `/api/auth`
| Método | Ruta | Descripción |
|---|---|---|
| POST | `/register` | Registro con email + password |
| POST | `/login` | Login (OAuth2 form-urlencoded) → JWT |
| POST | `/logout` | Invalida el JWT en Redis blocklist |
| POST | `/forgot-password` | Envía email de reset |
| POST | `/reset-password` | Cambia contraseña con token |

### Chat `/api/chat`
| Método | Ruta | Descripción |
|---|---|---|
| POST | `/message` | Consulta al agente fiscal (Claude + tools) |
| GET | `/conversations` | Historial de conversaciones |
| GET | `/conversations/{id}` | Mensajes de una conversación |

### Calculadoras `/api/calc`
| Método | Ruta | Descripción |
|---|---|---|
| POST | `/isr/personas-fisicas` | ISR mensual persona física |
| POST | `/isr/personas-morales` | ISR mensual persona moral |
| POST | `/iva` | Cálculo de IVA |
| POST | `/imss` | Cuotas IMSS/INFONAVIT |
| POST | `/nomina` | Nómina con retenciones |
| POST | `/finiquito` | Cálculo de finiquito |
| POST | `/declaracion-anual/pf` | Declaración anual PF |

### CFDI `/api/cfdi`
| Método | Ruta | Descripción |
|---|---|---|
| POST | `/validate` | Valida XML de CFDI (3.3 y 4.0) |

### Clientes `/api/clients`
| Método | Ruta | Descripción |
|---|---|---|
| GET | `/` | Lista clientes del usuario |
| POST | `/` | Crea cliente |
| GET | `/{id}` | Detalle de cliente |

### Documentos `/api/documentos`
| Método | Ruta | Descripción |
|---|---|---|
| POST | `/{cliente_id}/upload` | Sube facturas (XML/PDF) |
| GET | `/{cliente_id}` | Lista documentos del cliente |
| GET | `/{cliente_id}/resumen` | Resumen fiscal (ingresos/egresos/IVA) |
| DELETE | `/{doc_id}/documento` | Elimina documento |
| GET | `/{cliente_id}/exportar-excel` | Exporta a Excel |
| GET | `/{cliente_id}/diot` | Genera DIOT |

### SAT Descarga Masiva `/api/sat`
| Método | Ruta | Descripción |
|---|---|---|
| POST | `/credentials` | Registra e.firma (.cer + .key) |
| GET | `/credentials` | Lista credenciales del usuario |
| DELETE | `/credentials/{id}` | Elimina credencial |
| POST | `/download` | Solicita descarga masiva al SAT |
| GET | `/jobs` | Historial de descargas |
| GET | `/jobs/{id}` | Estado de una descarga |
| GET | `/cfdis` | Lista CFDIs descargados |
| GET | `/cfdis/{uuid}/xml` | Descarga XML de un CFDI |

### Dashboard, Billing, Laws
- `GET /api/dashboard/stats` — métricas del usuario
- `GET /api/billing/status` — plan y uso
- `POST /api/billing/checkout` — crear sesión de pago Stripe
- `POST /api/laws/search` — búsqueda semántica en leyes fiscales

---

## Base de datos

Migraciones con Alembic. Para aplicar:

```powershell
cd backend
.\venv\Scripts\alembic upgrade head
```

### Tablas principales

| Tabla | Descripción |
|---|---|
| `users` | Usuarios con plan (free/pro/agencia) y contador de queries |
| `clientes` | Clientes del contador |
| `conversations` | Historial de chats |
| `messages` | Mensajes individuales con tools_used |
| `documentos` | Facturas/CFDIs subidos por el contador |
| `law_updates` | Artículos de leyes fiscales indexados en Qdrant |
| `sat_credentials` | e.firma cifrada con Fernet AES-128 |
| `sat_download_jobs` | Jobs de descarga masiva con estado y progreso |
| `cfdi_downloaded` | CFDIs descargados del SAT con todos sus campos |

---

## Seguridad

- **JWT** con `jti` único + blocklist en Redis al hacer logout
- **Rate limiting** con slowapi: 5-10 req/min en endpoints sensibles
- **e.firma** nunca en texto plano — cifrada con Fernet (clave derivada de `JWT_SECRET` via SHA-256)
- **XML parsing** con `defusedxml` para prevenir XXE
- **CORS** restringido a `CORS_ORIGINS`
- **Security headers** en cada respuesta: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, etc.
- **Passwords** con bcrypt (cost factor 12)
- **Reset tokens** consumidos atómicamente con Redis `GETDEL` (evita race condition TOCTOU)

---

## Planes

| Plan | Queries/mes | Clientes |
|---|---|---|
| Free | 50 | 5 |
| Pro | 1,000 | 50 |
| Agencia | Ilimitado | Ilimitado |

---

## Descarga masiva SAT

Requiere e.firma vigente (certificado `.cer` + llave privada `.key`).  
Usa la API oficial SOAP del SAT (Servicio de Descarga Masiva de CFDIs).

**Flujo:**
1. Sube tu e.firma en `/sat` → se valida y guarda cifrada
2. Selecciona rango de fechas (máx 1 año por solicitud) y tipo de comprobante
3. El backend encola una tarea Celery que:
   - Autentica contra el SAT (token válido ~5 min)
   - Solicita el paquete de CFDIs
   - Hace polling hasta que el SAT lo prepare (puede tardar minutos)
   - Descarga los ZIPs, extrae y parsea cada XML
   - Guarda los CFDIs en la base de datos (deduplicados por UUID)
4. Consulta tus CFDIs descargados con filtros por tipo y RFC

**Instalar cfdiclient (solo la primera vez):**
```powershell
.\backend\venv\Scripts\pip install cfdiclient==0.1.0
```

---

## Desarrollo

### Correr solo el backend
```powershell
cd backend
.\venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

### Correr solo el frontend
```powershell
cd frontend
npm run dev
```

### Worker Celery (para emails y descarga SAT)
```powershell
cd backend
.\venv\Scripts\activate
celery -A celery_app worker --loglevel=info
```

### Crear nueva migración
```powershell
cd backend
.\venv\Scripts\alembic revision --autogenerate -m "descripcion"
.\venv\Scripts\alembic upgrade head
```

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
git clone https://github.com/borreguitom/contadormx.git
cd contadormx
.\start.ps1
```

El script hace automáticamente:
1. Verifica Docker, Python y Node
2. Crea `backend/.env` desde `.env.example` si no existe
3. Crea el venv de Python e instala dependencias
4. Instala dependencias de Node
5. Levanta Postgres (5433), Redis (6379) y Qdrant (6333) en Docker
6. Inicia el backend FastAPI en ventana nueva (puerto 8000)
7. Inicia el frontend Next.js en ventana nueva (puerto 3000)

```powershell
.\stop.ps1   # Para detener todo
```

**Primer uso — comandos adicionales:**
```powershell
# Aplicar migraciones (primera vez o después de actualizar)
cd backend
.\venv\Scripts\alembic upgrade head

# Instalar cliente SAT (necesario para descarga masiva)
.\venv\Scripts\pip install cfdiclient==0.1.0
```

---

## Variables de entorno

Copia `backend/.env.example` a `backend/.env` y configura:

```env
# Requerido para que el chat funcione
ANTHROPIC_API_KEY=sk-ant-api03-...

# Postgres — puerto 5433 para no colisionar con Postgres nativo de Windows
DATABASE_URL=postgresql://contadormx:contadormx_dev@localhost:5433/contadormx

REDIS_URL=redis://localhost:6379/0
QDRANT_URL=http://localhost:6333

# JWT — cambia esto antes de producción (mínimo 32 caracteres)
JWT_SECRET=genera-un-secreto-aleatorio-largo-aqui
JWT_EXPIRE_MINUTES=10080

# Embeddings
VOYAGE_API_KEY=pa-...
EMBEDDING_PROVIDER=voyage

# Email transaccional
RESEND_API_KEY=re_...

# Stripe (opcional)
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
│   │   ├── api/routes/
│   │   │   ├── auth.py          # Registro, login, logout, reset password
│   │   │   ├── chat.py          # Agente fiscal (Claude + tools)
│   │   │   ├── calc.py          # Calculadoras: ISR, IVA, IMSS, nómina, finiquito
│   │   │   ├── cfdi.py          # Validador de CFDI XML
│   │   │   ├── clients.py       # CRUD de clientes
│   │   │   ├── dashboard.py     # Stats del usuario
│   │   │   ├── documentos.py    # Upload/análisis de facturas + DIOT
│   │   │   ├── empleados.py     # CRUD empleados + nómina masiva + Excel
│   │   │   ├── laws.py          # Búsqueda semántica en leyes fiscales
│   │   │   ├── billing.py       # Planes y checkout Stripe
│   │   │   ├── docs.py          # Generador de documentos (PDF/DOCX)
│   │   │   └── sat.py           # Descarga masiva de CFDIs del SAT
│   │   ├── calculators/         # Lógica fiscal: ISR PF/PM, IVA, IMSS, nómina
│   │   ├── core/
│   │   │   ├── config.py        # Settings (pydantic-settings)
│   │   │   ├── database.py      # Modelos SQLAlchemy + AsyncSession
│   │   │   ├── deps.py          # Auth, límites de plan
│   │   │   └── limiter.py       # Rate limiting (slowapi)
│   │   ├── scrapers/            # DOF, SAT novedades, INPC (Celery)
│   │   ├── services/
│   │   │   ├── agent.py         # Orquestador del agente Claude
│   │   │   ├── crypto.py        # Fernet AES-128 para credenciales SAT
│   │   │   ├── doc_extractor.py # Extracción de datos de XML/PDF
│   │   │   ├── doc_generator.py # Generación de PDF/DOCX con Jinja2
│   │   │   ├── embeddings.py    # VoyageAI / OpenAI embeddings
│   │   │   ├── rag.py           # Búsqueda semántica en Qdrant
│   │   │   ├── sat_ws.py        # Cliente SOAP SAT (Descarga Masiva)
│   │   │   └── tools.py         # Herramientas del agente (tool_use)
│   │   └── tasks/
│   │       ├── emails.py        # Emails transaccionales (Celery)
│   │       ├── fiscal_reminders.py
│   │       └── sat_download.py  # Tarea de descarga masiva SAT
│   ├── alembic/versions/        # Migraciones 001–005
│   ├── celery_app.py
│   └── requirements.txt
├── frontend/
│   ├── app/(app)/               # Rutas autenticadas
│   │   ├── dashboard/           # Panel principal + checklist primeros pasos
│   │   ├── chat/                # Chat con el agente fiscal
│   │   ├── clientes/            # Gestión de clientes
│   │   ├── calculadoras/        # Calculadoras fiscales
│   │   ├── cfdi/                # Validador de CFDI
│   │   ├── documentos/          # Generador de documentos
│   │   ├── nomina/              # Empleados + cálculo masivo + Excel
│   │   ├── sat/                 # Descarga masiva SAT (e.firma)
│   │   ├── declaracion-anual/
│   │   ├── calendario/          # Calendario fiscal
│   │   └── billing/             # Planes y suscripción
│   ├── app/(auth)/              # Login, registro, reset password
│   ├── components/
│   │   ├── layout/Sidebar.tsx
│   │   └── onboarding/
│   │       └── OnboardingWizard.tsx   # Wizard interactivo de primer uso
│   └── lib/
│       ├── api.ts               # Cliente HTTP + todos los tipos TypeScript
│       └── auth.tsx             # Contexto de autenticación
├── docker-compose.yml
├── start.ps1
└── stop.ps1
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
| POST | `/nomina` | Nómina individual con retenciones |
| POST | `/finiquito` | Cálculo de finiquito |
| POST | `/declaracion-anual/pf` | Declaración anual PF |

### Empleados / Nómina masiva `/api/empleados`
| Método | Ruta | Descripción |
|---|---|---|
| GET | `/template` | Descarga plantilla Excel para importar empleados |
| GET | `/{cliente_id}` | Lista empleados activos del cliente |
| POST | `/{cliente_id}` | Crea empleado |
| PUT | `/{cliente_id}/{emp_id}` | Actualiza empleado |
| DELETE | `/{cliente_id}/{emp_id}` | Baja lógica (fecha_baja + is_active=False) |
| POST | `/{cliente_id}/import` | Importación masiva desde Excel |
| POST | `/{cliente_id}/nomina` | Corre nómina para todos los empleados activos |
| GET | `/{cliente_id}/nomina/excel` | Exporta nómina calculada a Excel |

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
| GET | `/{cliente_id}/resumen` | Resumen fiscal (ingresos/egresos/IVA neto) |
| DELETE | `/{doc_id}/documento` | Elimina documento |
| GET | `/{cliente_id}/exportar-excel` | Exporta a Excel |
| GET | `/{cliente_id}/diot` | Genera DIOT (JSON o TXT) |

### SAT Descarga Masiva `/api/sat`
| Método | Ruta | Descripción |
|---|---|---|
| POST | `/credentials` | Registra e.firma (.cer + .key) cifrada |
| GET | `/credentials` | Lista credenciales del usuario |
| DELETE | `/credentials/{id}` | Elimina credencial |
| POST | `/download` | Solicita descarga masiva al SAT |
| GET | `/jobs` | Historial de descargas |
| GET | `/jobs/{id}` | Estado y progreso de un job |
| GET | `/cfdis` | Lista CFDIs descargados (filtros: tipo, RFC) |
| GET | `/cfdis/{uuid}/xml` | Descarga XML de un CFDI |

### Dashboard, Billing, Laws
| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/dashboard/stats` | Métricas del usuario (clientes, queries, obligaciones) |
| GET | `/api/billing/status` | Plan actual y límites |
| POST | `/api/billing/checkout` | Crear sesión de pago Stripe |
| POST | `/api/billing/portal` | Portal de gestión Stripe |
| POST | `/api/laws/search` | Búsqueda semántica en leyes fiscales |
| GET | `/api/laws/recent-updates` | Últimas actualizaciones legales |

---

## Base de datos

Migraciones con Alembic:

```powershell
cd backend
.\venv\Scripts\alembic upgrade head
```

### Tablas

| Tabla | Migración | Descripción |
|---|---|---|
| `users` | 001 | Usuarios con plan (free/pro/agencia) y contador de queries |
| `clientes` | 001 | Clientes del contador con RFC y régimen |
| `conversations` | 001 | Historial de chats con el agente |
| `messages` | 001 | Mensajes individuales con tools_used |
| `documentos` | 002 | Facturas/CFDIs subidos: datos extraídos de XML/PDF |
| `law_updates` | 003 | Artículos de leyes fiscales indexados en Qdrant |
| `sat_credentials` | 004 | e.firma cifrada con Fernet AES-128 |
| `sat_download_jobs` | 004 | Jobs de descarga masiva con estado y progreso |
| `cfdi_downloaded` | 004 | CFDIs descargados del SAT (deduplicados por UUID) |
| `empleados` | 005 | Empleados con RFC, CURP, NSS, salario, contrato |

---

## Onboarding

Al registrarse, el usuario ve un wizard interactivo de 4 pasos:

1. **Bienvenida** — propuestas de valor principales
2. **Rol** — contador / empresa / freelancer (personaliza el flujo)
3. **Primer cliente** — crea el cliente directamente desde el wizard vía API
4. **Siguiente paso** — acciones concretas según el rol: SAT, facturas, calculadora, chat

El dashboard muestra un **checklist "Primeros pasos"** con barra de progreso que detecta el estado real del usuario (¿tiene clientes? ¿ha chatado?) y desaparece al completarse.

Para reiniciar el wizard (desarrollo):
```javascript
localStorage.removeItem('cmx_onboarding_v2'); location.reload();
```

---

## Nómina masiva

Flujo para clientes con empleados:

1. Ve a `/nomina` y selecciona el cliente
2. Agrega empleados uno a uno **o** descarga la plantilla Excel, llénala y súbela
3. En la pestaña "Correr Nómina": selecciona período y fechas → calcula ISR, IMSS y neto para todos los empleados activos en un solo clic
4. Revisa el detalle por empleado y los totales (percepciones, ISR, IMSS obrero/patronal, INFONAVIT, costo empresa)
5. Exporta a Excel con dos hojas: detalle por empleado + resumen de totales

El cálculo usa salario diario × 30 como base mensual e integra automáticamente aguinaldo y vacaciones en el SDI (Art. 27 LSS).

---

## Descarga masiva SAT

Requiere e.firma vigente (`.cer` + `.key`). Usa la API SOAP oficial del SAT.

**Flujo:**
1. Sube tu e.firma en `/sat` → se valida y guarda cifrada (nunca en texto plano)
2. Selecciona rango de fechas (máx 1 año) y tipo de comprobante
3. El backend encola una tarea Celery que autentica, solicita, hace polling (hasta 30 min), descarga los ZIPs y parsea cada XML CFDI 3.3/4.0
4. Los CFDIs quedan en la BD deduplicados por UUID

```powershell
# Instalar cfdiclient (primera vez)
.\backend\venv\Scripts\pip install cfdiclient==0.1.0
```

---

## Seguridad

- **JWT** con `jti` único + blocklist en Redis al hacer logout
- **Rate limiting** con slowapi: 5–10 req/min en endpoints sensibles
- **e.firma** nunca en texto plano — Fernet AES-128, clave derivada de `JWT_SECRET` via SHA-256
- **XML parsing** con `defusedxml` para prevenir XXE
- **CORS** restringido a `CORS_ORIGINS`
- **Security headers** en cada respuesta: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`
- **Passwords** con bcrypt (cost factor 12)
- **Reset tokens** consumidos atómicamente con Redis `GETDEL` (sin race condition TOCTOU)

---

## Planes

| Plan | Queries/mes | Clientes |
|---|---|---|
| Free | 50 | 5 |
| Pro | 1,000 | 50 |
| Agencia | Ilimitado | Ilimitado |

---

## Desarrollo

```powershell
# Solo backend
cd backend
.\venv\Scripts\activate
uvicorn app.main:app --reload --port 8000

# Solo frontend
cd frontend
npm run dev

# Worker Celery (emails + descarga SAT)
cd backend
.\venv\Scripts\activate
celery -A celery_app worker --loglevel=info

# Nueva migración
cd backend
.\venv\Scripts\alembic revision --autogenerate -m "descripcion"
.\venv\Scripts\alembic upgrade head
```

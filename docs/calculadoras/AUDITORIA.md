# 🗄️ Migración Alembic — Auditoría de cálculos fiscales

Crea la tabla `calculos_fiscales` para auditar cada cálculo realizado en la plataforma.

---

## 📦 Contenido del paquete

```
contadormx_alembic/
├── alembic/versions/
│   └── a7f3c9b2e8d1_add_calculos_fiscales.py   ← La migración
├── app/
│   ├── models/
│   │   └── calculo_fiscal.py                    ← Modelo SQLAlchemy
│   ├── repositories/
│   │   └── calculo_fiscal_repository.py         ← Queries útiles
│   └── middleware/
│       └── audit_calculos.py                    ← Captura automática
└── README.md
```

---

## 🚀 Instalación

### 1. Copiar archivos al proyecto

```bash
# Desde tu repo contadormx
cd backend

# La migración (ajustar nombre si tienes versionado por fecha)
cp ../contadormx_alembic/alembic/versions/*.py alembic/versions/

# Modelo, repository y middleware
cp ../contadormx_alembic/app/models/calculo_fiscal.py app/models/
cp ../contadormx_alembic/app/repositories/calculo_fiscal_repository.py app/repositories/
cp ../contadormx_alembic/app/middleware/audit_calculos.py app/middleware/
```

### 2. Ajustar la migración

Edita `alembic/versions/a7f3c9b2e8d1_add_calculos_fiscales.py`:

```python
# CAMBIAR ESTE VALOR
down_revision = None  # ← Poner el ID de la última migración existente
```

Para encontrar la última revisión:
```bash
alembic current
# O ver la última en alembic/versions/ por fecha
ls -lt alembic/versions/ | head -2
```

### 3. (Opcional) Activar foreign keys

En la migración, descomentar si tienes las tablas `clientes` y `users`:

```python
op.create_foreign_key(
    "fk_calculos_cliente",
    "calculos_fiscales", "clientes",
    ["cliente_id"], ["id"],
    ondelete="SET NULL",
)
```

En el modelo `app/models/calculo_fiscal.py`, descomentar también:

```python
cliente_id: Mapped[Optional[int]] = mapped_column(
    BigInteger,
    ForeignKey("clientes.id", ondelete="SET NULL"),  # ← descomentar
    nullable=True,
)
```

### 4. Verificar que `pgcrypto` está habilitado (para `gen_random_uuid()`)

```sql
-- Conectarse a tu BD PostgreSQL
CREATE EXTENSION IF NOT EXISTS pgcrypto;
```

O agrégalo al inicio de la migración:

```python
def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")
    op.create_table(...)
```

### 5. Ejecutar migración

```bash
# Verificar que todo compile
alembic check

# Ver SQL que se ejecutará (recomendado primero)
alembic upgrade --sql head > /tmp/migration.sql
less /tmp/migration.sql

# Aplicar
alembic upgrade head
```

### 6. Activar el middleware en `main.py`

```python
# backend/app/main.py
from fastapi import FastAPI
from app.middleware.audit_calculos import AuditoriaCalculosMiddleware

app = FastAPI()

# IMPORTANTE: agregar DESPUÉS del middleware de autenticación
app.add_middleware(AuditoriaCalculosMiddleware)
```

---

## ✅ Verificación

```bash
# Tabla creada
psql $DATABASE_URL -c "\d calculos_fiscales"

# Hacer un cálculo desde el frontend o curl
curl -X POST http://localhost:8000/api/v2/calc/isr-pf \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"ingresos_mensuales": 20000, "regimen": "sueldos"}'

# Verificar que se registró
psql $DATABASE_URL -c "SELECT id, tipo_calculo, monto_principal, creado_en FROM calculos_fiscales ORDER BY id DESC LIMIT 5;"
```

---

## 🔍 Ejemplos de uso

### Listar cálculos de un cliente

```python
from app.repositories.calculo_fiscal_repository import CalculoFiscalRepository

with SessionLocal() as db:
    repo = CalculoFiscalRepository(db)
    calculos = repo.listar_por_cliente(
        cliente_id=42,
        tipo_calculo="nomina",
        desde=datetime(2025, 1, 1),
        limit=20,
    )
    for c in calculos:
        print(f"{c.creado_en} - {c.rfc_contribuyente} - ${c.monto_principal}")
```

### Estadísticas para dashboard

```python
estadisticas = repo.estadisticas_por_tipo(cliente_id=42, ejercicio=2025)
# [
#   {"tipo": "nomina", "total": 150, "monto_total": 4500000.00},
#   {"tipo": "iva", "total": 12, "monto_total": 234000.00},
#   ...
# ]
```

### Endpoint para mostrar histórico al usuario

```python
# backend/app/api/routes/auditoria.py
from fastapi import APIRouter, Depends
from app.repositories.calculo_fiscal_repository import CalculoFiscalRepository

router = APIRouter(prefix="/api/v2/auditoria", tags=["Auditoría"])

@router.get("/mis-calculos")
async def mis_calculos(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    repo = CalculoFiscalRepository(db)
    calculos = repo.listar_por_usuario(user_id, ultimos_dias=90, limit=100)
    return {"calculos": [c.to_dict() for c in calculos]}
```

---

## 🛡️ Características de seguridad

✅ **Trigger anti-modificación:** Una vez completado un cálculo, no se pueden modificar los datos de entrada/salida (solo archivar).

✅ **UUID público:** El campo `id` es interno; para referencias externas se usa `uuid` (no expone IDs secuenciales).

✅ **Constraints:** `tipo_calculo`, `estado` y `ejercicio_fiscal` con check constraints.

✅ **Auditoría no bloqueante:** Si la persistencia falla, el cálculo se entrega normal al usuario (solo se logea el error).

✅ **IP real con X-Forwarded-For:** Considera proxies/load balancers.

---

## 📊 Schema final

```
calculos_fiscales
─────────────────────────────────────────────────────
id                    BIGINT PK
uuid                  UUID UNIQUE (gen_random_uuid())
cliente_id            BIGINT FK → clientes
usuario_id            BIGINT FK → users (NOT NULL)
tipo_calculo          VARCHAR(50) CHECK
subtipo               VARCHAR(50)
ejercicio_fiscal      SMALLINT CHECK (2020-2050)
periodo               VARCHAR(20)
mes                   SMALLINT
rfc_contribuyente     VARCHAR(13)
rfc_empleador         VARCHAR(13)
nombre_contribuyente  VARCHAR(300)
parametros_entrada    JSONB NOT NULL
resultado             JSONB NOT NULL
fundamento_legal      JSONB
monto_principal       NUMERIC(15,2)
tiene_advertencias    BOOLEAN
creado_en             TIMESTAMPTZ
ip_origen             INET
user_agent            VARCHAR(500)
request_id            VARCHAR(64)
estado                VARCHAR(20) CHECK
notas                 TEXT
─────────────────────────────────────────────────────
ÍNDICES:
  ix_calculos_cliente_fecha    (cliente_id, creado_en DESC) WHERE cliente_id NOT NULL
  ix_calculos_usuario_fecha    (usuario_id, creado_en DESC)
  ix_calculos_rfc              (rfc_contribuyente) WHERE NOT NULL
  ix_calculos_tipo_ejercicio   (tipo, ejercicio, fecha)
  ix_calculos_resultado_gin    (resultado USING gin)
  ix_calculos_uuid             (uuid UNIQUE)

TRIGGER:
  tr_calculos_fiscales_audit   Bloquea modificación de parametros/resultado

CONSTRAINTS:
  ck_calculos_tipo_valido      tipo IN ('isr_pf','isr_pm','iva','ieps','imss','nomina','finiquito')
  ck_calculos_estado_valido    estado IN ('completado','error','archivado')
  ck_calculos_ejercicio_rango  ejercicio BETWEEN 2020 AND 2050
```

---

## 🔄 Reversa (rollback)

```bash
# Ver migraciones aplicadas
alembic history

# Revertir la última
alembic downgrade -1

# Revertir todas hasta una específica
alembic downgrade <revision>
```

El downgrade elimina:
1. El trigger `tr_calculos_fiscales_audit`
2. La función `fn_calculos_fiscales_audit()`
3. La tabla completa

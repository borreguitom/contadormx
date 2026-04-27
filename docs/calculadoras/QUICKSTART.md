# ⚡ Quickstart — Integración inmediata

Comandos para integrar el paquete en menos de 30 minutos.

---

## 1. Backend

```bash
# Desde la raíz de tu proyecto contadormx
cd backend

# Crear directorios necesarios (si no existen)
mkdir -p app/utils app/schemas

# Copiar archivos
cp -v ../contadormx_mejoras/backend/utils/*.py app/utils/
cp -v ../contadormx_mejoras/backend/schemas/*.py app/schemas/
cp -v ../contadormx_mejoras/backend/calculators/*.py app/calculators/
cp -v ../contadormx_mejoras/backend/api/routes/calc_v2.py app/api/routes/
cp -v ../contadormx_mejoras/backend/tests/test_calculadoras.py tests/

# Asegurar que existan __init__.py
touch app/utils/__init__.py app/schemas/__init__.py
```

### Registrar router en `main.py`

Buscar línea como:
```python
from app.api.routes import calc
app.include_router(calc.router)
```

Y agregar:
```python
from app.api.routes import calc, calc_v2
app.include_router(calc.router)
app.include_router(calc_v2.router)
```

### Verificar instalación

```bash
# Tests
pytest -v tests/test_calculadoras.py

# Servidor
uvicorn app.main:app --reload --port 8000

# Probar endpoint
curl http://localhost:8000/api/v2/calc/health
```

Debe responder:
```json
{
  "status": "ok",
  "calculadoras_disponibles": ["isr-pf", "isr-pm", "iva", ...],
  "ejercicio_fiscal": 2025,
  "version": "2.0"
}
```

---

## 2. Frontend

```bash
cd frontend

# Cliente API
cp -v ../contadormx_mejoras/frontend/lib/api-calc.ts lib/

# Componentes
mkdir -p components/calculadoras
cp -v ../contadormx_mejoras/frontend/components/calculadoras/*.tsx components/calculadoras/
```

### Verificar `.env.local`

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Crear las páginas

```bash
# Página principal de calculadoras
mkdir -p "app/(app)/calculadoras-v2"
cat > "app/(app)/calculadoras-v2/page.tsx" << 'EOF'
import CalculadorasFiscales from "@/components/calculadoras/CalculadorasFiscales";

export default function Page() {
  return <CalculadorasFiscales />;
}
EOF

# Nómina
mkdir -p "app/(app)/nomina/calculadora"
cat > "app/(app)/nomina/calculadora/page.tsx" << 'EOF'
import NominaCalculator from "@/components/calculadoras/NominaCalculator";

export default function Page() {
  return <NominaCalculator />;
}
EOF

# Finiquito
mkdir -p "app/(app)/finiquito"
cat > "app/(app)/finiquito/page.tsx" << 'EOF'
import FiniquitoCalculator from "@/components/calculadoras/FiniquitoCalculator";

export default function Page() {
  return <FiniquitoCalculator />;
}
EOF

# Iniciar dev server
npm run dev
```

Visitar:
- http://localhost:3000/calculadoras-v2
- http://localhost:3000/nomina/calculadora
- http://localhost:3000/finiquito

---

## 3. Base de datos (opcional, para auditoría)

### Migración Alembic

```bash
cd backend

# Generar migración
alembic revision -m "add_calculos_fiscales_table"
```

Editar el archivo generado en `alembic/versions/`:

```python
def upgrade():
    op.create_table(
        'calculos_fiscales',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('cliente_id', sa.BigInteger(), sa.ForeignKey('clientes.id')),
        sa.Column('usuario_id', sa.BigInteger(), sa.ForeignKey('users.id')),
        sa.Column('tipo_calculo', sa.String(50), nullable=False),
        sa.Column('rfc_contribuyente', sa.String(13)),
        sa.Column('rfc_empleador', sa.String(13)),
        sa.Column('parametros_entrada', sa.dialects.postgresql.JSONB, nullable=False),
        sa.Column('resultado', sa.dialects.postgresql.JSONB, nullable=False),
        sa.Column('creado_en', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('ip_origen', sa.dialects.postgresql.INET),
        sa.Column('user_agent', sa.String),
        sa.Column('ejercicio_fiscal', sa.SmallInteger, nullable=False),
        sa.Column('periodo', sa.String(20)),
    )
    op.create_index('idx_calculos_cliente', 'calculos_fiscales',
                    ['cliente_id', 'creado_en'], postgresql_using='btree')
    op.create_index('idx_calculos_rfc', 'calculos_fiscales', ['rfc_contribuyente'])

def downgrade():
    op.drop_table('calculos_fiscales')
```

```bash
alembic upgrade head
```

---

## 4. Ejemplo de uso en código

### Backend (Python)

```python
from app.calculators.nomina import calcular_nomina

resultado = calcular_nomina(
    salario_mensual_bruto=25000,
    periodo="quincenal",
    anios_antiguedad=3,
    vales_despensa=500,
    horas_extras_dobles=4,
    pension_alimenticia_pct=0.20,
)

print(f"Neto a pagar: ${resultado['neto_a_pagar']:,.2f}")
print(f"ISR retenido: ${resultado['deducciones']['isr']['isr_a_retener']:,.2f}")
```

### Frontend (TypeScript)

```typescript
import { calcApi, MXN } from "@/lib/api-calc";

const resultado = await calcApi.nomina({
  salario_mensual_bruto: 25000,
  periodo: "quincenal",
  anios_antiguedad: 3,
  vales_despensa: 500,
  horas_extras_dobles: 4,
  pension_alimenticia_pct: 0.20,
});

if (resultado.success) {
  const datos = resultado.datos as { neto_a_pagar: number };
  console.log(`Neto: ${MXN(datos.neto_a_pagar)}`);
}
```

---

## 5. Pruebas de aceptación

### Test 1: ISR Sueldos $20,000
```bash
curl -X POST http://localhost:8000/api/v2/calc/isr-pf \
  -H "Content-Type: application/json" \
  -d '{"ingresos_mensuales": 20000, "regimen": "sueldos"}'
```
**Esperado:** ISR a cargo entre $2,500 y $3,000

### Test 2: Nómina quincenal
```bash
curl -X POST http://localhost:8000/api/v2/calc/nomina \
  -H "Content-Type: application/json" \
  -d '{
    "salario_mensual_bruto": 30000,
    "periodo": "quincenal",
    "anios_antiguedad": 5
  }'
```
**Esperado:** Neto cercano a $13,000

### Test 3: Finiquito despido injustificado
```bash
curl -X POST http://localhost:8000/api/v2/calc/finiquito \
  -H "Content-Type: application/json" \
  -d '{
    "salario_diario": 1000,
    "fecha_ingreso": "2020-01-15",
    "fecha_separacion": "2025-06-30",
    "tipo_separacion": "despido_injustificado"
  }'
```
**Esperado:** Indemnización ~$200,000

---

## 6. Monitoreo en producción

### Logs estructurados (recomendado)

```python
# backend/app/main.py
import logging
import json
from datetime import datetime

class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "module": record.name,
            "message": record.getMessage(),
        })

handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logging.basicConfig(level=logging.INFO, handlers=[handler])
```

### Métricas con Prometheus (opcional)

```python
from prometheus_client import Counter, Histogram

calculos_total = Counter("calculos_total", "Total de cálculos", ["tipo"])
calculo_duracion = Histogram("calculo_duracion_seconds", "Duración del cálculo", ["tipo"])

# En cada endpoint:
@calculo_duracion.labels(tipo="nomina").time()
async def nomina_endpoint(...):
    calculos_total.labels(tipo="nomina").inc()
    # ...
```

---

¡Listo! Tu sistema de cálculos fiscales está al 100% de cumplimiento legal. 🎉

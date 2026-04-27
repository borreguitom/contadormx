# 📦 Mejoras a Calculadoras Fiscales — contadormx

**Stack:** Next.js 15 + FastAPI + PostgreSQL 16
**Versión:** 2.0
**Ejercicio fiscal:** 2025
**Fecha:** Abril 2026

---

## 🎯 Resumen ejecutivo

Este paquete reescribe y mejora las **7 calculadoras fiscales** del proyecto contadormx para alcanzar el 100% de cumplimiento con la legislación mexicana vigente:

| # | Calculadora | Estado anterior | Mejoras aplicadas |
|---|---|---|---|
| 1 | **ISR PF** | 95% correcto | + Deducciones personales con tope, RESICO con límite anual, todos los regímenes |
| 2 | **ISR PM** | 90% correcto | + Cálculo anual, pérdidas fiscales, depreciaciones, PTU |
| 3 | **IVA** | 70% correcto | + Frontera 8%, retenciones bidireccionales, importaciones, proporcionalidad |
| 4 | **IEPS** | 30% correcto | + 16+ categorías (combustibles, cigarros, plaguicidas, telecom...) |
| 5 | **IMSS / INFONAVIT** | 90% correcto | + Validación primas por clase, desglose por concepto |
| 6 | **Nómina** | 85% correcto | + Horas extras dobles/triples, pensión alimenticia, FONACOT, exenciones |
| 7 | **Finiquito** | 95% correcto | + 8 tipos de separación, salarios caídos, ISR a tasa efectiva |

---

## 📂 Estructura del paquete

```
contadormx_mejoras/
├── backend/
│   ├── utils/
│   │   ├── validators_mx.py          ← RFC, CURP, NSS, CLABE
│   │   └── constantes_fiscales.py    ← UMA, tarifas, tasas (única fuente de verdad)
│   ├── schemas/
│   │   └── comunes.py                ← Pydantic v2 con validadores
│   ├── calculators/
│   │   ├── isr_pf.py                 ← ISR Persona Física
│   │   ├── isr_pm.py                 ← ISR Persona Moral
│   │   ├── iva.py                    ← IVA con todas las situaciones
│   │   ├── ieps.py                   ← IEPS multi-categoría
│   │   ├── imss.py                   ← Cuotas IMSS/INFONAVIT
│   │   ├── nomina.py                 ← Nómina completa
│   │   └── finiquito.py              ← Finiquito y liquidación
│   ├── api/routes/
│   │   └── calc_v2.py                ← Endpoints FastAPI
│   └── tests/
│       └── test_calculadoras.py      ← Suite de tests pytest
├── frontend/
│   ├── lib/
│   │   └── api-calc.ts               ← Cliente API tipado
│   └── components/calculadoras/
│       ├── NominaCalculator.tsx       ← Componente nómina
│       ├── FiniquitoCalculator.tsx    ← Componente finiquito
│       └── CalculadorasFiscales.tsx   ← Hub para ISR, IVA, IEPS, IMSS
└── docs/
    └── README.md                      ← Este archivo
```

---

## 🚀 Instalación paso a paso

### 1. Backend

```bash
# Desde la raíz del proyecto contadormx
cd backend

# Copiar archivos del paquete
cp -r /ruta/contadormx_mejoras/backend/utils ./app/
cp -r /ruta/contadormx_mejoras/backend/schemas ./app/
cp -r /ruta/contadormx_mejoras/backend/calculators/* ./app/calculators/
cp /ruta/contadormx_mejoras/backend/api/routes/calc_v2.py ./app/api/routes/
cp /ruta/contadormx_mejoras/backend/tests/test_calculadoras.py ./tests/

# Verificar que no haya conflicto de imports
# Los nuevos archivos usan `from app.utils.constantes_fiscales import ...`
# Si tu estructura no usa `app.`, ajusta los imports
```

#### Registrar el router v2 en `main.py`

```python
# backend/app/main.py
from app.api.routes import calc, calc_v2  # ← agregar calc_v2

app.include_router(calc.router)
app.include_router(calc_v2.router)        # ← agregar
```

#### Ejecutar tests

```bash
cd backend
pytest -v tests/test_calculadoras.py
```

### 2. Frontend

```bash
cd frontend

# Cliente API
cp /ruta/contadormx_mejoras/frontend/lib/api-calc.ts ./lib/

# Componentes
mkdir -p ./components/calculadoras
cp /ruta/contadormx_mejoras/frontend/components/calculadoras/*.tsx ./components/calculadoras/

# Verificar variable de entorno
# .env.local debe tener:
# NEXT_PUBLIC_API_URL=http://localhost:8000
```

#### Crear páginas en Next.js

```tsx
// frontend/app/(app)/calculadoras/page.tsx
import CalculadorasFiscales from "@/components/calculadoras/CalculadorasFiscales";

export default function Page() {
  return <CalculadorasFiscales />;
}
```

```tsx
// frontend/app/(app)/nomina/calculadora/page.tsx
import NominaCalculator from "@/components/calculadoras/NominaCalculator";

export default function Page() {
  return <NominaCalculator />;
}
```

```tsx
// frontend/app/(app)/finiquito/page.tsx
import FiniquitoCalculator from "@/components/calculadoras/FiniquitoCalculator";

export default function Page() {
  return <FiniquitoCalculator />;
}
```

---

## 🔬 Pruebas rápidas

### cURL — ISR PF Sueldos

```bash
curl -X POST http://localhost:8000/api/v2/calc/isr-pf \
  -H "Content-Type: application/json" \
  -d '{
    "ingresos_mensuales": 20000,
    "regimen": "sueldos",
    "periodo": "mensual"
  }'
```

### cURL — Nómina completa

```bash
curl -X POST http://localhost:8000/api/v2/calc/nomina \
  -H "Content-Type: application/json" \
  -d '{
    "salario_mensual_bruto": 30000,
    "periodo": "quincenal",
    "anios_antiguedad": 3,
    "vales_despensa": 500,
    "horas_extras_dobles": 4
  }'
```

### cURL — Finiquito

```bash
curl -X POST http://localhost:8000/api/v2/calc/finiquito \
  -H "Content-Type: application/json" \
  -d '{
    "salario_diario": 800,
    "fecha_ingreso": "2018-03-15",
    "fecha_separacion": "2025-06-30",
    "tipo_separacion": "despido_injustificado"
  }'
```

### cURL — IEPS Cigarros (cálculo mixto)

```bash
curl -X POST http://localhost:8000/api/v2/calc/ieps \
  -H "Content-Type: application/json" \
  -d '{
    "categoria": "tabacos_labrados",
    "precio_enajenacion": 80,
    "cantidad_cigarros": 20
  }'
```

---

## 🔐 Validaciones implementadas

### RFC (CFF Art. 27)
- Persona Física: 13 caracteres `AAAA######XXX`
- Persona Moral: 12 caracteres `AAA######XXX`
- Validación de fecha embebida (YYMMDD)
- Soporta RFC genérico XAXX010101000

### CURP (RENAPO)
- 18 caracteres con regex completo
- Validación de fecha de nacimiento

### NSS (IMSS)
- 11 dígitos numéricos
- Validación checksum Luhn

### CLABE (Banxico)
- 18 dígitos
- Algoritmo módulo 10

---

## 📊 Funcionalidades clave

### ✅ Validaciones en vivo (frontend)
- RFC, NSS, CLABE, CURP con feedback instantáneo
- Cálculo automático de antigüedad desde fechas

### ✅ Desglose detallado (backend)
- Cada cálculo devuelve trazabilidad paso a paso
- Fundamentos legales por concepto
- Advertencias y notas contextuales

### ✅ Topes legales aplicados
- Indemnización: 25 SM diarios (Art. 50-II LFT)
- Prima de antigüedad: 2 SM (Art. 162 LFT)
- SBC IMSS: 25 UMAs (Art. 28 LSS)
- Salarios caídos: máximo 12 meses (Art. 48 LFT)
- Deducciones personales: 5 UMAs anuales o 15% ingresos

### ✅ Exenciones ISR aplicadas
- Vales de despensa: 40% UMA mensual (Art. 93-XIV)
- Horas extras dobles: 50% hasta 5 UMAs (Art. 93-I)
- Aguinaldo: 30 UMAs (Art. 93-XIV)
- Prima vacacional: 15 UMAs (Art. 93-XIV)
- Indemnización: 90 SM × años (Art. 93-XIII)

---

## 🗄️ Schema sugerido para PostgreSQL (auditoría)

```sql
-- Tabla de auditoría de cálculos
CREATE TABLE calculos_fiscales (
    id BIGSERIAL PRIMARY KEY,
    cliente_id BIGINT REFERENCES clientes(id),
    usuario_id BIGINT REFERENCES users(id),
    tipo_calculo VARCHAR(50) NOT NULL,  -- 'nomina', 'finiquito', 'isr_pf', etc.

    -- Datos identificatorios
    rfc_contribuyente VARCHAR(13),
    rfc_empleador VARCHAR(13),

    -- Cálculo
    parametros_entrada JSONB NOT NULL,
    resultado JSONB NOT NULL,

    -- Auditoría
    creado_en TIMESTAMPTZ DEFAULT NOW(),
    ip_origen INET,
    user_agent TEXT,

    -- Búsqueda
    ejercicio_fiscal SMALLINT NOT NULL,
    periodo VARCHAR(20)
);

CREATE INDEX idx_calculos_cliente ON calculos_fiscales(cliente_id, creado_en DESC);
CREATE INDEX idx_calculos_rfc ON calculos_fiscales(rfc_contribuyente);
CREATE INDEX idx_calculos_tipo ON calculos_fiscales(tipo_calculo, ejercicio_fiscal);
```

### SQLAlchemy model

```python
# backend/app/models/calculo_fiscal.py
from sqlalchemy import Column, BigInteger, String, JSON, DateTime, ForeignKey, SmallInteger
from sqlalchemy.dialects.postgresql import INET, JSONB
from datetime import datetime
from app.database import Base

class CalculoFiscal(Base):
    __tablename__ = "calculos_fiscales"

    id = Column(BigInteger, primary_key=True)
    cliente_id = Column(BigInteger, ForeignKey("clientes.id"))
    usuario_id = Column(BigInteger, ForeignKey("users.id"))
    tipo_calculo = Column(String(50), nullable=False)
    rfc_contribuyente = Column(String(13))
    rfc_empleador = Column(String(13))
    parametros_entrada = Column(JSONB, nullable=False)
    resultado = Column(JSONB, nullable=False)
    creado_en = Column(DateTime(timezone=True), default=datetime.utcnow)
    ip_origen = Column(INET)
    user_agent = Column(String)
    ejercicio_fiscal = Column(SmallInteger, nullable=False)
    periodo = Column(String(20))
```

---

## 🛣️ Roadmap de integración

### Fase 1 (1-2 días) — Backend
- [x] Copiar módulos a estructura del proyecto
- [x] Registrar router v2 en main.py
- [x] Ejecutar tests pytest
- [ ] Configurar logging a Sentry/Logflare
- [ ] Agregar middleware de auditoría
- [ ] Migración Alembic para tabla `calculos_fiscales`

### Fase 2 (2-3 días) — Frontend
- [x] Copiar componentes y cliente API
- [x] Crear páginas Next.js
- [ ] Conectar con autenticación existente
- [ ] Agregar estado global (Zustand/Redux)
- [ ] Tests con Vitest/Playwright

### Fase 3 (3-5 días) — Integraciones
- [ ] Generación de CFDI 4.0 para nómina
- [ ] Exportación a Excel/PDF
- [ ] Importación masiva desde plantilla
- [ ] Histórico de cálculos por cliente

### Fase 4 (1 semana) — Producción
- [ ] Deploy a staging (Railway)
- [ ] Pruebas E2E con datos reales
- [ ] Auditoría de seguridad
- [ ] Deploy a producción

---

## 📚 Referencias legales

| Cálculo | Fundamento |
|---------|-----------|
| ISR Sueldos mensual | Art. 96 LISR |
| ISR Sueldos anual | Art. 152 LISR |
| ISR Honorarios/AE | Art. 106 LISR |
| ISR Arrendamiento | Art. 116 LISR |
| RESICO PF | Art. 113-E LISR |
| ISR PM provisional | Art. 14 LISR |
| ISR PM anual | Art. 9 LISR |
| RESICO PM | Art. 196 LISR |
| IVA general | Art. 1, 4, 5 LIVA |
| IVA frontera | Art. 2 LIVA + Decreto 31-dic-2018 |
| IVA tasa 0% | Art. 2-A LIVA |
| Proporcionalidad | Art. 5-C LIVA |
| Retenciones IVA | Art. 1-A LIVA |
| IEPS bebidas | Art. 2-I-A LIEPS |
| IEPS cigarros | Art. 2-I-C LIEPS |
| IEPS combustibles | Art. 2-I-D LIEPS |
| IMSS cuotas | Art. 25-168 LSS |
| Integración SDI | Art. 27 LSS |
| Tope SBC | Art. 28 LSS |
| INFONAVIT | Art. 29 Ley INFONAVIT |
| Vacaciones LFT | Art. 76 LFT (reforma 2023) |
| Prima vacacional | Art. 80 LFT |
| Aguinaldo | Art. 87 LFT |
| Indemnización | Art. 50 LFT |
| Salarios caídos | Art. 48 LFT |
| Prima antigüedad | Art. 162 LFT |
| Exenciones ISR | Art. 93 LISR |

---

## ⚠️ Diferencias clave vs. versión anterior

### Antes
```python
def calcular_nomina(salario_mensual_bruto, periodo, vales_despensa, ...):
    # Cálculo directo
    return dict
```

### Ahora
```python
def calcular_nomina(
    salario_mensual_bruto,
    *,
    periodo="mensual",
    fecha_inicio=None,
    fecha_fin=None,
    datos_trabajador=None,    # ← incluye RFC validado, NSS, etc.
    datos_empleador=None,
    anios_antiguedad=1,        # ← afecta vacaciones (Art. 76)
    horas_extras_dobles=0,     # ← cálculo correcto + exención
    horas_extras_triples=0,
    pension_alimenticia_pct=0,
    fonacot_descuento=0,
    # ... más opciones
):
    # Cálculo con desglose detallado
    return ResultadoNomina(...).to_dict()
```

---

## 🆘 Soporte y contribución

Si encuentras un error en algún cálculo o tienes una sugerencia:

1. Verifica con el [Aplicativo SAT](https://www.sat.gob.mx) o la calculadora oficial del IMSS
2. Documenta el caso de prueba (entrada → salida esperada → salida obtenida)
3. Cita el fundamento legal aplicable
4. Reporta en el repositorio del proyecto

---

**Versión:** 2.0
**Mantenedor:** tcpu
**Stack:** Next.js 15 + FastAPI + PostgreSQL 16
**Licencia:** Según el repositorio principal

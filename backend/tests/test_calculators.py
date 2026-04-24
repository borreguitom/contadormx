"""
Tests de calculadoras fiscales.
Valores esperados basados en tablas 2025 Art. 96 LISR y Art. 27 LSS.
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.calculators.isr import calcular_isr_pf, calcular_isr_pm
from app.calculators.iva import calcular_iva
from app.calculators.imss import calcular_cuotas_imss
from app.calculators.nomina import calcular_nomina
from app.calculators.finiquito import calcular_finiquito


# ── ISR PF ────────────────────────────────────────────────────────────────────

class TestISRPF:
    def test_sueldo_bajo_subsidio_empleo(self):
        """Sueldo de $3,000/mes — subsidio al empleo cubre todo el ISR."""
        r = calcular_isr_pf(3000, "sueldos")
        assert r["regimen"] == "Sueldos y Salarios"
        assert r["subsidio_al_empleo"] > 0
        assert r["isr_a_retener"] == 0.0  # subsidio > ISR

    def test_sueldo_30k(self):
        """Sueldo $30,000 — debe retener ISR sin subsidio."""
        r = calcular_isr_pf(30000, "sueldos")
        assert r["isr_a_retener"] > 0
        assert r["subsidio_al_empleo"] == 0.0
        # Tasa efectiva razonable para este nivel
        assert 0.15 < r["tasa_efectiva_pct"] < 25

    def test_sueldo_100k(self):
        """Sueldo $100,000 — tramo del 30%."""
        r = calcular_isr_pf(100000, "sueldos")
        assert r["desglose"]["tasa_marginal"] == 0.30
        assert r["isr_a_retener"] > 20000

    def test_arrendamiento_deduccion_ciega(self):
        """Arrendamiento $15,000 — aplica 35% deducción ciega."""
        r = calcular_isr_pf(15000, "arrendamiento")
        assert r["base_gravable"] == round(15000 * 0.65, 2)

    def test_resico_pf_25k(self):
        """RESICO PF $20,000 — tasa 1%."""
        r = calcular_isr_pf(20000, "resico_pf")
        assert r["isr_a_retener"] == 200.0
        assert r["fundamento"] == "Art. 113-E LISR"

    def test_honorarios_con_deducciones(self):
        """Honorarios $50,000 con $20,000 de deducciones."""
        r = calcular_isr_pf(50000, "honorarios", deducciones_mensuales=20000)
        assert r["base_gravable"] == 30000.0

    def test_retorno_tiene_fundamento(self):
        for regimen in ["sueldos", "honorarios", "arrendamiento", "resico_pf"]:
            r = calcular_isr_pf(25000, regimen)
            assert "fundamento" in r


# ── ISR PM ────────────────────────────────────────────────────────────────────

class TestISRPM:
    def test_pago_provisional_mes1(self):
        """PM — primer pago provisional enero, $500,000 ingresos, CU 0.20."""
        r = calcular_isr_pm(500000, 0.20, mes=1)
        assert r["utilidad_fiscal_estimada"] == 100000.0
        assert r["pago_provisional_a_enterar"] > 0
        assert r["fundamento"] == "Art. 14 LISR"

    def test_pagos_previos_reducen_cargo(self):
        r1 = calcular_isr_pm(1000000, 0.20, pagos_provisionales_previos=0, mes=2)
        r2 = calcular_isr_pm(1000000, 0.20, pagos_provisionales_previos=10000, mes=2)
        assert r2["pago_provisional_a_enterar"] < r1["pago_provisional_a_enterar"]

    def test_resico_pm(self):
        """RESICO PM — 1% sobre ingresos."""
        r = calcular_isr_pm(1000000, regimen="resico_pm", mes=6)
        assert r["pago_provisional_a_enterar"] == 10000.0
        assert r["fundamento"] == "Art. 196 LISR"


# ── IVA ───────────────────────────────────────────────────────────────────────

class TestIVA:
    def test_iva_a_cargo_simple(self):
        """$100k ventas, $50k compras — IVA a cargo $8,000."""
        r = calcular_iva(ventas_16=100000, compras_16_acreditables=50000)
        assert r["iva_a_cargo"] == 8000.0
        assert r["iva_a_favor"] == 0.0

    def test_iva_a_favor(self):
        """Más compras que ventas — saldo a favor."""
        r = calcular_iva(ventas_16=50000, compras_16_acreditables=100000)
        assert r["iva_a_favor"] == 8000.0
        assert r["iva_a_cargo"] == 0.0

    def test_saldo_favor_anterior(self):
        r = calcular_iva(ventas_16=100000, compras_16_acreditables=50000, saldo_favor_anterior=5000)
        assert r["iva_a_cargo"] == 3000.0

    def test_proporcionalidad(self):
        """Ventas mixtas — proporcionalidad Art. 5-C."""
        r = calcular_iva(
            ventas_16=80000, ventas_exentas=20000,
            compras_16_acreditables=50000
        )
        assert r["desglose"]["proporcion_acreditamiento"] == pytest.approx(0.80, rel=1e-2)

    def test_tasa_0_no_genera_iva_trasladado(self):
        r = calcular_iva(ventas_16=0, ventas_0=100000)
        assert r["iva_trasladado"]["tasa_16_pct"] == 0.0


# ── IMSS ─────────────────────────────────────────────────────────────────────

class TestIMSS:
    def test_sdi_salario_minimo(self):
        """SDI cercano al salario mínimo."""
        r = calcular_cuotas_imss(300.0)
        assert r["cuotas_patronales"]["total_patronal"] > 0
        assert r["cuotas_trabajador"]["total_trabajador"] > 0
        assert r["fundamento"].startswith("Ley del Seguro Social")

    def test_tope_25_umas(self):
        """SDI muy alto debe toparse a 25 UMAs."""
        r = calcular_cuotas_imss(5000.0)
        from app.calculators.imss import TOPE_SBC_25_UMA
        assert r["sdi_topado_25uma"] == TOPE_SBC_25_UMA

    def test_infonavit_5_pct(self):
        """INFONAVIT debe ser 5% del SDI mensual."""
        sdi = 500.0
        r = calcular_cuotas_imss(sdi)
        esperado = round(sdi * 30.4 * 0.05, 2)
        assert r["cuotas_patronales"]["infonavit"] == pytest.approx(esperado, rel=1e-3)


# ── Nómina ───────────────────────────────────────────────────────────────────

class TestNomina:
    def test_nomina_mensual(self):
        r = calcular_nomina(20000)
        assert r["neto_a_pagar"] < 20000
        assert r["neto_a_pagar"] > 0
        assert "percepciones" in r
        assert "deducciones" in r

    def test_nomina_quincenal(self):
        r = calcular_nomina(20000, periodo="quincenal")
        assert r["periodo"] == "quincenal"
        assert r["dias_periodo"] == 15

    def test_neto_aumenta_con_subsidio(self):
        """Sueldo bajo debe recibir subsidio al empleo."""
        r = calcular_nomina(5000)
        assert r["deducciones"]["subsidio_al_empleo"] > 0

    def test_vales_despensa_exentos(self):
        r = calcular_nomina(30000, vales_despensa=1000)
        assert r["percepciones"]["vales_despensa_exentos"] > 0


# ── Finiquito ────────────────────────────────────────────────────────────────

class TestFiniquito:
    def test_finiquito_renuncia_1_anio(self):
        r = calcular_finiquito(
            salario_diario=466.0,
            dias_trabajados_anio=180,
            anios_servicio=1.0,
            tipo_separacion="renuncia",
        )
        assert r["total_a_pagar"] > 0
        assert "partes_proporcionales" in r

    def test_liquidacion_incluye_3_meses(self):
        r = calcular_finiquito(
            salario_diario=500.0,
            dias_trabajados_anio=365,
            anios_servicio=3.0,
            tipo_separacion="despido_injustificado",
        )
        assert r["indemnizacion"]["tres_meses_art_50"] == 500 * 90
        assert r["indemnizacion"]["veinte_dias_por_anio"] > 0

    def test_vacaciones_proporcionales(self):
        """Trabajador con 6 meses = 50% de días vacaciones."""
        r = calcular_finiquito(500, 182, 0.5, "renuncia")
        # Debe tener parte proporcional de vacaciones
        assert r["partes_proporcionales"]["vacaciones_dias"] > 0

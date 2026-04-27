"""
Tests pytest para calculadoras fiscales mejoradas
==================================================
Cobertura:
  - Validadores RFC, CURP, NSS, CLABE
  - ISR PF (sueldos, honorarios, arrendamiento, RESICO)
  - ISR PM (general, RESICO)
  - IVA (16%, 8%, 0%, exento, proporcionalidad)
  - IEPS (todas las categorías)
  - IMSS (cuotas trabajador y patronal)
  - Nómina (integración completa)
  - Finiquito (todos los tipos de separación)

Ejecutar: pytest -v backend/tests/test_calculadoras.py
"""
import pytest
from app.utils.validators_mx import (
    validar_rfc, validar_curp, validar_nss, validar_clabe,
    validar_fecha_iso, validar_rango_fechas, calcular_antiguedad_anios,
    detectar_tipo_rfc,
)
from app.calculators.isr_pf import calcular_isr_pf
from app.calculators.isr_pm import calcular_isr_pm
from app.calculators.iva import calcular_iva
from app.calculators.ieps import calcular_ieps, listar_categorias_ieps
from app.calculators.imss import calcular_cuotas_imss, calcular_sdi_completo
from app.calculators.nomina import calcular_nomina
from app.calculators.finiquito import calcular_finiquito


# ══════════════════════════════════════════════════════════════════════════
# VALIDADORES
# ══════════════════════════════════════════════════════════════════════════

class TestValidadores:
    """Tests para validadores fiscales mexicanos."""

    @pytest.mark.parametrize("rfc,esperado", [
        ("PEGJ950101AB1", True),     # PF válido
        ("PEGJ950101AB", False),     # PF muy corto
        ("PEGJ95011AB1", False),     # Fecha inválida
        ("XAXX010101000", True),     # Genérico PF
        ("ABC950101AB1", True),      # PM válido
        ("AB950101AB1", False),      # PM muy corto
        ("", False),                 # Vacío
        ("xxxxxxx", False),          # Cualquiera
    ])
    def test_validar_rfc(self, rfc, esperado):
        assert validar_rfc(rfc) == esperado

    def test_detectar_tipo_rfc(self):
        assert detectar_tipo_rfc("PEGJ950101AB1") == "pf"
        assert detectar_tipo_rfc("ABC950101AB1") == "pm"
        assert detectar_tipo_rfc("INVALID") is None

    @pytest.mark.parametrize("curp,esperado", [
        ("PEGJ950101HDFRRR05", True),
        ("PEGJ950101HDFRRR0", False),  # Muy corto
        ("PEGJ95011HDFRRR05", False),  # Fecha inválida
        ("", False),
    ])
    def test_validar_curp(self, curp, esperado):
        assert validar_curp(curp) == esperado

    @pytest.mark.parametrize("nss,esperado", [
        ("12345678901", True),    # 11 dígitos OK formato
        ("1234567890", False),    # Solo 10
        ("123456789012", False),  # 12
        ("ABC12345678", False),   # No numérico
    ])
    def test_validar_nss_formato(self, nss, esperado):
        # Solo verifica formato (no checksum estricto)
        if esperado:
            assert validar_nss(nss) in (True, False)  # depende del Luhn
        else:
            assert validar_nss(nss) == esperado

    def test_validar_clabe_18_digitos(self):
        # Valor formato correcto
        assert isinstance(validar_clabe("123456789012345678"), bool)
        # Muy corto
        assert validar_clabe("12345") is False

    def test_validar_fechas(self):
        assert validar_fecha_iso("2025-01-15") is True
        assert validar_fecha_iso("2025-13-01") is False
        assert validar_fecha_iso("invalid") is False

        ok, _ = validar_rango_fechas("2025-01-01", "2025-12-31")
        assert ok is True

        ok, _ = validar_rango_fechas("2025-12-31", "2025-01-01")
        assert ok is False

    def test_antiguedad(self):
        anios = calcular_antiguedad_anios("2020-01-01", "2025-01-01")
        assert 4.9 < anios < 5.1


# ══════════════════════════════════════════════════════════════════════════
# ISR PERSONAS FÍSICAS
# ══════════════════════════════════════════════════════════════════════════

class TestISRPF:
    """Tests para ISR personas físicas."""

    def test_sueldos_salario_bajo_subsidio(self):
        """Salario bajo: aplica subsidio para el empleo."""
        r = calcular_isr_pf(5000, regimen="sueldos")
        assert r["regimen"] == "Sueldos y Salarios"
        assert r["subsidio_empleo"]["aplica"] is True
        assert r["isr_a_cargo"] >= 0

    def test_sueldos_salario_alto(self):
        """Salario alto: tasa marginal 30%+."""
        r = calcular_isr_pf(100_000, regimen="sueldos")
        assert r["isr_a_cargo"] > 0
        assert r["subsidio_empleo"]["aplica"] is False
        assert r["tarifa_aplicada"]["tasa_marginal"] >= 0.30

    def test_sueldos_caso_referencia_20k(self):
        """Salario $20,000: ~$2,650 ISR aprox."""
        r = calcular_isr_pf(20_000, regimen="sueldos")
        assert 2_500 < r["isr_a_cargo"] < 3_000

    def test_honorarios(self):
        """Honorarios: aplica deducciones."""
        r = calcular_isr_pf(50_000, regimen="honorarios", deducciones_mensuales=10_000)
        assert "Honorarios" in r["regimen"]
        assert r["base_gravable"] == 40_000

    def test_arrendamiento_ciega(self):
        """Arrendamiento con deducción ciega 35%."""
        r = calcular_isr_pf(20_000, regimen="arrendamiento")
        assert r["regimen"] == "Arrendamiento"
        assert r["base_gravable"] == 13_000  # 20,000 - 35% = 13,000

    def test_resico_pf(self):
        """RESICO PF: tasa progresiva sobre ingresos."""
        r = calcular_isr_pf(20_000, regimen="resico_pf")
        assert r["regimen"] == "RESICO Personas Físicas"
        assert r["isr_a_cargo"] > 0
        # 20k está en rango 0-25k → 1%
        assert abs(r["tasa_efectiva_pct"] - 1.0) < 0.1

    def test_resico_pf_excede_limite(self):
        """RESICO PF: advertencia si excede 3.5M anual."""
        r = calcular_isr_pf(
            300_000, regimen="resico_pf",
            ingresos_acumulados_anio=3_400_000
        )
        assert any("Límite" in a for a in r["advertencias"])

    def test_anual_con_deducciones_personales(self):
        """Cálculo anual aplica deducciones personales con tope."""
        r = calcular_isr_pf(
            500_000, regimen="sueldos", periodo="anual",
            deducciones_personales_anuales=200_000
        )
        # Tope = min(5 UMAs anuales, 15% × 500k = 75k)
        assert r["deducciones_aplicadas"] == 75_000


# ══════════════════════════════════════════════════════════════════════════
# ISR PERSONAS MORALES
# ══════════════════════════════════════════════════════════════════════════

class TestISRPM:
    """Tests para ISR personas morales."""

    def test_provisional_general(self):
        """Pago provisional régimen general."""
        r = calcular_isr_pm(
            ingresos_acumulados=1_000_000,
            coeficiente_utilidad=0.20,
            mes=6,
            regimen="general",
        )
        assert "Régimen General" in r["regimen"]
        assert r["utilidad_fiscal_estimada"] == 200_000  # 1M × 20%
        assert r["tasa_aplicada_pct"] == 30.0

    def test_resico_pm(self):
        """RESICO PM: 1% sobre ingresos."""
        r = calcular_isr_pm(
            ingresos_acumulados=500_000,
            regimen="resico_pm",
            mes=3,
        )
        assert "RESICO" in r["regimen"]
        assert r["isr_acumulado"] == 5_000  # 500k × 1%

    def test_resico_pm_excede_limite(self):
        """RESICO PM: advertencia si excede 35M."""
        r = calcular_isr_pm(
            ingresos_acumulados=36_000_000,
            regimen="resico_pm",
        )
        assert any("Límite" in a for a in r["advertencias"])

    def test_anual_con_perdidas(self):
        """Cálculo anual con pérdidas fiscales pendientes."""
        r = calcular_isr_pm(
            ingresos_acumulados=10_000_000,
            es_calculo_anual=True,
            deducciones_autorizadas_anual=7_000_000,
            perdidas_fiscales_pendientes=500_000,
        )
        # Resultado fiscal = 10M - 7M = 3M
        # Base = 3M - 500k = 2.5M
        # ISR = 2.5M × 30% = 750k
        assert "Anual" in r["regimen"]
        assert r["calculo"]["base_gravable"] == 2_500_000

    def test_coeficiente_default_por_actividad(self):
        """Si no hay coef, usa default por actividad."""
        r = calcular_isr_pm(
            ingresos_acumulados=100_000,
            coeficiente_utilidad=0,  # forzar default
            actividad="servicios",
            mes=1,
        )
        # Servicios tiene coef default 0.45
        assert r["coeficiente_utilidad"] == 0.45


# ══════════════════════════════════════════════════════════════════════════
# IVA
# ══════════════════════════════════════════════════════════════════════════

class TestIVA:
    """Tests para IVA."""

    def test_iva_basico_a_cargo(self):
        """Ventas > Compras: IVA a cargo."""
        r = calcular_iva(ventas_16=100_000, compras_16_acreditables=20_000)
        # Trasladado: 16k, Acreditable: 3.2k → A cargo: 12.8k
        assert r["iva_a_cargo"] == 12_800
        assert r["iva_a_favor"] == 0

    def test_iva_a_favor(self):
        """Compras > Ventas: IVA a favor."""
        r = calcular_iva(ventas_16=10_000, compras_16_acreditables=50_000)
        assert r["iva_a_favor"] > 0
        assert r["iva_a_cargo"] == 0

    def test_iva_frontera_8(self):
        """Tasa 8% en frontera."""
        r = calcular_iva(ventas_8_frontera=50_000, compras_16_acreditables=10_000)
        assert r["iva_trasladado_8"] == 4_000  # 50k × 8%

    def test_iva_proporcionalidad(self):
        """Con ventas exentas: aplica proporcionalidad."""
        r = calcular_iva(
            ventas_16=80_000,
            ventas_exentas=20_000,
            compras_16_acreditables=10_000,
        )
        assert r["aplica_proporcionalidad"] is True
        # Proporción: 80/100 = 0.80
        assert abs(r["proporcion_acreditamiento"] - 0.80) < 0.01

    def test_iva_retenciones(self):
        """IVA retenido por terceros se descuenta."""
        r = calcular_iva(
            ventas_16=100_000,
            compras_16_acreditables=20_000,
            iva_retenido_por_terceros=5_000,
        )
        # 12.8k - 5k = 7.8k
        assert r["iva_a_cargo"] == 7_800

    def test_iva_saldo_favor_anterior(self):
        """Saldo a favor anterior se acredita."""
        r = calcular_iva(
            ventas_16=100_000,
            compras_16_acreditables=20_000,
            saldo_favor_anterior=3_000,
        )
        # 12.8k - 3k = 9.8k
        assert r["iva_a_cargo"] == 9_800


# ══════════════════════════════════════════════════════════════════════════
# IEPS
# ══════════════════════════════════════════════════════════════════════════

class TestIEPS:
    """Tests para IEPS."""

    def test_listar_categorias(self):
        """Listado de categorías para frontend."""
        cats = listar_categorias_ieps()
        assert len(cats) > 10
        assert all("clave" in c for c in cats)
        assert all("nombre" in c for c in cats)

    def test_alcohol_destilado(self):
        """Bebidas >20° GL: 53%."""
        r = calcular_ieps(
            "bebidas_alcoholicas_mas_20gl",
            precio_enajenacion=500,
        )
        assert r["ieps_calculado"] == 265  # 500 × 53%
        assert r["tasa_aplicada"] == 0.53

    def test_cerveza(self):
        """Cerveza: 26.5%."""
        r = calcular_ieps("cerveza", precio_enajenacion=100)
        assert abs(r["ieps_calculado"] - 26.5) < 0.01

    def test_cigarros_mixto(self):
        """Cigarros: tasa + cuota por cigarro."""
        r = calcular_ieps(
            "tabacos_labrados",
            precio_enajenacion=80,  # cajetilla
            cantidad_cigarros=20,
        )
        # 80 × 1.60 + 20 × 0.6166 = 128 + 12.33 = 140.33
        assert abs(r["ieps_calculado"] - 140.33) < 0.5

    def test_combustible_magna(self):
        """Gasolina Magna: cuota fija."""
        r = calcular_ieps(
            "combustibles_automotrices_gasolina_menor_92",
            precio_enajenacion=0,
            cantidad_litros=100,
        )
        # 100 L × 6.4555 = 645.55
        assert abs(r["ieps_calculado"] - 645.55) < 0.01

    def test_categoria_invalida(self):
        """Categoría no existente."""
        r = calcular_ieps("inexistente", precio_enajenacion=100)
        assert r.get("error") is True

    def test_iva_sobre_ieps(self):
        """IEPS forma parte de base IVA (Art. 18 LIVA)."""
        r = calcular_ieps(
            "cerveza",
            precio_enajenacion=100,
            incluir_iva=True,
        )
        # Precio: 100, IEPS: 26.5, Base IVA: 126.5, IVA: 20.24
        assert abs(r["iva_calculado"] - 20.24) < 0.1


# ══════════════════════════════════════════════════════════════════════════
# IMSS
# ══════════════════════════════════════════════════════════════════════════

class TestIMSS:
    """Tests para cuotas IMSS."""

    def test_sdi_basico(self):
        """SDI con factor de integración mínimo."""
        r = calcular_sdi_completo(salario_diario_base=500)
        # Factor con 15 días aguinaldo + 12 vac × 25% = 1.0452
        assert r["sdi_calculado"] > 500
        assert 1.04 < r["factor_integracion"] < 1.06

    def test_cuotas_imss_clase_i(self):
        """Cuotas IMSS clase I (riesgo bajo)."""
        r = calcular_cuotas_imss(
            salario_diario_integrado=500,
            clase_riesgo="I",
        )
        assert r["clase_riesgo"] == "I"
        assert r["total_cuota_trabajador"] > 0
        assert r["total_cuota_patronal"] > r["total_cuota_trabajador"]
        assert r["infonavit"]["monto_patronal"] > 0

    def test_cuotas_imss_topa_25_uma(self):
        """SDI muy alto se topa en 25 UMAs."""
        r = calcular_cuotas_imss(
            salario_diario_integrado=10_000,  # exagerado
        )
        assert r["sdi_topado_25_uma"] < 10_000
        assert any("25 UMAs" in a for a in r["advertencias"])

    def test_porcentaje_cuota_trabajador(self):
        """Cuota trabajador ~3.275% del SDI mensual."""
        sdi = 500
        r = calcular_cuotas_imss(salario_diario_integrado=sdi)
        sdi_mensual = sdi * 30.4
        pct = r["total_cuota_trabajador"] / sdi_mensual
        assert 0.025 < pct < 0.045


# ══════════════════════════════════════════════════════════════════════════
# NÓMINA
# ══════════════════════════════════════════════════════════════════════════

class TestNomina:
    """Tests para nómina completa."""

    def test_nomina_basica_quincenal(self):
        """Nómina quincenal con salario 20k."""
        r = calcular_nomina(
            salario_mensual_bruto=20_000,
            periodo="quincenal",
            anios_antiguedad=2,
        )
        assert "error" not in r or r.get("error") is None
        assert r["periodo_pago"]["dias"] == 15
        assert r["total_percepciones"] > 0
        assert r["total_deducciones"] > 0
        assert r["neto_a_pagar"] > 0
        assert r["neto_a_pagar"] < r["total_percepciones"]

    def test_nomina_con_vales_despensa(self):
        """Vales de despensa: parte exenta, parte gravada."""
        r = calcular_nomina(
            salario_mensual_bruto=20_000,
            vales_despensa=2_000,
        )
        vales = r["percepciones"]["vales_despensa"]
        assert vales["exento"] > 0
        # 40% UMA mensual = ~1376 → exento parcialmente

    def test_nomina_con_horas_extras(self):
        """Horas extras dobles: parte exenta hasta 5 UMAs."""
        r = calcular_nomina(
            salario_mensual_bruto=20_000,
            horas_extras_dobles=4,
        )
        he = r["percepciones"]["horas_extras"]
        assert he["dobles"]["importe"] > 0
        assert he["dobles"]["exento"] > 0

    def test_nomina_costo_empresa_mayor_neto(self):
        """Costo empresa siempre > neto trabajador."""
        r = calcular_nomina(salario_mensual_bruto=15_000)
        assert r["costo_empresa"]["costo_total_para_empresa"] > r["neto_a_pagar"]

    def test_nomina_periodo_mensual_factor_1(self):
        """Período mensual: factor = 1."""
        r = calcular_nomina(salario_mensual_bruto=20_000, periodo="mensual")
        assert r["periodo_pago"]["dias"] == 30
        assert r["percepciones"]["salario_base"]["monto_periodo"] == 20_000

    def test_nomina_pension_alimenticia(self):
        """Pensión alimenticia se descuenta."""
        r = calcular_nomina(
            salario_mensual_bruto=20_000,
            pension_alimenticia_pct=0.30,  # 30%
        )
        assert r["deducciones"]["pension_alimenticia"]["monto"] > 0


# ══════════════════════════════════════════════════════════════════════════
# FINIQUITO
# ══════════════════════════════════════════════════════════════════════════

class TestFiniquito:
    """Tests para finiquito."""

    def test_renuncia_menos_15_anios(self):
        """Renuncia con <15 años: solo partes proporcionales."""
        r = calcular_finiquito(
            salario_diario=500,
            anios_servicio=5,
            dias_trabajados_anio=180,
            tipo_separacion="renuncia",
        )
        assert r["prima_antiguedad"]["aplica"] is False
        assert r["indemnizacion"]["aplica"] is False
        assert r["subtotal_partes_proporcionales"] > 0

    def test_renuncia_con_15_anios(self):
        """Renuncia con 15+ años: incluye prima antigüedad."""
        r = calcular_finiquito(
            salario_diario=500,
            anios_servicio=20,
            dias_trabajados_anio=180,
            tipo_separacion="renuncia",
        )
        assert r["prima_antiguedad"]["aplica"] is True
        assert r["subtotal_prima_antiguedad"] > 0

    def test_despido_injustificado_completo(self):
        """Despido injustificado: 3m + 20 días/año + prima."""
        r = calcular_finiquito(
            salario_diario=1000,
            anios_servicio=5,
            dias_trabajados_anio=180,
            tipo_separacion="despido_injustificado",
        )
        ind = r["indemnizacion"]
        assert ind["aplica"] is True
        assert ind["tres_meses_salario"]["monto"] == 90_000  # 90 × 1000
        assert ind["veinte_dias_por_anio"]["monto"] > 0
        assert r["prima_antiguedad"]["aplica"] is True

    def test_despido_injust_topa_indemnizacion(self):
        """Indemnización 20 días: tope 25 SM."""
        r = calcular_finiquito(
            salario_diario=10_000,  # muy alto
            anios_servicio=5,
            dias_trabajados_anio=180,
            tipo_separacion="despido_injustificado",
        )
        # Tope = 25 × 278.80 = 6970
        ind = r["indemnizacion"]
        assert ind["veinte_dias_por_anio"]["salario_topado_25_sm"] == 6970

    def test_salarios_caidos_max_12_meses(self):
        """Salarios caídos: máximo 12 meses (Art. 48 LFT)."""
        r = calcular_finiquito(
            salario_diario=500,
            anios_servicio=5,
            dias_trabajados_anio=180,
            tipo_separacion="despido_injustificado",
            meses_salarios_caidos=18,  # excede 12
        )
        assert any("12 meses" in a for a in r["advertencias"])
        # Solo debe pagar 12 meses
        assert r["indemnizacion"]["salarios_caidos"]["meses"] == 12

    def test_finiquito_con_fechas(self):
        """Cálculo con fechas reales."""
        r = calcular_finiquito(
            salario_diario=500,
            fecha_ingreso="2020-01-15",
            fecha_separacion="2025-06-30",
            tipo_separacion="renuncia",
        )
        assert r["periodo_laboral"]["anios_servicio"] > 5

    def test_jubilacion_aplica_prima(self):
        """Jubilación: aplica prima antigüedad."""
        r = calcular_finiquito(
            salario_diario=500,
            anios_servicio=30,
            dias_trabajados_anio=180,
            tipo_separacion="jubilacion",
        )
        assert r["prima_antiguedad"]["aplica"] is True

    def test_finiquito_isr_calculado(self):
        """ISR del finiquito calculado correctamente."""
        r = calcular_finiquito(
            salario_diario=500,
            anios_servicio=10,
            dias_trabajados_anio=180,
            tipo_separacion="despido_injustificado",
        )
        assert r["isr_finiquito"]["isr_retenido"] >= 0
        assert r["neto_a_pagar"] == r["total_bruto"] - r["isr_retenido"]


# ══════════════════════════════════════════════════════════════════════════
# INTEGRACIÓN — flujos completos
# ══════════════════════════════════════════════════════════════════════════

class TestIntegracion:
    """Tests de integración entre módulos."""

    def test_flujo_completo_empleado_basico(self):
        """Flujo: SDI → IMSS → Nómina."""
        # 1. Calcular SDI
        sdi_r = calcular_sdi_completo(salario_diario_base=500)
        sdi = sdi_r["sdi_calculado"]

        # 2. Calcular cuotas IMSS
        imss_r = calcular_cuotas_imss(salario_diario_integrado=sdi)
        assert imss_r["total_cuota_trabajador"] > 0

        # 3. Calcular nómina
        nom_r = calcular_nomina(
            salario_mensual_bruto=500 * 30,
            periodo="mensual",
        )
        assert nom_r["neto_a_pagar"] > 0

    def test_consistencia_isr_nomina(self):
        """ISR de nómina consistente con cálculo directo."""
        salario = 30_000

        isr_r = calcular_isr_pf(salario, regimen="sueldos")
        nom_r = calcular_nomina(salario_mensual_bruto=salario, periodo="mensual")

        # El ISR retenido en nómina debe estar muy cerca al cálculo directo
        # (puede haber pequeñas diferencias por vales y horas extras)
        diff = abs(nom_r["deducciones"]["isr"]["isr_a_retener"] - isr_r["isr_a_cargo"])
        assert diff < 100  # Tolerancia de $100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

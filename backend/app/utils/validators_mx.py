"""
Validadores fiscales mexicanos
==============================
RFC, CURP, NSS, CLABE — validaciones de formato según SAT/IMSS/CFF.

Uso:
    from app.utils.validators_mx import validar_rfc, validar_curp, validar_nss

    if not validar_rfc("PEGJ950101ABC"):
        raise ValueError("RFC inválido")
"""
from __future__ import annotations
import re
from datetime import datetime
from typing import Optional


# ──────────────────────────────────────────────────────────────────────────
# RFC — Registro Federal de Contribuyentes (CFF Art. 27)
# ──────────────────────────────────────────────────────────────────────────

# Persona física: 4 letras + 6 dígitos (fecha YYMMDD) + 3 alfanuméricos
RFC_PF_PATTERN = re.compile(r"^[A-ZÑ&]{4}\d{6}[A-Z0-9]{3}$")

# Persona moral: 3 letras + 6 dígitos (fecha YYMMDD) + 3 alfanuméricos
RFC_PM_PATTERN = re.compile(r"^[A-ZÑ&]{3}\d{6}[A-Z0-9]{3}$")

# RFC genérico (público en general)
RFC_GENERICO_PF = "XAXX010101000"
RFC_GENERICO_EXTRANJERO = "XEXX010101000"


def validar_rfc(rfc: str, tipo: str = "auto") -> bool:
    """
    Valida formato de RFC mexicano.
    tipo: 'pf' (persona física, 13 caracteres),
          'pm' (persona moral, 12 caracteres),
          'auto' (detecta automáticamente)
    """
    if not rfc or not isinstance(rfc, str):
        return False

    rfc = rfc.upper().strip()

    if rfc in (RFC_GENERICO_PF, RFC_GENERICO_EXTRANJERO):
        return True

    if tipo == "pf":
        if not RFC_PF_PATTERN.match(rfc):
            return False
        return _validar_fecha_rfc(rfc[4:10])
    elif tipo == "pm":
        if not RFC_PM_PATTERN.match(rfc):
            return False
        return _validar_fecha_rfc(rfc[3:9])
    else:
        # Auto-detección por longitud
        if len(rfc) == 13:
            return validar_rfc(rfc, "pf")
        elif len(rfc) == 12:
            return validar_rfc(rfc, "pm")
        return False


def _validar_fecha_rfc(yymmdd: str) -> bool:
    """Valida que los 6 dígitos de fecha sean válidos."""
    try:
        yy, mm, dd = int(yymmdd[:2]), int(yymmdd[2:4]), int(yymmdd[4:6])
        # Asumimos siglo 19xx si yy >= 30, sino 20xx
        anio = 1900 + yy if yy >= 30 else 2000 + yy
        datetime(anio, mm, dd)
        return True
    except (ValueError, IndexError):
        return False


def detectar_tipo_rfc(rfc: str) -> Optional[str]:
    """Devuelve 'pf', 'pm' o None."""
    if not rfc:
        return None
    rfc = rfc.upper().strip()
    if len(rfc) == 13 and validar_rfc(rfc, "pf"):
        return "pf"
    if len(rfc) == 12 and validar_rfc(rfc, "pm"):
        return "pm"
    return None


# ──────────────────────────────────────────────────────────────────────────
# CURP — Clave Única de Registro de Población
# ──────────────────────────────────────────────────────────────────────────

CURP_PATTERN = re.compile(
    r"^[A-Z][AEIOUX][A-Z]{2}\d{6}[HM][A-Z]{2}[BCDFGHJKLMNPQRSTVWXYZ]{3}[A-Z0-9]\d$"
)


def validar_curp(curp: str) -> bool:
    """Valida formato CURP (18 caracteres)."""
    if not curp or not isinstance(curp, str):
        return False
    curp = curp.upper().strip()
    if not CURP_PATTERN.match(curp):
        return False
    return _validar_fecha_rfc(curp[4:10])


# ──────────────────────────────────────────────────────────────────────────
# NSS — Número de Seguridad Social IMSS (11 dígitos)
# ──────────────────────────────────────────────────────────────────────────

NSS_PATTERN = re.compile(r"^\d{11}$")


def validar_nss(nss: str) -> bool:
    """Valida NSS de 11 dígitos con checksum Luhn modificado IMSS."""
    if not nss or not isinstance(nss, str):
        return False
    nss = nss.strip()
    if not NSS_PATTERN.match(nss):
        return False
    return _luhn_check_nss(nss)


def _luhn_check_nss(nss: str) -> bool:
    """Validación checksum Luhn para NSS."""
    try:
        suma = 0
        for i, digito in enumerate(nss[:10]):
            n = int(digito)
            if i % 2 == 0:
                n *= 2
                if n > 9:
                    n -= 9
            suma += n
        verificador = (10 - (suma % 10)) % 10
        return verificador == int(nss[10])
    except (ValueError, IndexError):
        # Si falla el checksum, aceptar formato (algunos NSS antiguos no cumplen)
        return True


# ──────────────────────────────────────────────────────────────────────────
# CLABE — 18 dígitos para transferencias interbancarias
# ──────────────────────────────────────────────────────────────────────────

CLABE_PATTERN = re.compile(r"^\d{18}$")


def validar_clabe(clabe: str) -> bool:
    """Valida CLABE interbancaria de 18 dígitos con checksum."""
    if not clabe or not isinstance(clabe, str):
        return False
    clabe = clabe.strip().replace(" ", "")
    if not CLABE_PATTERN.match(clabe):
        return False
    return _checksum_clabe(clabe)


def _checksum_clabe(clabe: str) -> bool:
    """Algoritmo oficial CLABE (módulo 10)."""
    pesos = [3, 7, 1] * 5 + [3, 7, 1]  # 17 pesos
    try:
        suma = sum((int(clabe[i]) * pesos[i]) % 10 for i in range(17))
        verificador = (10 - (suma % 10)) % 10
        return verificador == int(clabe[17])
    except (ValueError, IndexError):
        return False


# ──────────────────────────────────────────────────────────────────────────
# Validaciones de fechas y rangos
# ──────────────────────────────────────────────────────────────────────────

def validar_fecha_iso(fecha: str) -> bool:
    """Valida formato YYYY-MM-DD."""
    if not fecha or not isinstance(fecha, str):
        return False
    try:
        datetime.strptime(fecha, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def validar_rango_fechas(inicio: str, fin: str) -> tuple[bool, Optional[str]]:
    """Valida que inicio <= fin. Devuelve (válido, mensaje_error)."""
    if not validar_fecha_iso(inicio):
        return False, f"Fecha inicio inválida: {inicio}"
    if not validar_fecha_iso(fin):
        return False, f"Fecha fin inválida: {fin}"

    d_inicio = datetime.strptime(inicio, "%Y-%m-%d")
    d_fin = datetime.strptime(fin, "%Y-%m-%d")

    if d_fin < d_inicio:
        return False, "Fecha fin debe ser posterior a inicio"
    return True, None


def calcular_antiguedad_anios(fecha_ingreso: str, fecha_referencia: str = None) -> float:
    """Calcula años de antigüedad con decimales."""
    if not validar_fecha_iso(fecha_ingreso):
        raise ValueError(f"Fecha ingreso inválida: {fecha_ingreso}")

    d_ingreso = datetime.strptime(fecha_ingreso, "%Y-%m-%d")
    d_ref = datetime.strptime(fecha_referencia, "%Y-%m-%d") if fecha_referencia else datetime.now()

    delta = d_ref - d_ingreso
    return round(delta.days / 365.25, 4)


# ──────────────────────────────────────────────────────────────────────────
# Excepción específica
# ──────────────────────────────────────────────────────────────────────────

class ValidacionFiscalError(Exception):
    """Error de validación fiscal con campo y motivo."""
    def __init__(self, campo: str, motivo: str):
        self.campo = campo
        self.motivo = motivo
        super().__init__(f"{campo}: {motivo}")


def validar_o_lanzar(campo: str, valor, validador) -> str:
    """Helper: valida y lanza ValidacionFiscalError si falla."""
    if not validador(valor):
        raise ValidacionFiscalError(campo, f"Formato inválido: '{valor}'")
    return valor.upper().strip() if isinstance(valor, str) else valor

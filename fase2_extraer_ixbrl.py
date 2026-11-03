"""
FASE 2e - Extrae las cifras de las cuentas en iXBRL (formato digital etiquetado).
Sin OCR: cada cifra viene marcada con su concepto (p. ej. TurnoverRevenue) y su
periodo, asi que la lectura es exacta.

Salida: datos_fase2/cifras_ixbrl_largo.csv (mismo formato que cifras_ocr_largo.csv)
Uso:  python fase2_extraer_ixbrl.py [carpeta_cuentas]   (por defecto C:\\datos_premier\\cuentas)
"""
import csv, re, sys, warnings
from datetime import date
from pathlib import Path
from bs4 import BeautifulSoup
try:
    from bs4 import XMLParsedAsHTMLWarning
    warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
except ImportError:
    pass

BASE = Path(__file__).resolve().parent
CUENTAS = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(r"C:\datos_premier\cuentas")
OUT = BASE / "datos_fase2" / "cifras_ixbrl_largo.csv"

# variable -> (conceptos posibles, signo). signo -1: el concepto es un gasto en positivo
# y en la cuenta de resultados se presenta en negativo (como en el OCR).
MAPA = {
    "ingresos": (["TurnoverRevenue", "Revenue"], 1),
    "resultado_explotacion": (["OperatingProfitLoss"], 1),
    "resultado_antes_impuestos": (["ProfitLossOnOrdinaryActivitiesBeforeTax", "ProfitLossBeforeTax"], 1),
    "impuesto": (["TaxTaxCreditOnProfitOrLossOnOrdinaryActivities", "TaxExpenseCredit"], -1),
    "resultado_neto": (["ProfitLoss"], 1),
    "intereses_pagados": (["InterestPayableSimilarChargesFinanceCosts"], -1),
    "beneficio_traspasos": (["GainLossOnDisposalsIntangibleAssets"], 1),
    "amortizacion_jugadores": (["AmortisationExpenseIntangibleAssets", "IncreaseFromAmortisationChargeForYearIntangibleAssets"], -1),
    "gastos_personal": (["StaffCostsEmployeeBenefitsExpense"], 1),
    "sueldos_salarios": (["WagesSalaries"], 1),
    "seguridad_social": (["SocialSecurityCosts"], 1),
    "pensiones": (["PensionOtherPostEmploymentBenefitCostsOtherPensionCosts", "PensionCosts"], 1),
    "intangibles": (["IntangibleAssets"], 1),
    "inmovilizado_material": (["PropertyPlantEquipment"], 1),
    "deudores": (["Debtors"], 1),
    "caja": (["CashBankOnHand", "CashCashEquivalents"], 1),
    "acreedores_cp": (["Creditors@WithinOneYear"], 1),
    "acreedores_lp": (["Creditors@AfterOneYear"], 1),
    "activo_circulante_neto": (["NetCurrentAssetsLiabilities"], 1),
    "activo_menos_pasivo_cp": (["TotalAssetsLessCurrentLiabilities"], 1),
    "provisiones": (["ProvisionsForLiabilitiesBalanceSheetSubtotal"], 1),
    "activos_netos": (["NetAssetsLiabilities"], 1),
    "patrimonio": (["Equity"], 1),
}

def fecha(s):
    try:
        return date.fromisoformat(s.strip()[:10])
    except Exception:
        return None

def leer(ruta):
    s = BeautifulSoup(ruta.read_bytes(), "lxml")
    ctx = {}
    for c in s.find_all(re.compile(r"(^|:)context$")):
        fin = c.find(re.compile(r"(^|:)(enddate|instant)$"))
        miembros = [m.get_text(strip=True) for m in c.find_all(re.compile(r"(^|:)explicitmember$"))]
        tipos = [m.get_text(strip=True) for m in c.find_all(re.compile(r"(^|:)typedmember$"))]
        ctx[c.get("id")] = (fecha(fin.get_text()) if fin else None, miembros, bool(tipos))
    hechos = []
    for t in s.find_all(re.compile(r"nonfraction$")):
        nombre = (t.get("name") or "").split(":")[-1]
        fin, miembros, tipado = ctx.get(t.get("contextref"), (None, [], False))
        if fin is None or tipado:
            continue
        txt = t.get_text(strip=True)
        if not re.search(r"\d", txt):
            v = 0.0
        else:
            v = float(re.sub(r"[^\d.]", "", txt.replace(",", "")) or 0)
        v *= 10 ** int(t.get("scale") or 0)
        if t.get("sign") == "-":
            v = -v
        # dimensiones aceptadas: ninguna, grupo consolidado, o vencimiento (para acreedores)
        vto = ""
        valido = True
        for m in miembros:
            ml = m.lower()
            if "withinoneyear" in ml:
                vto = "@WithinOneYear"
            elif "afteroneyear" in ml or "morethanoneyear" in ml:
                vto = "@AfterOneYear"
            elif "consolidated" in ml or ml.endswith("groupmember"):
                pass
            else:
                valido = False
        if valido:
            hechos.append((nombre + vto, fin, v / 1000.0))
    return hechos

def main():
    filas = []
    docs = sorted(CUENTAS.glob("*/*.xhtml"))
    for ruta in docs:
        numero = ruta.parent.name
        cierre = fecha(ruta.stem[:10])
        hechos = leer(ruta)
        for var, (conceptos, signo) in MAPA.items():
            for con in conceptos:
                act = [v for n, f, v in hechos if n == con and f == cierre]
                previos = sorted({f for n, f, v in hechos if n == con and f < cierre})
                ant = [v for n, f, v in hechos if n == con and previos and f == previos[-1]]
                if act:
                    filas.append({"numero": numero, "cierre": str(cierre), "documento": ruta.stem,
                                  "bloque": "ixbrl", "variable": var, "actual": signo * act[0],
                                  "anterior": signo * ant[0] if ant else None, "pagina": "",
                                  "etiqueta_ocr": con})
                    break
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        w.writeheader(); w.writerows(filas)
    print(f"Listo: {len(filas)} cifras de {len(docs)} documentos iXBRL -> {OUT}")

if __name__ == "__main__":
    main()

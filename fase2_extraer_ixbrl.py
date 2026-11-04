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
            elif "consolidated" in ml or ml.endswith("groupmember") or ml.endswith(":original"):
                pass        # grupo consolidado, o importe "tal como se publico" (dimension de reexpresion)
            else:
                valido = False
        if valido:
            hechos.append((nombre + vto, fin, v / 1000.0))
    return hechos

def texto_tablas(s):
    """Texto del documento con una linea por fila de tabla (para leer con las mismas reglas que el OCR)."""
    lineas = []
    for tr in s.find_all(re.compile(r"(^|:)tr$")):
        celdas = [c.get_text(" ", strip=True) for c in tr.find_all(re.compile(r"(^|:)t[dh]$"))]
        if celdas:
            lineas.append("  ".join(c for c in celdas if c))
    return "\n".join(lineas)

def texto_lineal(s):
    """Para documentos maquetados con <div> (sin tablas): cada etiqueta va seguida de sus
    cifras en lineas sueltas. Se reconstruye 'etiqueta cifra1 cifra2'."""
    trozos = [x.strip() for x in s.get_text("\n", strip=True).splitlines() if x.strip()]
    num = re.compile(r"^\(?-?[\d,.]+\)?$|^-$")
    lineas, i = [], 0
    while i < len(trozos):
        t = trozos[i]
        if not num.match(t):
            j, cifras = i + 1, []
            while j < len(trozos) and num.match(trozos[j]) and len(cifras) < 6:
                cifras.append(trozos[j]); j += 1
            if cifras:
                lineas.append(t + "  " + "  ".join(cifras)); i = j; continue
        lineas.append(t); i += 1
    return "\n".join(lineas)

def main():
    import fase2_extraer_cifras as X
    filas = []
    docs = sorted(CUENTAS.glob("*/*.xhtml"))
    for ruta in docs:
        numero = ruta.parent.name
        cierre = fecha(ruta.stem[:10])
        hechos = leer(ruta)
        soup = BeautifulSoup(ruta.read_bytes(), "lxml")
        texto = texto_tablas(soup) + "\n" + texto_lineal(soup)
        tiene_pyg = bool(re.search(r"(?im)^(turnover|revenue)", texto) and re.search(r"(?i)before (income )?tax", texto))
        filas.append({"numero": numero, "cierre": str(cierre), "documento": ruta.stem, "bloque": "ixbrl",
                      "variable": "cuenta_resultados_publicada", "actual": 1.0 if tiene_pyg else 0.0,
                      "anterior": None, "pagina": "", "etiqueta_ocr": "deteccion en texto"})
        encontradas = set()
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
                    encontradas.add(var)
                    break
        # partidas no etiquetadas: se leen del texto con las reglas del OCR. La unidad del
        # texto se calibra con las partidas que SI estan etiquetadas (si no hay ninguna en
        # comun, no se usa el texto: mejor un hueco que una cifra con la unidad equivocada)
        etiq = {f["variable"]: f["actual"] for f in filas if f["documento"] == ruta.stem and f["bloque"] == "ixbrl"}
        leido = {}
        for bloque, reglas in (("pyg", X.PYG), ("balance", X.BAL), ("personal", X.PER)):
            if bloque == "pyg" and not tiene_pyg:
                continue
            # solo lineas de tabla: etiqueta corta y al menos una cifra de importe (>=1.000)
            tabla = "\n".join(l for l in texto.splitlines()
                               if len(re.split(r"\s\(?-?\d", l, 1)[0]) <= 45
                               and any(abs(v) >= 1000 for v in X.numeros(l))
                               and not re.search(r"(?i)for the year was|increase|decrease|compared", l))
            for var, v in X.extraer(tabla, reglas, 1.0).items():
                leido.setdefault(var, v)
        factores = [etiq[v] / leido[v][0] for v in leido if v in etiq and etiq[v] and leido[v][0]]
        factores = [f for f in factores if any(abs(f / k - 1) < 0.01 for k in (1000.0, 1.0, 0.001))]
        u = None
        if factores:
            for k in (1000.0, 1.0, 0.001):
                if sum(abs(f / k - 1) < 0.01 for f in factores) > len(factores) / 2:
                    u = k
        if u is not None:
            for var, (a, b, et) in leido.items():
                if var not in encontradas and a and not (var == "ingresos" and abs(a * u) < 500) and not re.search(r"stream|was|by ", et):
                    a, b = a * u, (b * u if b is not None else None)
                    filas.append({"numero": numero, "cierre": str(cierre), "documento": ruta.stem,
                                  "bloque": "ixbrl_texto", "variable": var, "actual": a, "anterior": b,
                                  "pagina": "", "etiqueta_ocr": "texto: " + et})
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        w.writeheader(); w.writerows(filas)
    print(f"Listo: {len(filas)} cifras de {len(docs)} documentos iXBRL -> {OUT}")

if __name__ == "__main__":
    main()

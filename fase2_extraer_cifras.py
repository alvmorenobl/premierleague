"""
FASE 2d - Extrae las cifras principales del texto OCR de cada cuenta.

Para cada documento de <ocr>/<numero>/<documento>/:
  - elige la pagina de la cuenta de resultados y la del balance (entre las
    paginas clave) y la(s) de personal;
  - en cada linea separa la etiqueta de las cifras y reconoce la partida con
    reglas (turnover -> ingresos, before tax -> resultado antes de impuestos...);
  - toma la columna del ejercicio actual y la del anterior;
  - pasa todo a miles de libras.

Salida: datos_fase2/cifras_ocr_largo.csv (una fila por documento y partida)
Uso:  python fase2_extraer_cifras.py [carpeta_ocr]   (por defecto C:\\datos_premier\\ocr)
"""
import csv, json, re, sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
OCR = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(r"C:\datos_premier\ocr")
OUT = BASE / "datos_fase2" / "cifras_ocr_largo.csv"

# (variable, regex sobre la etiqueta en minusculas). El orden importa: la primera que encaja gana.
PYG = [
    ("resultado_explotacion_sin_traspasos", r"operating .{0,30}(before|excluding) .{0,30}(player|trading|amortis|transfer)"),
    ("beneficio_traspasos", r"(profit|gain|surplus|loss).{0,40}(disposal|sale|transfer|trading).{0,30}(player|registration)|player trading"),
    ("amortizacion_jugadores", r"amortis.{0,40}(player|registration)"),
    ("resultado_explotacion", r"operating (profit|loss|\(loss\)|result|\(toss\)|toss)|^(profit|loss).{0,6}/.{0,10}operating"),
    ("intereses_pagados", r"interest payable"),
    ("resultado_antes_impuestos", r"before tax"),
    ("impuesto", r"^tax (on|credit|charge)|^taxation"),
    ("resultado_neto", r"(profit|loss|result).{0,40}for the (financial )?(year|period)"),
    ("ingresos", r"^(total )?(turnover|revenue)s?\b(?!.*(by|from|analys|split))"),
]
BAL = [
    ("intangibles", r"^intangible"),
    ("inmovilizado_material", r"^tangible"),
    ("acreedores_cp", r"creditors.{0,50}within one year"),
    ("acreedores_lp", r"creditors.{0,50}(after more than one year|after one year|more than one year)"),
    ("activo_circulante_neto", r"net current (assets|liabilities|\(liabilities\))"),
    ("activo_menos_pasivo_cp", r"total assets less current liabilities"),
    ("provisiones", r"^provisions"),
    ("activos_netos", r"^net (assets|liabilities|\(liabilities\))|^net assets/|^net \(?liabilities"),
    ("patrimonio", r"total (shareholders|equity|capital employed)|shareholders.{0,6}(funds|deficit|deficiency)|^total equity|members.{0,3} (funds|deficit)"),
    ("deudores", r"^debtors"),
    ("caja", r"^cash (at bank|and cash equivalents|in hand)|^cash$"),
]
PER = [
    ("gastos_personal", r"^(total )?(staff|employment|personnel) costs|^total staff"),
    ("sueldos_salarios", r"^wages and salaries"),
    ("seguridad_social", r"^social security"),
    ("pensiones", r"^(other )?pension"),
]

NUM = re.compile(r"\(?-?\d{1,3}(?:[,.;:]\d{3})+\)?|\(?-?\d+\)?|(?<!\S)[-–—=](?!\S)")

def numero(tok):
    if tok in "-–—=":
        return 0.0
    neg = tok.startswith("(") or tok.endswith(")") or tok.startswith("-")
    d = re.sub(r"[^\d]", "", tok)
    if not d:
        return None
    v = float(d)
    return -v if neg else v

def unidad(texto):
    """Multiplicador para pasar a miles de libras.
    1) marca explicita de miles (£000, £'000...) -> 1
    2) si hay varias cifras con dos separadores (1,234,567) estan en libras -> 0,001
    3) cabecera '£m' -> 1000
    4) por defecto, miles."""
    t = texto.lower()
    if re.search(r"[£€fe]\s?['’`°\"]?\s?[0o]{3}\b|£k|000s|['’`]000\b|(?<![\d,])000(?![\d,])", t):
        return 1.0
    if len(re.findall(r"\d{1,3}[,.]\d{3}[,.]\d{3}", t)) >= 3:
        return 0.001
    if re.search(r"(?<!\S)£\s?m(?!\S)", t):
        return 1000.0
    return 1.0

def lineas(texto):
    """Devuelve (etiqueta, [numeros]) por linea, uniendo etiquetas partidas en 2 lineas."""
    previa = ""
    for raw in texto.splitlines():
        s = raw.replace("|", " ").strip(" .,;:'‘’\"_~-*")
        m = NUM.search(s)
        etiqueta = s[:m.start()] if m else s
        etiqueta = re.sub(r"[^A-Za-z/()' &]", " ", etiqueta).lower()
        etiqueta = re.sub(r"\s+", " ", etiqueta).strip()
        nums = [numero(t) for t in NUM.findall(s[m.start():])] if m else []
        nums = [n for n in nums if n is not None]
        if not nums:
            previa = etiqueta if 0 < len(etiqueta) < 70 else ""
            continue
        unida = (previa + " " + etiqueta).strip() if (len(etiqueta) < 25 and previa) else etiqueta
        previa = ""
        yield (etiqueta, unida), nums

def columnas(nums, n_cols):
    """Elige (actual, anterior).
    - Formato 'operaciones | traspasos | total | total año anterior' (Bolton, Everton,
      Man City...) y su version de 6 columnas (Arsenal): se detecta porque
      a + b = total, y se toma la columna total.
    - n_cols=4 cuando hay grupo y sociedad (2 años x 2 columnas).
    - Por defecto: penultima = año actual, ultima = año anterior."""
    g = list(nums)
    while len(g) > 2 and abs(g[0]) < 50 and g[0] == int(g[0]):   # numeros de nota
        g = g[1:]
    cerca = lambda x, y: abs(x - y) <= max(2, 0.002 * abs(y))
    if len(g) >= 3:
        for i in range(2, len(g)):
            if cerca(g[i-2] + g[i-1], g[i]) and abs(g[i]) > 0:
                act = g[i]
                rest = g[i+1:]
                if len(rest) >= 3 and cerca(rest[0] + rest[1], rest[2]):
                    return act, rest[2]
                return act, (rest[-1] if rest else None)
    if n_cols == 4 and len(g) >= 4:
        return g[-4], g[-3]
    if len(g) >= 2:
        return g[-2], g[-1]
    return g[-1], None

def n_columnas(texto):
    for l in texto.splitlines()[:25]:
        anos = re.findall(r"\b20[0-3]\d\b", l)
        if len(anos) >= 4 and len(set(anos)) == 2:
            return 4
    return 2

def extraer(texto, reglas):
    u = unidad(texto); nc = n_columnas(texto)
    res = {}
    for (sola, unida), nums in lineas(texto):
        for var, pat in reglas:
            et = sola if re.search(pat, sola) else (unida if re.search(pat, unida) else None)
            if et is not None:
                if var not in res:
                    a, b = columnas(nums, nc)
                    res[var] = (a * u if a is not None else None, b * u if b is not None else None, et[:60])
                break
    return res, u

def mejor_pagina(doc, paginas, reglas, obligatoria):
    mejor, mres = None, {}
    for p in paginas:
        f = doc / "fino" / f"pag_{p:03d}.txt"
        if not f.exists():
            continue
        t = f.read_text(encoding="utf-8", errors="replace")
        if obligatoria and not re.search(obligatoria, t.lower()):
            continue
        res, u = extraer(t, reglas)
        if len(res) > len(mres):
            mejor, mres = p, res
    return mejor, mres

def main():
    OUT.parent.mkdir(exist_ok=True)
    filas = []
    docs = sorted(OCR.glob("*/*/hecho.json"))
    for i, h in enumerate(docs, 1):
        doc = h.parent
        numero_soc = doc.parent.name
        cierre = doc.name[:10]
        try:
            clave = json.loads((doc / "paginas_clave.json").read_text(encoding="utf-8"))
        except Exception:
            clave = {}
        bloques = [
            ("pyg", clave.get("resultados", []), PYG, r"before tax"),
            ("balance", clave.get("balance", []), BAL, r"net (current )?(assets|liabilities)"),
            ("personal", clave.get("personal", []), PER, r"wages|staff costs"),
        ]
        for bloque, pags, reglas, obl in bloques:
            p, res = mejor_pagina(doc, pags, reglas, obl)
            for var, (a, b, et) in res.items():
                filas.append({"numero": numero_soc, "cierre": cierre, "documento": doc.name,
                              "bloque": bloque, "variable": var, "actual": a, "anterior": b,
                              "pagina": p, "etiqueta_ocr": et})
        if i % 200 == 0:
            print(f"{i}/{len(docs)}")
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        w.writeheader(); w.writerows(filas)
    print(f"Listo: {len(filas)} cifras de {len(docs)} documentos -> {OUT}")

if __name__ == "__main__":
    main()

"""
FASE 2d - Extrae las cifras principales del texto OCR de cada cuenta (version 2,
reescrita tras la auditoria del 3/11/2026).

Cambios respecto a la v1 (cada uno corrige un fallo medido en la muestra de referencia):
  - usa la localizacion v2 de paginas (paginas_clave_v2.json): titulos FRS 102/NIIF y
    preferencia por el estado CONSOLIDADO;
  - cifras con espacio como separador de miles ("10 979,172") se unen solo si encajan
    en magnitud con la columna del ano anterior;
  - se descartan fechas y anos leidos como cifras ("year ended 30 June 2015");
  - formatos de 1, 2, 4 y 6 columnas (primer ejercicio, grupo/sociedad, operaciones +
    traspasos = total);
  - la unidad (libras, miles, millones) se fija UNA vez por documento;
  - etiquetas de titulos excluidas; el impuesto solo se lee en la cuenta de resultados.

Salida: datos_fase2/cifras_ocr_largo.csv (una fila por documento y partida, con pagina)
Uso:  python fase2_extraer_cifras.py [carpeta_ocr]   (por defecto C:\\datos_premier\\ocr)
"""
import csv, json, math, re, sys
from fase2_reglas import TIT_BAL, TIT_PYG
from pathlib import Path

BASE = Path(__file__).resolve().parent
OCR = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(r"C:\datos_premier\ocr")
OUT = BASE / "datos_fase2" / "cifras_ocr_largo.csv"

EXCLUIR_ETIQ = r"account for|statement of|ended|notes? to|as at|balance sheet|excluding pension|analysed as|and li[a-z]*bilities"
PYG = [
    ("resultado_explotacion_sin_traspasos", r"operating .{0,40}(before|excluding) .{0,40}(player|trading|amortis|transfer|registration)"),
    ("beneficio_traspasos", r"(profit|gain|surplus|loss).{0,40}(disposal|sale|transfer|trading).{0,30}(player|registration|football staff|intangible)|^profit on player trading"),
    ("amortizacion_jugadores", r"^amortis.{0,50}(player|registration)"),
    ("resultado_antes_impuestos", r"before (income )?tax|before and after tax"),
    ("resultado_explotacion", r"^(group )?operating (profit|loss|\(loss\)|result|\(toss\)|toss)|^(profit|loss)\W{0,3}(\(loss\)|\(profit\))?\W{0,3}operating"),
    ("intereses_pagados", r"interest payable|^finance costs?$|^interest expense"),
    ("impuesto", r"^(tax|taxation|income tax)\b(?!.*before)"),
    ("resultado_neto", r"^\W*(\(?(profit|loss)\)?\W{0,3}){1,2}.{0,30}(for the (financial )?(year|period)|after tax)"),
    ("ingresos", r"^(total |group |consolidated )?(turnover|tumover|revenue)s?\b(?!.*(by|from (?!contracts)|analys|split|recogni|deferred|stream|was|joint venture|share of))"),
]
BAL = [
    ("intangibles", r"^intangible"),
    ("inmovilizado_material", r"^tangible|^property,? plant"),
    ("acreedores_cp", r"(creditors|current liabilities).{0,50}within one year|^current liabilities$"),
    ("acreedores_lp", r"creditors.{0,50}(after more than one year|after one year|more than one year)|^non.?current liabilities$"),
    ("activo_circulante_neto", r"^net current (assets|liabilities|\(liabilities\))"),
    ("activo_menos_pasivo_cp", r"^total assets less current liabilities"),
    ("provisiones", r"^provisions"),
    ("activos_netos", r"^net \(?(assets|l[a-z]{4,10}t?i?es|deficit)\)?(?=\W|$)(?!.*excluding)"),
    ("patrimonio", r"^(?!.*and li[a-z]*bilities)total (shareholders|equity|members)|shareholder.{0,8}(funds|deficit|deficiency)|^total equity|^members.{0,3} (funds|deficit)|^equity shareholders"),
    ("deudores", r"^debtors$|^debtors\b(?!.*after)|^trade and other receivables"),
    ("caja", r"^cash (at bank|and cash equivalents|in hand)|^cash$"),
]
PER = [
    ("gastos_personal", r"^(total )?(staff|employment|personnel) costs\b(?!.*(were|comprise|include|as follows))|^total staff"),
    ("sueldos_salarios", r"^wages ?and ?sal[a-z]{3,5}s?\b"),     # 'salanes', 'andsalaries' (OCR)
    ("seguridad_social", r"^social security"),
    ("pensiones", r"^(other )?pension"),
]
# exclusiones propias de una partida
EXCL_VAR = {"sueldos_salarios": r"normal|exceptional|director|included|excluding"}
MESES = r"january|february|march|april|may|june|july|august|september|october|november|december"

TOK = re.compile(r"\(?-?\d{1,3}(?:[,.;:]\d{3})+\)?|\(?-?\d+\)?|(?<!\S)[-–—](?!\S)")   # "=" es ruido de subrayado, no cero

def valor(tok):
    if tok in "-–—":
        return 0.0
    neg = tok.startswith("(") or tok.endswith(")") or tok.startswith("-")
    d = re.sub(r"[^\d]", "", tok)
    if not d:
        return None
    return -float(d) if neg else float(d)

def tokens(s):
    """Lista de (texto, inicio, fin) de cada cifra de la linea."""
    s = re.sub(r"\((\d{1,3}) (\d{3}(?:,\d{3})*)\)", r"(\1,\2)", s)   # "(63 173)" -> "(63,173)"
    s = re.sub(r"(\d,)\s(\d{3}\b)(?![,.]\d)", r"\1\2", s)     # "5,078, 106" -> "5,078,106" (no "332,211. 298,903")
    s = re.sub(r"(?<![\d,.])(\d{1,3}),\s(\d{3}(?:,\d{3})+)\b", r"\1,\2", s)   # "10, 886,881" -> "10,886,881"
    return [(m.group(), m.start(), m.end()) for m in TOK.finditer(s)]

def es_fecha(linea):
    l = linea.lower()
    return bool(re.search(MESES, l) or re.search(r"year ended|period ended|as at|\b(19|20)\d\d\s+(19|20)\d\d\b", l))

def numeros(s):
    s = re.sub(r"(?<![\d,])[$§](?=\d{1,3}(,\d{3})+)", "5", s)    # "$49,633" -> "549,633"
    s = re.sub(r"\((\d{1,3}) (\d{3}(?:,\d{3})*)\)", r"(\1,\2)", s)
    s = re.sub(r"(\d,)\s(\d{3}\b)(?![,.]\d)", r"\1\2", s)
    s = re.sub(r"(?<![\d,.])(\d{1,3}),\s(\d{3}(?:,\d{3})+)\b", r"\1,\2", s)
    """Cifras de una linea, uniendo grupos separados por espacio ('10 979,172') cuando la
    union encaja mejor en magnitud con la columna siguiente."""
    tk = tokens(s)
    vals = [valor(t) for t, _, _ in tk]
    i = 0
    out = []
    while i < len(tk):
        t, a, b = tk[i]
        v = vals[i]
        if (i + 1 < len(tk) and re.fullmatch(r"\(?\d{1,3}", t) and s[b:tk[i+1][1]] == " "
                and re.fullmatch(r"\d{3}(?:[,.;:]\d{3})+\)?", tk[i+1][0])):
            unido = valor(t.lstrip("(") + "," + tk[i+1][0]) * (-1 if t.startswith("(") or tk[i+1][0].endswith(")") else 1)
            sig = vals[i+2] if i + 2 < len(tk) else None
            suelto = vals[i+1]
            if sig not in (None, 0) and unido != 0 and suelto not in (None, 0):
                err_u = abs(math.log(abs(unido) / abs(sig)))
                err_s = abs(math.log(abs(suelto) / abs(sig)))
                if err_u < err_s:
                    out.append(unido); i += 2; continue
        if (i + 1 < len(tk) and re.fullmatch(r"\(?\d{1,3}(?:[,.]\d{3})+", t) and s[b:tk[i+1][1]] == " "
                and re.fullmatch(r"\d{3}\)?", tk[i+1][0]) and i >= 1):
            unido = valor(t.lstrip("(") + "," + tk[i+1][0])
            if t.startswith("(") or tk[i+1][0].endswith(")"):
                unido = -abs(unido)
            vecinos = [x for x in ((out[-1] if out else None), (vals[i+2] if i + 2 < len(tk) else None)) if x]
            if vecinos and unido and v:
                du = min(abs(math.log(abs(unido) / abs(x))) for x in vecinos)
                dv = min(abs(math.log(abs(v) / abs(x))) for x in vecinos)
                if du < dv:
                    out.append(unido); i += 2; continue
        if v is not None:
            out.append(v)
        i += 1
    return out

def n_columnas_ano(texto):
    """Columnas de ano de la tabla: 1 (primer ejercicio), 2 (normal) o 4 (grupo y sociedad).
    Se decide por la cabecera (anos) y por cuantas cifras grandes tiene cada linea."""
    cab = texto.splitlines()[:30]
    for l in cab:
        anos = re.findall(r"\b20[0-3]\d\b", l)
        if len(anos) >= 4 and len(set(anos)) == 2:
            return 4
        if len(anos) == 3 and len(set(anos)) == 3:
            return 3          # p. ej. '30 June 2025 | 30 June 2024 | 1 July 2023' (balance reexpresado)
    cuentas = {}
    for l in texto.splitlines():
        if es_fecha(l):
            continue
        big = [v for v in numeros(l) if abs(v) >= 100 or v == 0]
        if big:
            cuentas[len(big)] = cuentas.get(len(big), 0) + 1
    if cuentas:
        moda = max(cuentas, key=cuentas.get)
        dos_anos = any(len(re.findall(r"\b(20[0-3]\d|\d{1,2}\.\d{1,2}\.\d{2})\b", l)) >= 2 for l in cab)
        if moda == 1 and not dos_anos:
            return 1
    return 2

def elegir(nums, ncol):
    """(actual, anterior) a partir de las cifras de la linea."""
    g = list(nums)
    cerca = lambda x, y: abs(x - y) <= max(2, 0.00002 * abs(y))    # la suma de columnas es exacta
    nota = lambda x: x != 0 and abs(x) < 60 and x == int(x)
    sin_nota = list(g)
    while len(sin_nota) > 2 and nota(sin_nota[0]):
        sin_nota = sin_nota[1:]
    # 6 columnas: operaciones | traspasos | total | (lo mismo del año anterior)
    if len(sin_nota) == 6 and cerca(sin_nota[3] + sin_nota[4], sin_nota[5]):
        return sin_nota[2], sin_nota[5]
    # 'operaciones | traspasos | total | (anterior...)': a + b = total
    if len(g) >= 3:
        for i in range(2, len(g)):
            if nota(g[i-2]) or nota(g[i-1]):
                continue
            if cerca(g[i-2] + g[i-1], g[i]) and g[i] != 0:
                rest = g[i+1:]
                if len(rest) >= 3 and cerca(rest[0] + rest[1], rest[2]):
                    return g[i], rest[2]
                return g[i], (rest[-1] if rest else None)
    # lo mismo sin los ceros de guiones/ruido sueltos ('0 (48,286) 0 72,377 24,091 (74,447)')
    nz = [x for x in g if x != 0 and not nota(x)]
    if len(nz) >= 3 and len(nz) < len(g):
        for i in range(2, len(nz)):
            if cerca(nz[i-2] + nz[i-1], nz[i]):
                rest = nz[i+1:]
                return nz[i], (rest[-1] if rest else None)
    # quitar numeros de nota al principio
    while len(g) > max(ncol, 1) and abs(g[0]) < 60 and g[0] == int(g[0]):
        g = g[1:]
    if ncol == 1:
        if len(g) >= 2 and abs(g[0]) < 60:
            g = g[1:]
        return (g[-1] if g else None), None
    if ncol == 4:
        if len(sin_nota) >= 4:
            return sin_nota[-4], sin_nota[-3]
        if len(sin_nota) == 3:          # falta el guion de una columna vacia
            return sin_nota[-2], sin_nota[-1]
    if ncol == 3 and len(g) >= 3:
        return g[-3], g[-2]
    if len(g) >= 2:
        return g[-2], g[-1]
    return (g[-1] if g else None), None

def lineas(texto):
    """(etiqueta, etiqueta_ampliada, cifras) por linea. La etiqueta ampliada une la linea
    anterior sin cifras ('Loss on ordinary activities' + 'before taxation 6 (4,454)') o la
    siguiente cuando completa la etiqueta ('... before (14,594) 1,210' + 'taxation')."""
    previa = ""
    pendiente = None
    def limpiar(x):
        return re.sub(r"\s+", " ", re.sub(r"[^A-Za-z/()' &,-]", " ", x).lower()).strip(" ,-")
    for raw in texto.splitlines():
        s = raw.replace("|", " ").strip(" .,;:'‘’\"_~-*")
        if es_fecha(s) and not re.search(r"turnover|revenue|profit|loss|assets|liabilities", s.lower()):
            if pendiente: yield pendiente; pendiente = None
            previa = ""
            continue
        # un guion seguido de texto es parte de la etiqueta ('wages and salaries - normal costs')
        m = next((x for x in TOK.finditer(s) if not (x.group() in "-–—" and re.match(r"\s*[A-Za-z]", s[x.end():]))), None)
        etiq = re.sub(r"^(?:[a-z] )+(?=[a-z]{3,})", "", limpiar(s[:m.start()] if m else s))   # 'i wages ...' (ruido OCR)
        nums = numeros(s[m.start():]) if m else []
        if not nums:
            if pendiente:
                e, u, n = pendiente
                if 0 < len(etiq) < 40 and re.search(r"\b(before|and|on|of|ordinary|activities|the|from|after)$", e):
                    pendiente = (e, (u + " " + etiq).strip(), n)
                yield pendiente; pendiente = None
            previa = etiq if 0 < len(etiq) < 70 else ""
            continue
        if pendiente: yield pendiente
        unida = (previa + " " + etiq).strip() if (len(etiq) < 25 and previa) else etiq
        previa = ""
        pendiente = (etiq, unida, nums)
    if pendiente:
        yield pendiente

def unidad_documento(textos):
    """Multiplicador a miles de libras, fijado con las paginas de estados principales."""
    t = " ".join(textos).lower()
    if re.search(r"[£€fe]\s?['’`°\"]?\s?[0o]{3}\b|£k\b|['’`]000\b|(?<![\d,.])000(?![\d,.])", t):
        return 1.0
    if len(re.findall(r"\d{1,3}[,.]\d{3}[,.]\d{3}", t)) >= 3:
        return 0.001
    if re.search(r"(?<!\S)£\s?m(?!\S)|£ ?million", t):
        return 1000.0
    return 1.0

def extraer(texto, reglas, u):
    ncol = n_columnas_ano(texto)
    res = {}
    for sola, unida, nums in lineas(texto):
        # cuentas en libras: un entero < 60 al principio es el numero de nota, nunca un importe
        while u == 0.001 and len(nums) >= 2 and nums[0] != 0 and abs(nums[0]) < 60 and nums[0] == int(nums[0]):
            nums = nums[1:]
        for var, pat in reglas:
            et = sola if re.search(pat, sola) else (unida if re.search(pat, unida) and reglas is not PER else None)
            if et is None or re.search(EXCLUIR_ETIQ, et) or (var in EXCL_VAR and re.search(EXCL_VAR[var], et)):
                continue
            if var not in res:
                a, b = elegir(nums, ncol)
                # 'Net liabilities 80,928,554' sin parentesis: es un pasivo neto -> negativo
                if var in ("activos_netos", "patrimonio") and re.match(r"^(net l[a-z]{4,10}ties|net deficit|(total )?shareholders.{0,3} deficit)$", et):
                    a = -abs(a) if a is not None else a
                    b = -abs(b) if b is not None else b
                if a is not None:
                    res[var] = (a * u, b * u if b is not None else None, et[:60])
            break
    return res

def leer(doc, p):
    f = doc / "fino" / f"pag_{p:03d}.txt"
    return f.read_text(encoding="utf-8", errors="replace") if f.exists() else None

def main():
    OUT.parent.mkdir(exist_ok=True)
    filas = []
    docs = sorted(OCR.glob("*/*/hecho.json"))
    for i, h in enumerate(docs, 1):
        doc = h.parent
        v2 = doc / "paginas_clave_v2.json"
        if v2.exists():
            clave = json.loads(v2.read_text(encoding="utf-8"))["paginas"]; version = "v2"
        else:
            clave = json.loads((doc / "paginas_clave.json").read_text(encoding="utf-8")); version = "v1"
        principales = [t for p in clave.get("resultados", [])[:1] + clave.get("balance", [])[:1]
                       if (t := leer(doc, p))]
        u = unidad_documento(principales) if principales else 1.0
        for bloque, tipo, reglas in (("pyg", "resultados", PYG), ("balance", "balance", BAL), ("personal", "personal", PER)):
            cand = list(clave.get(tipo, []))
            if bloque != "personal":
                # primero las paginas con el titulo del estado en la cabecera (no el informe de administradores)
                tit = TIT_BAL if bloque == "balance" else TIT_PYG
                def cab(p):
                    t = leer(doc, p)
                    return bool(t and re.search(tit, " ".join(t.lower().split()[:60])))
                cand.sort(key=lambda p: 0 if cab(p) else 1)
            hecho = False
            for p in cand:
                t = leer(doc, p)
                if not t:
                    continue
                res = extraer(t, reglas, u)
                minimo = 2 if bloque == "personal" else 3
                if len(res) < minimo and not (bloque == "personal" and res):
                    continue          # la pagina no es el estado buscado: se prueba la siguiente candidata
                if bloque != "personal":
                    sig = leer(doc, p + 1)
                    # solo si la pagina siguiente es continuacion (no otro estado con su propio titulo,
                    # p. ej. el balance de la sociedad despues del consolidado)
                    titulo = TIT_BAL if bloque == "balance" else TIT_PYG
                    if sig and re.search(titulo, " ".join(sig.lower().split()[:60])):
                        sig = None
                    if sig and res:
                        for var, val in extraer(sig, reglas, u).items():
                            res.setdefault(var, val)
                if len(res) >= (2 if bloque == "personal" else 3) or (bloque == "personal" and res):
                    for var, (a, b, et) in res.items():
                        filas.append({"numero": doc.parent.name, "cierre": doc.name[:10], "documento": doc.name,
                                      "bloque": bloque, "variable": var, "actual": a, "anterior": b,
                                      "pagina": p, "etiqueta_ocr": et, "unidad": u, "localizacion": version})
                    hecho = bloque != "personal" or "sueldos_salarios" in res or "gastos_personal" in res
                    if hecho:
                        break
            if bloque == "personal" and not hecho:
                # sin sueldos en las paginas localizadas: se busca la tabla de gastos de personal en todo el
                # documento, exigiendo sueldos y seguridad social o pensiones en la misma pagina
                ya = {r["variable"] for r in filas if r["documento"] == doc.name}
                ing = next((abs(r["actual"]) for r in filas if r["documento"] == doc.name and r["variable"] == "ingresos"), None)
                opciones = []
                for fp in sorted((doc / "fino").glob("pag_*.txt")):
                    p = int(fp.stem[4:])
                    res = extraer(fp.read_text(encoding="utf-8", errors="replace"), PER, u)
                    if "sueldos_salarios" in res and ({"seguridad_social", "pensiones"} & set(res)):
                        opciones.append((abs(res["sueldos_salarios"][0]), p, res))
                if opciones:
                    # la tabla de personal del club es la de mayor importe (las otras son de administradores
                    # o de la sociedad matriz); debe ser plausible frente a los ingresos
                    sue, p, res = max(opciones, key=lambda x: x[0])
                    plausible = sue >= 100 and (ing is None or ing < 100 or 0.15 <= sue / ing <= 3)
                    if plausible:
                        for var, (a, b, et) in res.items():
                            if var not in ya:
                                filas.append({"numero": doc.parent.name, "cierre": doc.name[:10], "documento": doc.name,
                                              "bloque": bloque, "variable": var, "actual": a, "anterior": b,
                                              "pagina": p, "etiqueta_ocr": et, "unidad": u, "localizacion": "busqueda_personal"})
        if i % 250 == 0:
            print(f"{i}/{len(docs)}")
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        w.writeheader(); w.writerows(filas)
    print(f"Listo: {len(filas)} cifras de {len(docs)} documentos -> {OUT}")

if __name__ == "__main__":
    main()

"""
Reglas compartidas de la fase 2 (localizar paginas y leer cifras).
Las usan fase2_ocr_complemento.py y fase2_extraer_cifras.py.

Localizacion: cada pagina recibe una puntuacion por tipo de estado financiero segun
(1) el TITULO en la cabecera de la pagina y (2) la ESTRUCTURA (lineas con cifras que
deben aparecer en ese estado). Se penalizan las paginas de notas, politicas contables
e informes narrativos. Cubre titulos de UK GAAP antiguo, FRS 102 y NIIF.
"""
import re

TIT_PYG = (r"profit and loss account|statement of (total )?comprehensive income|income statement|"
           r"statement of profit or loss|statement of income|income and expenditure|"
           r"statement of (profit|loss)|profit or loss and other comprehensive")
TIT_BAL = r"balance sheet|statement of financial position|statement of net assets"
NOTAS = r"notes to the (financial statements|accounts)|accounting polic|principal accounting|basis of preparation"
NARRATIVO = (r"directors.? report|strategic report|chairman.?s statement|chief executive|"
             r"independent auditor|report of the directors|corporate governance")

def _cabecera(t, n=12):
    """Primeras lineas no vacias (el titulo del estado suele estar ahi)."""
    lineas = [l for l in t.splitlines() if l.strip()]
    return " ".join(lineas[:n]).lower()

def _lineas_con_cifras(t):
    return [l.lower() for l in t.splitlines() if re.search(r"\d{1,3}[,.;: ]\d{3}|\(\d", l)]

def puntuar(texto):
    """Devuelve dict tipo -> puntuacion, y si la pagina es consolidada."""
    t = texto.lower()
    cab = _cabecera(texto, 18)
    num = _lineas_con_cifras(texto)
    unidas = t   # psm 3 separa etiquetas y cifras en columnas: se busca en todo el texto
    p = {}
    pen = 0
    if re.search(NOTAS, cab): pen -= 4
    if re.search(NARRATIVO, cab): pen -= 5
    if len(num) < 5: pen -= 3
    # cuenta de resultados
    s = 0
    if re.search(TIT_PYG, cab): s += 4
    if re.search(r"(t[uo]r?n?m?over|tumover|revenue|income from)", unidas): s += 2
    if re.search(r"before (income )?tax|before taxation|before and after tax", unidas): s += 3
    if re.search(r"(profit|loss|result).{0,40}(for the (financial )?(year|period)|after tax)", unidas): s += 1
    if re.search(r"operating (profit|loss|result|expenses)", unidas): s += 1
    p["resultados"] = s + pen
    # balance
    s = 0
    if re.search(TIT_BAL, cab): s += 4
    if re.search(r"net (current )?(assets|liabilities)|total assets less current", unidas): s += 3
    if re.search(r"creditors|liabilities", unidas): s += 1
    if re.search(r"cash (at bank|and cash)", unidas): s += 1
    if re.search(r"capital and reserves|share capital|total equity|shareholders", t): s += 1
    p["balance"] = s + pen
    # notas (sin penalizacion de notas, claro)
    pen_n = (-5 if re.search(NARRATIVO, cab) else 0) + (-2 if len(num) < 2 else 0)
    p["personal"] = (3 if re.search(r"wages and salaries|staff costs|employment costs", unidas) else 0) \
        + (1 if re.search(r"social security", unidas) else 0) + (1 if re.search(r"average (monthly )?number", t) else 0) + pen_n
    p["acreedores"] = (3 if re.search(r"creditors", t) and re.search(r"within one year|after (more than )?one year", t) else 0) \
        + (1 if re.search(r"transfer fee|player|registration", unidas) else 0) + (1 if re.search(r"bank loan|loans|borrowings", unidas) else 0) + pen_n
    p["deudores"] = (3 if re.search(r"^\s*\d*\.?\s*debtors", t, re.M) else 0) \
        + (1 if re.search(r"transfer fee|player|registration", unidas) else 0) + pen_n
    p["intangibles"] = (3 if re.search(r"intangible", t) and re.search(r"amortisation|amortization", t) else 0) \
        + (1 if re.search(r"player|registration", t) else 0) + pen_n
    p["continuidad"] = 3 if re.search(r"going concern", t) else 0
    p["partes_vinculadas"] = 3 if re.search(r"related part", t) else 0
    p["flujos_caja"] = (3 if re.search(r"cash ?flow", cab) else 0) + (2 if re.search(r"operating activities", t) else 0) + pen
    p["auditor"] = 3 if re.search(r"independent auditor", cab) else 0
    consolidado = bool(re.search(r"consolidated|group", cab)) and not re.search(r"company (balance|statement)", cab)
    return p, consolidado

UMBRAL = {"resultados": 6, "balance": 6, "personal": 3, "acreedores": 3, "deudores": 3,
          "intangibles": 3, "continuidad": 3, "partes_vinculadas": 3, "flujos_caja": 4, "auditor": 3}
MAXIMO = {"resultados": 2, "balance": 2, "personal": 2, "acreedores": 2, "deudores": 1,
          "intangibles": 1, "continuidad": 2, "partes_vinculadas": 1, "flujos_caja": 1, "auditor": 1}

def localizar(textos):
    """textos: dict pagina -> texto (OCR rapido). Devuelve dict tipo -> [paginas] ordenadas
    por preferencia (para resultados y balance: consolidado primero, luego mejor puntuacion),
    y dict de paginas consolidadas."""
    punt = {pg: puntuar(t) for pg, t in textos.items()}
    res, cons = {}, {pg: c for pg, (s, c) in punt.items()}
    for tipo, umbral in UMBRAL.items():
        cand = [(s[tipo], pg) for pg, (s, c) in punt.items() if s[tipo] >= umbral]
        if tipo in ("resultados", "balance"):
            cand.sort(key=lambda x: (-(x[0] + (2 if cons[x[1]] else 0)), x[1]))
        else:
            cand.sort(key=lambda x: (-x[0], x[1]))
        if cand:
            res[tipo] = [pg for _, pg in cand[:MAXIMO[tipo]]]
    return res, cons

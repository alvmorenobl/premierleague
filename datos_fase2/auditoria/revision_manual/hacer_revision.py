"""Tiras para la revision manual dirigida: por cada (documento, pagina) de las cifras clave pendientes,
la cabecera de la tabla y las lineas de la partida. Se agrupan varias tiras por imagen."""
import pandas as pd, numpy as np, os, re, json, subprocess, tempfile, time, sys
from PIL import Image, ImageDraw

T = os.path.expanduser("~/trabajo")
C = os.path.expanduser("~/mnt/datos_premier/cuentas")
O = os.path.expanduser("~/ocrlocal")
OUT = os.path.expanduser("~/mnt/datos_premier/revision")
os.makedirs(OUT, exist_ok=True)
BLOQUE = {"ingresos": "resultados", "resultado_antes_impuestos": "resultados", "activos_netos": "balance", "sueldos_salarios": "personal"}
PAT = {"ingresos": r"(?i)turnover|tumover|revenue",
       "resultado_antes_impuestos": r"(?i)before (income )?tax|before and after",
       "activos_netos": r"(?i)^\W*net (assets|liab|\(liab|deficit)|total equity|shareholders|members.{0,3} (funds|deficit)",
       "sueldos_salarios": r"(?i)wages|staff costs|employment costs|salar"}

q = pd.read_csv(f"{T}/pendientes_revision.csv", dtype={"numero": str})
q = q[~q.tipo.fillna("").str.contains("dormant")].reset_index(drop=True)
inv = pd.read_csv(f"{T}/datos_fase2/inventario_cuentas_limpio.csv", dtype=str)
x = pd.read_csv(f"{T}/datos_fase2/cifras_ocr_largo.csv", dtype={"numero": str})
l = pd.read_csv(f"{T}/datos_fase2/panel_largo.csv", dtype={"numero": str})

# documento de la cuenta t (el elegido por el panel; si no, el AA del inventario)
def doc_de(n, c):
    s = x[(x.numero == n) & (x.cierre == c)]
    if len(s):
        return s.documento.value_counts().index[0]
    s = inv[(inv.numero == n) & (inv.cierre == c)]
    return (s.cierre + "_" + s.transaction_id).iloc[0] if len(s) else None

filas = []
for i, r in q.iterrows():
    d = doc_de(r.numero, r.cierre)
    p = None
    if d:
        e = x[(x.documento == d) & (x.variable == r.variable)]
        if len(e):
            p = int(e.pagina.iloc[0])
        else:
            b = {"resultados": "pyg", "balance": "balance", "personal": "personal"}[BLOQUE[r.variable]]
            e = x[(x.documento == d) & (x.bloque == b)]
            if len(e):
                p = int(e.pagina.iloc[0])
            else:
                f = f"{O}/{r.numero}/{d}/paginas_clave_v2.json"
                if os.path.exists(f):
                    cand = json.load(open(f))["paginas"].get(BLOQUE[r.variable], [])
                    p = cand[0] if cand else None
    s = l[(l.numero == r.numero) & (l.cierre == r.cierre) & (l.variable == r.variable)]
    lect = "" if s.empty else f"leido {s.actual.iloc[0]:,.3f} | comparativo t+1 {s.sig_anterior.iloc[0]:,.3f}"
    filas.append(dict(item=i, numero=r.numero, cierre=r.cierre, club=r.club, rol=r.rol, variable=r.variable,
                      documento=d, pagina=p, lecturas=lect))
it = pd.DataFrame(filas)
it.to_csv(f"{OUT}/items.csv", index=False)

grupos = it[it.pagina.notna()].groupby(["documento", "pagina"])
hechas = set(os.listdir(OUT))
t0 = time.time()
tiras_pend = []
for (d, p), g in grupos:
    nombre = f"t_{d[:10]}_{d[11:19]}_{int(p):03d}.png"
    if nombre in hechas:
        continue
    if time.time() - t0 > 140:
        break
    num = g.numero.iloc[0]
    pdf = f"{C}/{num}/{d}.pdf"
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["pdftoppm", "-r", "150", "-gray", "-f", str(int(p)), "-l", str(int(p)), "-png", "-singlefile", pdf, tmp + "/i"], stderr=subprocess.DEVNULL)
        if not os.path.exists(tmp + "/i.png"):
            continue
        im = Image.open(tmp + "/i.png"); im.load()
        tsv = subprocess.run(["tesseract", tmp + "/i.png", "stdout", "--psm", "6", "tsv"], capture_output=True, text=True).stdout
    lines = {}
    for row in tsv.splitlines()[1:]:
        c = row.split("\t")
        if len(c) < 12 or not c[11].strip():
            continue
        lines.setdefault((c[2], c[3], c[4]), []).append((int(c[7]), int(c[9]), c[11]))
    L2 = sorted((min(w[0] for w in ws), max(w[0] + w[1] for w in ws), " ".join(w[2] for w in ws)) for ws in lines.values())
    hdr = [z for z in L2[:30] if re.search(r"20[0-3]\d|£|000", z[2])][:3]
    bands = [(max(0, a - 6), b + 6) for a, b, _ in hdr]
    for v in g.variable.unique():
        for a, b, t in L2:
            if re.search(PAT[v], t):
                bands.append((max(0, a - 8), b + 8))
    bands = sorted(set(bands))[:12]
    cab = [f"{g.club.iloc[0]} ({g.rol.iloc[0]}) {num} cierre {g.cierre.iloc[0]}  pag {int(p)}  doc {d[:10]}"]
    cab += [f"  item {r.item}: {r.variable}  {r.lecturas}" for r in g.itertuples()]
    crops = [im.crop((0, a, im.width, b)) for a, b in bands] or [im.resize((im.width // 3, im.height // 3))]
    W = max([c.width for c in crops] + [1200]); H = sum(c.height + 3 for c in crops) + 16 * len(cab) + 8
    cv = Image.new("L", (W, H), 255); dr = ImageDraw.Draw(cv); y = 3
    for s in cab:
        dr.text((5, y), s, fill=0); y += 16
    for c in crops:
        cv.paste(c, (0, y)); y += c.height + 3
    cv.save(f"{OUT}/{nombre}")
print("tiras:", len([f for f in os.listdir(OUT) if f.startswith("t_")]), "de", grupos.ngroups, "| items sin pagina:", it.pagina.isna().sum())

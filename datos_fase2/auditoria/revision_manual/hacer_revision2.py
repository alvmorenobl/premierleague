"""Segunda pasada de la revision manual: para cada cifra clave aun pendiente se busca la pagina en todo el
texto OCR (rapido y fino) y se recorta la zona de la partida (o la pagina entera si no se localiza)."""
import pandas as pd, os, re, glob, subprocess, tempfile, time, json
from PIL import Image, ImageDraw

T = os.path.expanduser("~/trabajo"); C = os.path.expanduser("~/mnt/datos_premier/cuentas")
O = os.path.expanduser("~/mnt/datos_premier/ocr"); OUT = os.path.expanduser("~/mnt/datos_premier/revision2")
os.makedirs(OUT, exist_ok=True)
PAT = {"ingresos": r"(?i)\b(turnover|tumover|revenue)\b",
       "resultado_antes_impuestos": r"(?i)before\s+(income\s+)?tax",
       "activos_netos": r"(?i)net\s+(assets|liabilities|\(liabilities\)|deficit)|total\s+equity|shareholders.{0,3}\s+(funds|deficit)",
       "sueldos_salarios": r"(?i)wages|salaries|staff\s+costs|employment\s+costs"}
TIT = {"ingresos": r"(?i)profit and loss|income statement|comprehensive income|statement of profit",
       "resultado_antes_impuestos": r"(?i)profit and loss|income statement|comprehensive income|statement of profit",
       "activos_netos": r"(?i)balance sheet|financial position",
       "sueldos_salarios": r"(?i)staff costs|employees|employment costs|directors"}
NUM = re.compile(r"\(?\d{1,3}(,\d{3})+\)?")
q = pd.read_csv(f"{T}/pendientes2.csv", dtype={"numero": str})
q = q[q.tipo.isin(["full", "group", "audit-exemption-subsiduary"])].reset_index(drop=True)
inv = pd.read_csv(f"{T}/datos_fase2/inventario_cuentas_limpio.csv", dtype=str)

def documento(n, c):
    s = inv[(inv.numero == n) & (inv.cierre == c) & (inv.tipo == "AA")]
    return (s.cierre + "_" + s.transaction_id).iloc[0] if len(s) else None

def pagina(n, d, v):
    mejor = None
    for f in sorted(glob.glob(f"{O}/{n}/{d}/*/pag_*.txt")):
        t = open(f, errors="ignore").read()
        lin = [l for l in t.splitlines() if re.search(PAT[v], l) and NUM.search(l)]
        if not lin:
            continue
        sc = len(lin) + (3 if re.search(TIT[v], t[:600]) else 0) + (2 if "/fino/" in f else 0)
        p = int(re.search(r"pag_(\d+)", f).group(1))
        if mejor is None or sc > mejor[0]:
            mejor = (sc, p)
    return mejor[1] if mejor else None

items = []
for i, r in q.iterrows():
    d = documento(r.numero, r.cierre)
    items.append(dict(item=i, **r.to_dict(), documento=d, pagina=pagina(r.numero, d, r.variable) if d else None))
it = pd.DataFrame(items); it.to_csv(f"{OUT}/items2.csv", index=False)
t0 = time.time()
for (d, p), g in it[it.pagina.notna()].groupby(["documento", "pagina"]):
    nombre = f"s_{d[:10]}_{d[11:19]}_{int(p):03d}.png"
    if os.path.exists(f"{OUT}/{nombre}") or time.time() - t0 > 140:
        continue
    n = g.numero.iloc[0]
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["pdftoppm", "-r", "110", "-gray", "-f", str(int(p)), "-l", str(int(p)), "-png", "-singlefile", f"{C}/{n}/{d}.pdf", tmp + "/i"], stderr=subprocess.DEVNULL)
        if not os.path.exists(tmp + "/i.png"):
            continue
        im = Image.open(tmp + "/i.png"); im.load()
        tsv = subprocess.run(["tesseract", tmp + "/i.png", "stdout", "--psm", "4", "tsv"], capture_output=True, text=True).stdout
    lines = {}
    for row in tsv.splitlines()[1:]:
        c = row.split("\t")
        if len(c) >= 12 and c[11].strip():
            lines.setdefault((c[2], c[3], c[4]), []).append((int(c[7]), int(c[9]), c[11]))
    L = [(min(w[0] for w in ws), max(w[0] + w[1] for w in ws), " ".join(w[2] for w in ws)) for ws in lines.values()]
    pat = "|".join(PAT[v][4:] for v in g.variable.unique())
    hit = [(a, b) for a, b, t in L if re.search("(?i)" + pat, t)]
    if hit:
        top = max(0, min(a for a, _ in hit) - 260); bot = min(im.height, max(b for _, b in hit) + 60)
        im = im.crop((0, top, im.width, bot))
    cab = [f"{g.club.iloc[0]} ({g.rol.iloc[0]}) {n} cierre {g.cierre.iloc[0]} pag {int(p)}"] + [f"  item {r.item}: {r.variable}" for r in g.itertuples()]
    cv = Image.new("L", (im.width, im.height + 16 * len(cab) + 6), 255); dr = ImageDraw.Draw(cv)
    for k, s in enumerate(cab):
        dr.text((5, 3 + 16 * k), s, fill=0)
    cv.paste(im, (0, 16 * len(cab) + 6)); cv.save(f"{OUT}/{nombre}")
print("items", len(it), "sin pagina", it.pagina.isna().sum(), "| imagenes", len(glob.glob(f"{OUT}/s_*.png")), "de", it[it.pagina.notna()].groupby(["documento", "pagina"]).ngroups)

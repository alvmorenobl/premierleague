"""
FASE 2b - Descarga todas las cuentas del inventario.
Lee datos_fase2/inventario_cuentas_limpio.csv y descarga cada documento:
iXBRL (.xhtml) cuando existe, si no PDF.

Los documentos pesan unos 2-3 GB en total, por eso se guardan FUERA de OneDrive
(por defecto en C:\\datos_premier\\cuentas). Para usar otra carpeta:
    python fase2_descarga_cuentas.py D:\\otra\\carpeta

Estructura: <carpeta>/<numero_sociedad>/<cierre>_<transaction_id>.<pdf|xhtml>
Es reanudable: si se corta, se vuelve a lanzar y salta lo ya descargado.
Uso:  python fase2_descarga_cuentas.py   (1-2 horas)
"""
import csv, sys, time
from pathlib import Path
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
import requests

BASE = Path(__file__).resolve().parent
KEY = (BASE / "api-premier-key.text").read_text(encoding="utf-8").strip()
INV = BASE / "datos_fase2" / "inventario_cuentas_limpio.csv"
DEST = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(r"C:\datos_premier\cuentas")
LOG = BASE / "datos_fase2" / "descargas_log.csv"

def get(s, url, **kw):
    for intento in range(5):
        try:
            r = s.get(url, timeout=120, **kw)
        except requests.RequestException as e:
            print("   reintento por error de red:", type(e).__name__); time.sleep(10); continue
        time.sleep(0.55)
        if r.status_code == 429:
            print("   limite de peticiones, espero 60 s"); time.sleep(60); continue
        return r
    return None

def main():
    DEST.mkdir(parents=True, exist_ok=True)
    filas = list(csv.DictReader(open(INV, encoding="utf-8")))
    s = requests.Session(); s.auth = (KEY, "")
    nuevo_log = not LOG.exists()
    lf = open(LOG, "a", newline="", encoding="utf-8")
    lw = csv.writer(lf)
    if nuevo_log:
        lw.writerow(["numero", "cierre", "transaction_id", "formato", "archivo", "bytes", "estado"])
    total, hechas, fallos = len(filas), 0, 0
    for i, f in enumerate(filas, 1):
        ext = "xhtml" if f["formato"] == "ixbrl" else "pdf"
        mime = "application/xhtml+xml" if ext == "xhtml" else "application/pdf"
        destino = DEST / f["numero"] / f"{f['cierre']}_{f['transaction_id']}.{ext}"
        if destino.exists() and destino.stat().st_size > 0:
            continue
        if not f["metadata_url"]:
            continue
        destino.parent.mkdir(exist_ok=True)
        print(f"[{i}/{total}] {f['club']} {f['cierre']} ({ext})")
        r = get(s, f["metadata_url"].rstrip("/") + "/content", headers={"Accept": mime})
        if r is None or r.status_code != 200 or not r.content:
            fallos += 1
            estado = "fallo" if r is None else f"http_{r.status_code}"
            print("   ", estado)
            lw.writerow([f["numero"], f["cierre"], f["transaction_id"], ext, "", 0, estado]); lf.flush()
            continue
        tmp = destino.with_suffix(destino.suffix + ".part")
        tmp.write_bytes(r.content); tmp.replace(destino)
        hechas += 1
        lw.writerow([f["numero"], f["cierre"], f["transaction_id"], ext, str(destino), len(r.content), "ok"]); lf.flush()
    lf.close()
    print(f"\nListo: {hechas} nuevas, {fallos} fallos. Carpeta: {DEST}")

if __name__ == "__main__":
    main()

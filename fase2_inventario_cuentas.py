"""
FASE 2a - Inventario de cuentas (sin descargar documentos todavia).
Para cada sociedad de datos_fase1/mapa_sociedades.csv (club y grupo) lista
todas las cuentas depositadas: fecha de cierre, fecha de deposito, tipo y en
que formatos estan (XHTML/iXBRL legible por maquina o PDF escaneado).
Sirve para saber cuanto hay que descargar y cuanto necesitara OCR.

Salida: datos_fase2/inventario_cuentas.csv
Uso:  python fase2_inventario_cuentas.py   (10-15 minutos; se puede relanzar,
      continua donde se quedo)
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
API = "https://api.company-information.service.gov.uk"
MAPA = BASE / "datos_fase1" / "mapa_sociedades.csv"
OUT = BASE / "datos_fase2" / "inventario_cuentas.csv"
DESDE = "2009-01-01"   # cuentas cerradas desde 2009 (cubre la temporada 2010/11 con retardo)
CAMPOS = ["club", "rol", "numero", "cierre", "depositada", "tipo", "descripcion",
          "paginas", "xhtml", "pdf", "metadata_url", "transaction_id"]

def get(s, url, params=None):
    for _ in range(4):
        try:
            r = s.get(url, params=params, timeout=30)
        except requests.RequestException:
            time.sleep(5); continue
        time.sleep(0.55)
        if r.status_code == 429:
            print("   limite de peticiones, espero 60 s"); time.sleep(60); continue
        return r
    return None

def main():
    OUT.parent.mkdir(exist_ok=True)
    hechas = set()
    if OUT.exists():
        with open(OUT, encoding="utf-8") as f:
            hechas = {r["numero"] for r in csv.DictReader(f)}
    soc = {}
    with open(MAPA, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            for rol, col in (("club", "numero_club"), ("grupo", "numero_grupo")):
                n = r[col].strip()
                if n and n not in soc:
                    soc[n] = (r["club"], rol)
    nueva = not OUT.exists()
    fh = open(OUT, "a", newline="", encoding="utf-8")
    w = csv.DictWriter(fh, fieldnames=CAMPOS)
    if nueva:
        w.writeheader()
    s = requests.Session(); s.auth = (KEY, "")
    for i, (num, (club, rol)) in enumerate(soc.items(), 1):
        if num in hechas:
            continue
        print(f"[{i}/{len(soc)}] {club} ({rol}) {num}")
        items, start = [], 0
        while True:
            r = get(s, f"{API}/company/{num}/filing-history",
                    {"category": "accounts", "items_per_page": 100, "start_index": start})
            if r is None or r.status_code != 200:
                print("   sin historial", None if r is None else r.status_code); break
            j = r.json(); lote = j.get("items", [])
            items += lote; start += len(lote)
            if not lote or start >= j.get("total_count", 0):
                break
        n = 0
        for it in items:
            cierre = (it.get("description_values") or {}).get("made_up_date", "")
            if cierre and cierre < DESDE:
                continue
            meta = (it.get("links") or {}).get("document_metadata", "")
            xhtml = pdf = ""
            if meta:
                m = get(s, meta)
                if m is not None and m.status_code == 200:
                    res = m.json().get("resources", {}) or {}
                    xhtml = "si" if "application/xhtml+xml" in res else "no"
                    pdf = "si" if "application/pdf" in res else "no"
            w.writerow({"club": club, "rol": rol, "numero": num, "cierre": cierre,
                        "depositada": it.get("date", ""), "tipo": it.get("type", ""),
                        "descripcion": it.get("description", ""), "paginas": it.get("pages", ""),
                        "xhtml": xhtml, "pdf": pdf, "metadata_url": meta,
                        "transaction_id": it.get("transaction_id", "")})
            n += 1
        fh.flush()
        print(f"   {n} cuentas")
    fh.close()
    print(f"\nListo: {OUT}")

if __name__ == "__main__":
    main()

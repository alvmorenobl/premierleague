"""
FASE 1b - Busca las sociedades que no salieron en fase1_sociedades.py
(cambios de nombre, administraciones, sociedades antiguas liquidadas).

Salida: datos_fase1/candidatos_pendientes.csv
Uso:  python fase1_sociedades_pendientes.py   (1-2 minutos)
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
OUT = BASE / "datos_fase1" / "candidatos_pendientes.csv"
API = "https://api.company-information.service.gov.uk"

# club -> busquedas (texto exacto aproximado del nombre oficial)
BUSQUEDAS = {
    "Bolton": ["Bolton Wanderers Football and Athletic Company", "Football Ventures (Whites)"],
    "Burton": ["Burton Albion Football Club", "Burton Albion"],
    "Crystal Palace": ["CPFC Limited", "Crystal Palace Football Club"],
    "Derby": ["Derby County Football Club Limited", "Gellaw Newco"],
    "Milton Keynes Dons": ["MK Dons", "Milton Keynes Dons"],
    "Portsmouth": ["Portsmouth Community Football Club"],
    "Wigan": ["Wigan Athletic AFC Limited", "Wigan Athletic Football Club"],
    "Wrexham": ["Wrexham AFC Limited", "Wrexham A.F.C."],
    "Yeovil": ["Yeovil Town Football Club", "Yeovil Town"],
    "Tottenham": ["Tottenham Hotspur Football & Athletic"],
    "Aston Villa": ["Aston Villa Football Club Limited", "Aston Villa Limited"],
}
CAMPOS = ["club", "busqueda", "numero", "nombre", "estado", "creada", "disuelta",
          "actividad_sic", "ultimas_cuentas_cierre", "ultimas_cuentas_tipo",
          "historial_insolvencia", "nombres_anteriores"]

def get(s, url, params=None):
    for _ in range(3):
        r = s.get(url, params=params, timeout=30)
        time.sleep(0.6)
        if r.status_code == 429:
            time.sleep(60); continue
        return r
    return r

def main():
    s = requests.Session(); s.auth = (KEY, "")
    filas, vistos = [], set()
    for club, qs in BUSQUEDAS.items():
        print(club)
        palabra = club.split()[0].upper().replace("NOTT'M", "NOTTINGHAM")
        for q in qs:
            r = get(s, f"{API}/search/companies", {"q": q, "items_per_page": 20})
            if r.status_code != 200:
                print("   error", r.status_code); continue
            for it in r.json().get("items", []):
                num = it.get("company_number", "")
                t = (it.get("title") or "").upper()
                if (club, num) in vistos or not num[:1].isdigit():
                    continue
                if not any(w in t for w in [palabra, "CPFC", "MK DONS", "FOOTBALL VENTURES", "GELLAW"]):
                    continue
                vistos.add((club, num))
                p = get(s, f"{API}/company/{num}")
                pj = p.json() if p.status_code == 200 else {}
                acc = (pj.get("accounts") or {}).get("last_accounts") or {}
                filas.append({
                    "club": club, "busqueda": q, "numero": num,
                    "nombre": pj.get("company_name", t),
                    "estado": pj.get("company_status", ""),
                    "creada": pj.get("date_of_creation", ""),
                    "disuelta": pj.get("date_of_cessation", ""),
                    "actividad_sic": ";".join(pj.get("sic_codes", []) or []),
                    "ultimas_cuentas_cierre": acc.get("made_up_to", ""),
                    "ultimas_cuentas_tipo": acc.get("type", ""),
                    "historial_insolvencia": pj.get("has_insolvency_history", ""),
                    "nombres_anteriores": " | ".join(
                        f"{x.get('name')} ({x.get('effective_from')} a {x.get('ceased_on')})"
                        for x in pj.get("previous_company_names", []) or []),
                })
                print("  ", num, filas[-1]["nombre"], filas[-1]["estado"])
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS); w.writeheader(); w.writerows(filas)
    print(f"\nListo: {len(filas)} candidatos en {OUT}")

if __name__ == "__main__":
    main()

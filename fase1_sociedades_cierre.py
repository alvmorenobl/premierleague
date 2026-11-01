"""
FASE 1c - Cierra el mapa club -> sociedad.
 1) Busqueda avanzada (incluye sociedades disueltas/liquidadas) para las
    sociedades antiguas de Bolton, Derby y Wigan.
 2) Quien controla a quien (persons-with-significant-control) para los casos
    dudosos: asi se ve la cadena club -> holding -> propietario.

Salidas: datos_fase1/antiguas.csv y datos_fase1/control_psc.csv
Uso:  python fase1_sociedades_cierre.py   (menos de 1 minuto)
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
D = BASE / "datos_fase1"

ANTIGUAS = {
    "Bolton": "BOLTON WANDERERS FOOTBALL",
    "Derby": "DERBY COUNTY FOOTBALL CLUB",
    "Wigan": "WIGAN ATHLETIC",
}
PSC = ["03375789", "02502822", "00046572",            # Aston Villa
       "00057186", "06279984", "01706358", "10443734",  # Tottenham
       "00488096",                                      # Burton
       "11761052",                                      # Bolton (grupo)
       "00189754", "07113379"]                          # Yeovil

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
    filas = []
    for club, nombre in ANTIGUAS.items():
        print(club)
        r = get(s, f"{API}/advanced-search/companies",
                {"company_name_includes": nombre, "size": 100})
        if r.status_code != 200:
            print("   error", r.status_code, r.text[:200]); continue
        for it in r.json().get("items", []):
            f = {"club": club, "numero": it.get("company_number"),
                 "nombre": it.get("company_name"), "estado": it.get("company_status"),
                 "creada": it.get("date_of_creation", ""), "disuelta": it.get("date_of_cessation", ""),
                 "sic": ";".join(it.get("sic_codes", []) or [])}
            filas.append(f)
            print("  ", f["numero"], f["nombre"], f["estado"], f["creada"], f["disuelta"])
    with open(D / "antiguas.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["club", "numero", "nombre", "estado", "creada", "disuelta", "sic"])
        w.writeheader(); w.writerows(filas)

    psc = []
    print("\nQuien controla cada sociedad:")
    for num in PSC:
        r = get(s, f"{API}/company/{num}/persons-with-significant-control")
        items = r.json().get("items", []) if r.status_code == 200 else []
        if not items:
            print("  ", num, "-> sin datos", r.status_code)
        for it in items:
            ident = it.get("identification") or {}
            p = {"numero": num, "controlador": it.get("name"), "tipo": it.get("kind"),
                 "numero_controlador": ident.get("registration_number", ""),
                 "pais": ident.get("country_registered", "") or ident.get("place_registered", ""),
                 "desde": it.get("notified_on", ""), "hasta": it.get("ceased_on", ""),
                 "naturaleza": ";".join(it.get("natures_of_control", []) or [])}
            psc.append(p)
            print("  ", num, "->", p["controlador"], p["numero_controlador"], p["desde"], p["hasta"])
    with open(D / "control_psc.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(psc[0].keys()) if psc else ["numero"])
        w.writeheader(); w.writerows(psc)
    print("\nListo: datos_fase1/antiguas.csv y datos_fase1/control_psc.csv")

if __name__ == "__main__":
    main()

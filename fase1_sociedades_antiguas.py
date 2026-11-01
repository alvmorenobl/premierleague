"""
FASE 1d - Encuentra las sociedades antiguas de Bolton, Derby y Wigan.
En una administracion la sociedad vieja suele cambiar de nombre (p. ej.
"... Realisations Limited"), por eso no sale buscando por el nombre del club.
Se localizan a traves de sus antiguos directivos: se busca a la persona y se
listan todas las sociedades en las que fue administrador.

Salida: datos_fase1/sociedades_via_directivos.csv
Uso:  python fase1_sociedades_antiguas.py   (1 minuto)
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
OUT = BASE / "datos_fase1" / "sociedades_via_directivos.csv"

# club -> antiguos directivos conocidos
PERSONAS = {
    "Bolton": ["Ken Anderson", "Phil Gartside", "Eddie Davies"],
    "Derby": ["Melvyn Morris", "Stephen Pearce"],
    "Wigan": ["David Whelan", "Jonathan Jackson", "Au Yeung Wai Kay"],
}
PISTAS = ["FOOTBALL", "ATHLETIC", "WANDERERS", "COUNTY", "REALISATION", "WIGAN", "BOLTON", "DERBY", "BWFC", "DCFC"]

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
    for club, personas in PERSONAS.items():
        print(club)
        for nombre in personas:
            r = get(s, f"{API}/search/officers", {"q": nombre, "items_per_page": 10})
            if r.status_code != 200:
                print("   error", r.status_code); continue
            for of in r.json().get("items", [])[:6]:
                link = (of.get("links") or {}).get("self", "")
                if "/appointments" not in link:
                    continue
                a = get(s, API + link, {"items_per_page": 50})
                if a.status_code != 200:
                    continue
                for ap in a.json().get("items", []):
                    to = ap.get("appointed_to") or {}
                    num, nom = to.get("company_number", ""), (to.get("company_name") or "").upper()
                    if not any(p in nom for p in PISTAS) or (club, num) in vistos:
                        continue
                    vistos.add((club, num))
                    f = {"club": club, "directivo": of.get("title"), "numero": num, "nombre": nom,
                         "estado": to.get("company_status", ""), "cargo": ap.get("officer_role", ""),
                         "nombrado": ap.get("appointed_on", ""), "cese": ap.get("resigned_on", "")}
                    filas.append(f)
                    print("  ", num, nom, f["estado"], "|", f["directivo"], f["nombrado"], "-", f["cese"])
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["club", "directivo", "numero", "nombre", "estado", "cargo", "nombrado", "cese"])
        w.writeheader(); w.writerows(filas)
    print(f"\nListo: {len(filas)} sociedades en {OUT}")

if __name__ == "__main__":
    main()

"""
FASE 2h - Busca las sociedades matriz (grupo) de Arsenal y Chelsea, que no estaban en el mapa.

El contraste externo (Deloitte, prensa) usa las cuentas consolidadas del grupo, mientras que el panel solo tenia
la sociedad del club. Este script:
  1) busca por nombre las posibles matrices (incluidas las disueltas);
  2) sube por la cadena de control (PSC) desde la sociedad del club;
  3) para cada candidata, lista sus cuentas anuales (tipo y fecha), para ver cuales consolidan ('group').

Salida: datos_fase1/matrices_candidatas.csv  (no modifica el mapa: eso se decide revisando la salida)
Uso:    python fase2_matrices.py   (1-2 minutos)
"""
import csv, sys, time
from pathlib import Path
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
import requests

BASE = Path(__file__).resolve().parent
API = "https://api.company-information.service.gov.uk"
KEY = (BASE / "api-premier-key.text").read_text(encoding="utf-8").strip()

BUSQUEDAS = {
    "Arsenal": ["ARSENAL HOLDINGS", "KSE UK"],
    "Chelsea": ["CHELSEA FC HOLDINGS", "CHELSEA FOOTBALL CLUB HOLDINGS", "FORDSTAM", "BLUECO 22", "CHELSEA FC PLC"],
}
CLUB = {"Arsenal": "00109244", "Chelsea": "01965149"}

def get(s, url, params=None):
    for _ in range(3):
        r = s.get(url, params=params, timeout=30)
        time.sleep(0.6)
        if r.status_code == 429:
            time.sleep(60); continue
        return r
    return r

def cuentas(s, numero):
    r = get(s, f"{API}/company/{numero}/filing-history", {"category": "accounts", "items_per_page": 100})
    if r.status_code != 200:
        return []
    return [(it.get("description", ""), (it.get("description_values") or {}).get("made_up_date", ""))
            for it in r.json().get("items", []) if it.get("type") == "AA"]

def main():
    s = requests.Session(); s.auth = (KEY, "")
    cand = {}
    for club, nombres in BUSQUEDAS.items():
        for nombre in nombres:
            r = get(s, f"{API}/advanced-search/companies", {"company_name_includes": nombre, "size": 50})
            if r.status_code != 200:
                print("  error", nombre, r.status_code); continue
            for it in r.json().get("items", []):
                cand[it["company_number"]] = dict(club=club, numero=it["company_number"], nombre=it.get("company_name"),
                                                  estado=it.get("company_status"), creada=it.get("date_of_creation", ""),
                                                  disuelta=it.get("date_of_cessation", ""), via="nombre")
        # cadena de control desde la sociedad del club (hasta 4 niveles)
        numero = CLUB[club]
        for nivel in range(4):
            r = get(s, f"{API}/company/{numero}/persons-with-significant-control")
            if r.status_code != 200:
                break
            sig = None
            for it in r.json().get("items", []):
                reg = (it.get("identification") or {}).get("registration_number", "")
                pais = (it.get("identification") or {}).get("country_registered", "")
                print(f"  {club} nivel {nivel}: {numero} controlada por {it.get('name')} ({reg} {pais}) desde {it.get('notified_on')} hasta {it.get('ceased_on', '')}")
                if reg and reg not in cand and reg.isalnum():
                    cand[reg] = dict(club=club, numero=reg.zfill(8) if reg.isdigit() else reg, nombre=it.get("name"),
                                     estado="", creada="", disuelta="", via=f"PSC nivel {nivel}")
                if reg and not it.get("ceased_on"):
                    sig = reg.zfill(8) if reg.isdigit() else reg
            if not sig:
                break
            numero = sig
    filas = []
    for c in cand.values():
        cs = cuentas(s, c["numero"])
        c["n_cuentas"] = len(cs)
        c["n_group"] = sum("group" in d for d, _ in cs)
        c["primera"] = min((f for _, f in cs if f), default="")
        c["ultima"] = max((f for _, f in cs if f), default="")
        c["tipos"] = ";".join(sorted({d.replace("accounts-with-accounts-type-", "") for d, _ in cs}))
        filas.append(c)
        print(f"{c['club']:8s} {c['numero']:10s} {str(c['nombre'])[:45]:45s} {c['estado']:10s} cuentas={c['n_cuentas']:3d} group={c['n_group']:3d} {c['primera']}..{c['ultima']}  ({c['via']})")
    out = BASE / "datos_fase1" / "matrices_candidatas.csv"
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(filas[0].keys())); w.writeheader(); w.writerows(filas)
    print("->", out)

if __name__ == "__main__":
    main()

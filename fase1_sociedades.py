"""
FASE 1 - Busca en Companies House las sociedades candidatas de cada club
(62 clubes que han estado en Premier o Championship entre 2010/11 y 2026/27).

Para cada club: busca por nombre, filtra candidatos que contengan el nombre del
club y descarga el perfil de cada candidato (estado, fecha de creacion, actividad,
ultimas cuentas y su tipo). NO decide: propone, y la decision se revisa a mano.

Salida: datos_fase1/candidatos_sociedades.csv  (una fila por candidato)

Uso (Anaconda Prompt, en la carpeta del proyecto):  python fase1_sociedades.py
Tarda unos 5-8 minutos (respeta el limite de peticiones de la API).
"""
import csv, sys, time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
try:
    import requests
except ImportError:
    sys.exit("Falta 'requests': pip install requests")

BASE = Path(__file__).resolve().parent
KEY_FILE = BASE / "api-premier-key.text"
OUT = BASE / "datos_fase1" / "candidatos_sociedades.csv"
API = "https://api.company-information.service.gov.uk"
PAUSA = 0.6
MAX_CANDIDATOS = 8

# club (nombre en los datos de resultados) -> (texto de busqueda, fragmentos que debe contener el nombre oficial)
CLUBES = {
    "Arsenal": ("Arsenal Football Club", ["ARSENAL"]),
    "Aston Villa": ("Aston Villa Football Club", ["ASTON VILLA"]),
    "Barnsley": ("Barnsley Football Club", ["BARNSLEY"]),
    "Birmingham": ("Birmingham City Football Club", ["BIRMINGHAM CITY"]),
    "Blackburn": ("Blackburn Rovers Football", ["BLACKBURN ROVERS"]),
    "Blackpool": ("Blackpool Football Club", ["BLACKPOOL"]),
    "Bolton": ("Bolton Wanderers Football Club", ["BOLTON WANDERERS"]),
    "Bournemouth": ("AFC Bournemouth", ["BOURNEMOUTH"]),
    "Brentford": ("Brentford FC", ["BRENTFORD"]),
    "Brighton": ("Brighton and Hove Albion Football Club", ["BRIGHTON"]),
    "Bristol City": ("Bristol City Football Club", ["BRISTOL CITY"]),
    "Burnley": ("Burnley Football", ["BURNLEY"]),
    "Burton": ("Burton Albion Football Club", ["BURTON ALBION"]),
    "Cardiff": ("Cardiff City Football Club", ["CARDIFF CITY"]),
    "Charlton": ("Charlton Athletic Football Club", ["CHARLTON ATHLETIC"]),
    "Chelsea": ("Chelsea Football Club", ["CHELSEA"]),
    "Coventry": ("Coventry City Football Club", ["COVENTRY CITY"]),
    "Crystal Palace": ("Crystal Palace Football Club", ["CRYSTAL PALACE"]),
    "Derby": ("Derby County Football Club", ["DERBY COUNTY"]),
    "Doncaster": ("Doncaster Rovers Football Club", ["DONCASTER ROVERS"]),
    "Everton": ("Everton Football Club Company", ["EVERTON"]),
    "Fulham": ("Fulham Football Club", ["FULHAM"]),
    "Huddersfield": ("Huddersfield Town Association Football Club", ["HUDDERSFIELD TOWN"]),
    "Hull": ("Hull City Tigers", ["HULL CITY"]),
    "Ipswich": ("Ipswich Town Football Club", ["IPSWICH TOWN"]),
    "Leeds": ("Leeds United Football Club", ["LEEDS UNITED"]),
    "Leicester": ("Leicester City Football Club", ["LEICESTER CITY"]),
    "Lincoln": ("Lincoln City Football Club", ["LINCOLN CITY"]),
    "Liverpool": ("Liverpool Football Club and Athletic Grounds", ["LIVERPOOL FOOTBALL CLUB"]),
    "Luton": ("Luton Town Football Club", ["LUTON TOWN"]),
    "Man City": ("Manchester City Football Club", ["MANCHESTER CITY"]),
    "Man United": ("Manchester United Football Club", ["MANCHESTER UNITED"]),
    "Middlesbrough": ("Middlesbrough Football and Athletic Company", ["MIDDLESBROUGH"]),
    "Millwall": ("Millwall Football Club", ["MILLWALL"]),
    "Milton Keynes Dons": ("MK Dons", ["MK DONS", "MILTON KEYNES DONS"]),
    "Newcastle": ("Newcastle United Football Company", ["NEWCASTLE UNITED"]),
    "Norwich": ("Norwich City Football Club", ["NORWICH CITY"]),
    "Nott'm Forest": ("Nottingham Forest Football Club", ["NOTTINGHAM FOREST"]),
    "Oxford": ("Oxford United Football Club", ["OXFORD UNITED"]),
    "Peterboro": ("Peterborough United Football Club", ["PETERBOROUGH UNITED"]),
    "Plymouth": ("Plymouth Argyle Football Club", ["PLYMOUTH ARGYLE"]),
    "Portsmouth": ("Portsmouth Football Club", ["PORTSMOUTH"]),
    "Preston": ("Preston North End Football Club", ["PRESTON NORTH END"]),
    "QPR": ("Queens Park Rangers Football", ["QUEENS PARK RANGERS"]),
    "Reading": ("Reading Football Club", ["READING FOOTBALL CLUB"]),
    "Rotherham": ("Rotherham United Football Club", ["ROTHERHAM UNITED"]),
    "Scunthorpe": ("Scunthorpe United Football Club", ["SCUNTHORPE UNITED"]),
    "Sheffield United": ("Sheffield United Football Club", ["SHEFFIELD UNITED"]),
    "Sheffield Weds": ("Sheffield Wednesday Football Club", ["SHEFFIELD WEDNESDAY"]),
    "Southampton": ("Southampton Football Club", ["SOUTHAMPTON"]),
    "Stoke": ("Stoke City Football Club", ["STOKE CITY"]),
    "Sunderland": ("Sunderland Association Football Club", ["SUNDERLAND"]),
    "Swansea": ("Swansea City Association Football Club", ["SWANSEA CITY"]),
    "Tottenham": ("Tottenham Hotspur Football", ["TOTTENHAM HOTSPUR"]),
    "Watford": ("Watford Association Football Club", ["WATFORD"]),
    "West Brom": ("West Bromwich Albion Football Club", ["WEST BROMWICH ALBION"]),
    "West Ham": ("West Ham United Football Club", ["WEST HAM UNITED"]),
    "Wigan": ("Wigan Athletic", ["WIGAN ATHLETIC"]),
    "Wolves": ("Wolverhampton Wanderers Football Club", ["WOLVERHAMPTON WANDERERS"]),
    "Wrexham": ("Wrexham Association Football Club", ["WREXHAM"]),
    "Wycombe": ("Wycombe Wanderers Football Club", ["WYCOMBE WANDERERS"]),
    "Yeovil": ("Yeovil Town Football Club", ["YEOVIL TOWN"]),
}

# Palabras que suelen indicar que NO es la sociedad que gestiona el primer equipo
EXCLUIR = ["FOUNDATION", "TRUST", "COMMUNITY", "SUPPORTERS", "LADIES", "WOMEN", "ACADEMY",
           "CHARIT", "FANS", "SHAREHOLDERS", "SOCIETY", "LOTTERY", "EX PLAYERS", "VETERANS"]


def leer_clave():
    clave = KEY_FILE.read_text(encoding="utf-8-sig").strip()
    if not clave:
        sys.exit("Clave vacia")
    return clave


def get(s, url, params=None):
    for _ in range(3):
        r = s.get(url, params=params, timeout=60)
        time.sleep(PAUSA)
        if r.status_code == 429:
            print("   limite alcanzado, espero 60 s"); time.sleep(60); continue
        return r
    return r


def main():
    s = requests.Session(); s.auth = (leer_clave(), "")
    filas = []
    for i, (club, (q, frags)) in enumerate(CLUBES.items(), 1):
        print(f"[{i}/{len(CLUBES)}] {club}")
        r = get(s, f"{API}/search/companies", {"q": q, "items_per_page": 30})
        items = r.json().get("items", []) if r.status_code == 200 else []
        cand = [c for c in items if any(f in (c.get("title") or "").upper() for f in frags)]
        cand = [c for c in cand if not any(x in (c.get("title") or "").upper() for x in EXCLUIR)]
        for c in cand[:MAX_CANDIDATOS]:
            num = c.get("company_number")
            p = get(s, f"{API}/company/{num}")
            perfil = p.json() if p.status_code == 200 else {}
            cuentas = (perfil.get("accounts") or {})
            ult = cuentas.get("last_accounts") or {}
            filas.append({
                "club": club,
                "numero": num,
                "nombre": perfil.get("company_name") or c.get("title"),
                "estado": perfil.get("company_status"),
                "tipo": perfil.get("type"),
                "creada": perfil.get("date_of_creation"),
                "disuelta": perfil.get("date_of_cessation", ""),
                "actividad_sic": ";".join(perfil.get("sic_codes", []) or []),
                "es_club_futbol_sic_93120": "93120" in (perfil.get("sic_codes") or []),
                "ultimas_cuentas_cierre": ult.get("made_up_to", ""),
                "ultimas_cuentas_tipo": ult.get("type", ""),
                "cuentas_vencidas": cuentas.get("overdue", ""),
                "tiene_prestamos_garantizados": perfil.get("has_charges", ""),
                "historial_insolvencia": perfil.get("has_insolvency_history", ""),
                "localidad": (perfil.get("registered_office_address") or {}).get("locality", ""),
            })
        print(f"   {len(cand[:MAX_CANDIDATOS])} candidatos")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=list(filas[0].keys()))
        w.writeheader(); w.writerows(filas)
    print(f"\nListo: {len(filas)} candidatos en {OUT}")


if __name__ == "__main__":
    main()

"""
FASE 0 - Prueba de viabilidad con la API de Companies House
Proyecto: Riesgo financiero individual y sistemico en el futbol ingles

Que hace este script, para 4 clubes de prueba:
  1. Comprueba que la clave de la API funciona.
  2. Busca la sociedad de cada club y guarda los candidatos (para revisarlos).
  3. Descarga: perfil de la empresa, historial de cuentas, prestamos garantizados
     (charges) y administradores (officers).
  4. Descarga las 3 cuentas anuales mas recientes, en iXBRL si existe (legible
     por maquina) o en PDF si no.
  5. Extrae todas las cifras etiquetadas de los iXBRL a una tabla CSV.
  6. Escribe un informe resumen en informe_fase0.txt

Como ejecutarlo (Anaconda Prompt):
  cd %USERPROFILE%\\OneDrive\\proyecto-premier
  python fase0_prueba.py

La clave se lee del archivo api-premier-key.text de esta carpeta.
No escribas la clave dentro de este codigo.
"""
import csv
import json
import sys
import time
from datetime import date
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

try:
    import requests
except ImportError:
    sys.exit("Falta la libreria 'requests'. Instalala con:  pip install requests")

try:
    from bs4 import BeautifulSoup
except ImportError:
    sys.exit("Falta la libreria 'beautifulsoup4'. Instalala con:  pip install beautifulsoup4")

# ---------------------------------------------------------------------------
# Configuracion
# ---------------------------------------------------------------------------
BASE = Path(__file__).resolve().parent
KEY_FILE = BASE / "api-premier-key.text"
OUT = BASE / "datos_fase0"
API = "https://api.company-information.service.gov.uk"
PAUSA = 0.6          # segundos entre peticiones (limite oficial: 600 cada 5 minutos)
N_CUENTAS = 3        # cuantas cuentas anuales descargar por club

# Para cada club: texto de busqueda y fragmentos que debe contener el nombre oficial
CLUBES = {
    "sheffield_wednesday": {
        "buscar": "Sheffield Wednesday Football Club Limited",
        "contiene": ["SHEFFIELD WEDNESDAY FOOTBALL CLUB"],
    },
    "everton": {
        "buscar": "Everton Football Club Company Limited",
        "contiene": ["EVERTON FOOTBALL CLUB"],
    },
    "brentford": {
        "buscar": "Brentford FC Limited",
        "contiene": ["BRENTFORD FC", "BRENTFORD FOOTBALL CLUB"],
    },
    "liverpool": {
        "buscar": "Liverpool Football Club and Athletic Grounds Limited",
        "contiene": ["LIVERPOOL FOOTBALL CLUB AND ATHLETIC GROUNDS"],
    },
}

# Conceptos contables que nos interesan para el resumen (busqueda por texto en el nombre del concepto)
CONCEPTOS_CLAVE = [
    "TurnoverRevenue", "Revenue", "WagesSalaries", "StaffCosts", "EmployeeBenefitsExpense",
    "ProfitLossOnOrdinaryActivitiesBeforeTax", "ProfitLossBeforeTax", "ProfitLoss",
    "OperatingProfitLoss", "CashBankOnHand", "CashCashEquivalents", "NetAssetsLiabilities",
    "Equity", "NetCurrentAssetsLiabilities", "Creditors", "TotalAssetsLessCurrentLiabilities",
    "IntangibleAssets", "AmortisationExpenseIntangibleAssets", "AmortisationImpairmentExpenseIntangibleAssets",
]


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def leer_clave() -> str:
    if not KEY_FILE.exists():
        sys.exit(f"No encuentro el archivo de la clave: {KEY_FILE}")
    clave = KEY_FILE.read_text(encoding="utf-8-sig").strip()
    if not clave:
        sys.exit("El archivo de la clave esta vacio.")
    return clave


def crear_sesion(clave: str) -> requests.Session:
    s = requests.Session()
    s.auth = (clave, "")   # la API usa la clave como usuario y contrasena vacia
    return s


def get(s, url, params=None, accept=None):
    """GET con pausa entre peticiones y reintento si se alcanza el limite (429)."""
    headers = {"Accept": accept} if accept else {}
    r = None
    for _ in range(3):
        r = s.get(url, params=params, headers=headers, timeout=90)
        time.sleep(PAUSA)
        if r.status_code == 429:
            print("   Limite de peticiones alcanzado, espero 60 segundos...")
            time.sleep(60)
            continue
        return r
    return r


def guardar_json(ruta: Path, datos):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(datos, indent=2, ensure_ascii=False), encoding="utf-8")


def a_numero(texto, escala, signo):
    """Convierte el texto de una cifra iXBRL a numero (comas, guiones, escala y signo)."""
    t = (texto or "").strip().replace(",", "").replace(" ", "").replace(" ", "")
    if t in ("", "-", "–", "—", "nil"):
        valor = 0.0
    else:
        t = t.strip("()")
        try:
            valor = float(t)
        except ValueError:
            return None
    if escala:
        try:
            valor *= 10 ** int(escala)
        except ValueError:
            pass
    if signo == "-":
        valor = -valor
    return valor


def extraer_ixbrl(ruta: Path):
    """Devuelve una lista de cifras etiquetadas (ix:nonFraction) con su periodo."""
    sopa = BeautifulSoup(ruta.read_bytes(), "html.parser")
    # Mapa contexto -> fecha de cierre del periodo
    contextos = {}
    for c in sopa.find_all("xbrli:context"):
        fin = c.find("xbrli:enddate") or c.find("xbrli:instant")
        contextos[c.get("id")] = fin.get_text(strip=True) if fin else ""
    filas = []
    for tag in sopa.find_all("ix:nonfraction"):
        nombre = tag.get("name", "")
        ctx = tag.get("contextref", "")
        filas.append({
            "concepto": nombre.split(":")[-1],
            "concepto_completo": nombre,
            "contexto": ctx,
            "fecha_periodo": contextos.get(ctx, ""),
            "valor": a_numero(tag.get_text(), tag.get("scale"), tag.get("sign")),
            "texto_original": tag.get_text(strip=True),
        })
    return filas


def dias_entre(a: str, b: str):
    try:
        return (date.fromisoformat(b) - date.fromisoformat(a)).days
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Programa principal
# ---------------------------------------------------------------------------
def main():
    OUT.mkdir(exist_ok=True)
    s = crear_sesion(leer_clave())
    informe = []

    # 1. Comprobar la clave
    print("1) Comprobando la clave con la API...")
    r = get(s, f"{API}/company/02509978")
    if r.status_code == 401:
        sys.exit("La clave no es valida (error 401). Revisa el archivo api-premier-key.text "
                 "y que la aplicacion sea 'live'.")
    if r.status_code != 200:
        sys.exit(f"Respuesta inesperada de la API: {r.status_code} {r.text[:200]}")
    print("   Clave correcta.\n")

    filas_cifras = []
    for clave_club, cfg in CLUBES.items():
        print(f"2) Club: {clave_club}")
        carpeta = OUT / clave_club

        # 2. Buscar la sociedad
        r = get(s, f"{API}/search/companies", params={"q": cfg["buscar"], "items_per_page": 10})
        candidatos = r.json().get("items", []) if r.status_code == 200 else []
        guardar_json(carpeta / "candidatos_busqueda.json", candidatos)
        elegido = None
        for c in candidatos:
            titulo = (c.get("title") or "").upper()
            if any(frag in titulo for frag in cfg["contiene"]):
                elegido = c
                break
        if not elegido:
            msg = f"   NO se encontro una sociedad que encaje. Revisa {carpeta / 'candidatos_busqueda.json'}"
            print(msg)
            informe.append(f"{clave_club}: sin sociedad encontrada")
            continue
        num = elegido["company_number"]
        print(f"   Sociedad elegida: {elegido.get('title')} ({num}) - estado: {elegido.get('company_status')}")

        # 3. Perfil, historial de cuentas, prestamos garantizados y administradores
        perfil = get(s, f"{API}/company/{num}").json()
        guardar_json(carpeta / "perfil.json", perfil)

        r = get(s, f"{API}/company/{num}/filing-history",
                params={"category": "accounts", "items_per_page": 100})
        historial = r.json() if r.status_code == 200 else {}
        guardar_json(carpeta / "historial_cuentas.json", historial)

        r = get(s, f"{API}/company/{num}/charges", params={"items_per_page": 100})
        charges = r.json() if r.status_code == 200 else {}
        guardar_json(carpeta / "charges.json", charges)

        r = get(s, f"{API}/company/{num}/officers", params={"items_per_page": 100})
        officers = r.json() if r.status_code == 200 else {}
        guardar_json(carpeta / "officers.json", officers)

        # Retraso entre el cierre del ejercicio y la presentacion de cada cuenta
        retrasos = []
        cuentas = [f for f in historial.get("items", []) if f.get("type", "").startswith("AA")]
        for f in cuentas:
            cierre = (f.get("description_values") or {}).get("made_up_date", "")
            d = dias_entre(cierre, f.get("date", ""))
            if d is not None:
                retrasos.append((cierre, f.get("date"), d))

        # 4. Descargar las cuentas mas recientes (iXBRL si existe, si no PDF)
        formatos = []
        for f in cuentas[:N_CUENTAS]:
            meta_url = (f.get("links") or {}).get("document_metadata")
            cierre = (f.get("description_values") or {}).get("made_up_date", "sin_fecha")
            if not meta_url:
                continue
            meta = get(s, meta_url)
            if meta.status_code != 200:
                formatos.append(f"{cierre}: error metadatos {meta.status_code}")
                continue
            recursos = meta.json().get("resources", {})
            if "application/xhtml+xml" in recursos:
                tipo, ext = "application/xhtml+xml", "xhtml"
            else:
                tipo, ext = "application/pdf", "pdf"
            doc = get(s, meta_url + "/content", accept=tipo)
            if doc.status_code != 200:
                formatos.append(f"{cierre}: error descarga {doc.status_code}")
                continue
            ruta = carpeta / "cuentas" / f"cuentas_{cierre}.{ext}"
            ruta.parent.mkdir(parents=True, exist_ok=True)
            ruta.write_bytes(doc.content)
            formatos.append(f"{cierre}: {ext.upper()} ({len(doc.content)//1024} KB)")

            # 5. Extraer cifras si es iXBRL
            if ext == "xhtml":
                for fila in extraer_ixbrl(ruta):
                    fila.update({"club": clave_club, "empresa": num, "cuentas_cierre": cierre})
                    filas_cifras.append(fila)

        # Resumen del club
        n_officers = officers.get("total_results", len(officers.get("items", [])))
        n_dimitidos = sum(1 for o in officers.get("items", []) if o.get("resigned_on"))
        bloque = [
            f"=== {clave_club.upper()} ===",
            f"Sociedad: {perfil.get('company_name')} ({num})",
            f"Estado: {perfil.get('company_status')}  |  Cuentas vencidas: "
            f"{(perfil.get('accounts') or {}).get('overdue')}",
            f"Cuentas anuales en el historial: {len(cuentas)}",
            "Retraso (dias desde el cierre hasta la presentacion), ultimas 6: "
            + "; ".join(f"{c}->{p}: {d}" for c, p, d in retrasos[:6]),
            f"Prestamos garantizados: total {charges.get('total_count', 0)}, "
            f"vigentes {charges.get('total_count', 0) - charges.get('satisfied_count', 0) - charges.get('part_satisfied_count', 0)}",
            f"Administradores (historico): {n_officers}, de ellos dimitidos/cesados: {n_dimitidos}",
            "Cuentas descargadas: " + "; ".join(formatos),
            "",
        ]
        informe.extend(bloque)
        print("\n".join("   " + l for l in bloque))

    # Guardar cifras y resumen
    if filas_cifras:
        campos = ["club", "empresa", "cuentas_cierre", "fecha_periodo", "concepto", "valor",
                  "texto_original", "contexto", "concepto_completo"]
        with open(OUT / "cifras_ixbrl.csv", "w", newline="", encoding="utf-8-sig") as fh:
            w = csv.DictWriter(fh, fieldnames=campos)
            w.writeheader()
            w.writerows(filas_cifras)
        clave_rows = [f for f in filas_cifras
                      if any(k.lower() in f["concepto"].lower() for k in CONCEPTOS_CLAVE)]
        with open(OUT / "cifras_clave.csv", "w", newline="", encoding="utf-8-sig") as fh:
            w = csv.DictWriter(fh, fieldnames=campos)
            w.writeheader()
            w.writerows(clave_rows)
        informe.append(f"Cifras iXBRL extraidas: {len(filas_cifras)} (clave: {len(clave_rows)})")

    (OUT / "informe_fase0.txt").write_text("\n".join(informe), encoding="utf-8")
    print(f"\nListo. Resultados en: {OUT}")


if __name__ == "__main__":
    main()

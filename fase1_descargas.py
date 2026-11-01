"""
FASE 1 - Descarga de datos base (solo descargas; el procesamiento se hace aparte)

Descarga a datos_fase1/raw/:
  1. Resultados de Premier League (E0) y Championship (E1) de football-data.co.uk,
     temporadas 2010/11 a 2026/27 -> de aqui sale que clubes estuvieron en cada division.
  2. Tablas 'games', 'clubs' y 'competitions' de transfermarkt-datasets
     -> de aqui sale que clubes jugaron competiciones europeas cada temporada.

Uso (Anaconda Prompt, dentro de la carpeta del proyecto):
  python fase1_descargas.py
"""
import sys
import time
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
RAW = BASE / "datos_fase1" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

FD_URL = "https://www.football-data.co.uk/mmz4281/{code}/{div}.csv"
TM_URL = "https://pub-e682421888d945d684bcae8890b0ec20.r2.dev/data/{tabla}.csv.gz"
CABECERAS = {"User-Agent": "Mozilla/5.0 (proyecto academico de investigacion)"}


def descargar(url, destino):
    if destino.exists() and destino.stat().st_size > 0:
        print(f"   ya existe: {destino.name}")
        return True
    try:
        r = requests.get(url, headers=CABECERAS, timeout=120)
        time.sleep(1)  # pausa de cortesia con el servidor
        if r.status_code == 200 and len(r.content) > 100:
            destino.write_bytes(r.content)
            print(f"   OK  {destino.name} ({len(r.content)//1024} KB)")
            return True
        print(f"   FALLO {destino.name}: HTTP {r.status_code}")
    except Exception as e:
        print(f"   FALLO {destino.name}: {e}")
    return False


def main():
    print("1) Resultados por temporada (football-data.co.uk)")
    ok = 0
    for inicio in range(2010, 2027):
        code = f"{inicio % 100:02d}{(inicio + 1) % 100:02d}"
        for div in ("E0", "E1"):
            ok += descargar(FD_URL.format(code=code, div=div), RAW / f"fd_{code}_{div}.csv")
    print(f"   {ok} archivos de resultados\n")

    print("2) Tablas de transfermarkt-datasets")
    for tabla in ("competitions", "clubs", "games"):
        descargar(TM_URL.format(tabla=tabla), RAW / f"tm_{tabla}.csv.gz")

    print(f"\nListo. Archivos en: {RAW}")


if __name__ == "__main__":
    main()

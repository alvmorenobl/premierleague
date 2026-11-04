"""
FASE 2a-bis - Limpia el inventario de cuentas (datos_fase2/inventario_cuentas.csv).

Se queda solo con cuentas anuales reales (tipo AA o AAMD) cerradas entre 2009 y 2026 y
excluye fechas imposibles (fecha de deposito anterior al cierre). Esto elimina, p. ej.,
5 cuentas de Tottenham de los anos 1920 que el registro guarda con el ano abreviado
y que aparecian como 2020-2026.

Calcula ademas el plazo legal de deposito (9 meses; 12 para plazos que vencian entre
el 25/03/2020 y el 05/04/2021 por la ampliacion COVID) y los dias fuera de plazo.
Margen de 30 dias por la diferencia entre fecha de entrega y fecha de inscripcion.

Salida: datos_fase2/inventario_cuentas_limpio.csv
Uso:  python fase2_limpiar_inventario.py
"""
from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parent
D2 = BASE / "datos_fase2"

def main():
    d = pd.read_csv(D2 / "inventario_cuentas.csv", dtype=str).fillna("")
    a = d[d.tipo.isin(["AA", "AAMD"]) & d.cierre.between("2009-01-01", "2026-12-31")].copy()
    a["cie"] = pd.to_datetime(a.cierre)
    a["dep"] = pd.to_datetime(a.depositada)
    imposibles = a[a.dep < a.cie]
    a = a[a.dep >= a.cie].copy()
    a["meses_hasta_deposito"] = ((a.dep - a.cie).dt.days / 30.44).round(2)
    lim = a.cie + pd.DateOffset(months=9)
    covid = lim.between("2020-03-25", "2021-04-05")
    lim[covid] = a.cie[covid] + pd.DateOffset(months=12)
    a["plazo_legal"] = lim.dt.date
    a["dias_fuera_plazo"] = (a.dep - lim).dt.days
    a["fuera_plazo_claro"] = (a.dias_fuera_plazo > 30) & (a.tipo == "AA")
    a["formato"] = a.xhtml.map({"si": "ixbrl"}).fillna("pdf")
    a["modificada"] = a.tipo.eq("AAMD")
    a = a.drop(columns=["cie", "dep"])
    a.to_csv(D2 / "inventario_cuentas_limpio.csv", index=False)
    print(f"{len(a)} cuentas validas; excluidas por fecha imposible: {len(imposibles)}")
    if len(imposibles):
        print(imposibles[["club", "numero", "cierre", "depositada"]].to_string(index=False))

if __name__ == "__main__":
    main()

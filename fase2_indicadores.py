"""
FASE 2g - Indicadores por club-temporada para los modelos de la fase 3.

Para cada club-temporada del estudio (Premier League y Championship) dice si la sociedad del club depositó
cuenta del ejercicio, y si no, si el plazo legal ya venció (cuenta NO depositada: señal de riesgo) o aún no
(temporadas recientes). Añade tipo de cuenta, retraso en el depósito y si la cuenta del grupo es de una holding
que no consolida al club.

Entrada:  datos_fase1/clubes_temporada.csv, datos_fase2/panel_financiero.csv
Salida:   datos_fase2/indicadores_club_temporada.csv
Uso:      python fase2_indicadores.py [fecha_referencia AAAA-MM-DD]   (por defecto, hoy)
"""
import sys
import pandas as pd
from pathlib import Path

BASE = Path(__file__).resolve().parent
HOY = pd.Timestamp(sys.argv[1]) if len(sys.argv) > 1 else pd.Timestamp.today().normalize()

def main():
    ct = pd.read_csv(BASE / "datos_fase1" / "clubes_temporada.csv")
    ct = ct[ct.temporada >= "2010/11"].copy()
    p = pd.read_csv(BASE / "datos_fase2" / "panel_financiero.csv", dtype={"numero": str})
    p = p[p.cierre_principal_temporada]
    cols = ["numero", "cierre", "meses_ejercicio", "cuenta_depositada", "tipo_cuenta", "cuenta_abreviada",
            "cuenta_inactiva", "depositada", "dias_fuera_plazo", "fuera_plazo_claro"]
    club = p[p.rol == "club"].sort_values("cuenta_depositada").drop_duplicates(["club", "temporada"], keep="last")
    grupo = p[p.rol == "grupo"].sort_values("cuenta_depositada").drop_duplicates(["club", "temporada"], keep="last")
    out = ct.merge(club[["club", "temporada"] + cols], on=["club", "temporada"], how="left")
    out = out.merge(grupo[["club", "temporada", "numero", "cuenta_depositada", "holding_sin_consolidar"]]
                    .rename(columns={"numero": "numero_grupo", "cuenta_depositada": "cuenta_grupo_depositada"}),
                    on=["club", "temporada"], how="left")
    out["cuenta_depositada"] = out.cuenta_depositada.fillna(False).astype(bool)
    # fin de la temporada (30 de junio del segundo año) + 9 meses de plazo legal + 1 mes de margen
    fin = pd.to_datetime(out.temporada.str[:4].astype(int) + 1, format="%Y") + pd.DateOffset(months=5, days=29)
    vencido = fin + pd.DateOffset(months=10) < HOY
    out["estado_cuenta"] = "depositada"
    out.loc[~out.cuenta_depositada & vencido, "estado_cuenta"] = "no_depositada"
    out.loc[~out.cuenta_depositada & ~vencido, "estado_cuenta"] = "aun_no_vencida"
    out.to_csv(BASE / "datos_fase2" / "indicadores_club_temporada.csv", index=False)
    print(out.estado_cuenta.value_counts().to_string())
    print(out[out.estado_cuenta == "no_depositada"][["temporada", "division", "club"]].to_string(index=False))

if __name__ == "__main__":
    main()

"""
Construye la tabla club x temporada (Premier y Championship) a partir de los
resultados de football-data.co.uk descargados con fase1_descargas.py.

Salida: datos_fase1/clubes_temporada.csv
  temporada, division, club, partidos, puntos_sin_sanciones, posicion_sin_sanciones,
  division_siguiente, movimiento (ascenso/descenso/se_mantiene/en_curso)

Nota: la clasificacion se calcula con los resultados, SIN aplicar deducciones de
puntos; por eso se llama 'sin_sanciones'. Los movimientos de division se deducen
de en que division aparece el club la temporada siguiente.
"""
from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parent
RAW = BASE / "datos_fase1" / "raw"
OUT = BASE / "datos_fase1"

DIVISIONES = {"E0": "Premier League", "E1": "Championship"}


def tabla(df):
    filas = []
    for _, p in df.iterrows():
        h, a, gh, ga = p["HomeTeam"], p["AwayTeam"], p["FTHG"], p["FTAG"]
        ph, pa = (3, 0) if gh > ga else (0, 3) if gh < ga else (1, 1)
        filas += [(h, ph, gh - ga), (a, pa, ga - gh)]
    t = pd.DataFrame(filas, columns=["club", "pts", "dg"]).groupby("club").agg(
        partidos=("pts", "size"), puntos=("pts", "sum"), dif_goles=("dg", "sum")).reset_index()
    t = t.sort_values(["puntos", "dif_goles"], ascending=False).reset_index(drop=True)
    t["posicion"] = t.index + 1
    return t


def main():
    registros = []
    for f in sorted(RAW.glob("fd_*_E*.csv")):
        _, code, div = f.stem.split("_")
        temporada = f"20{code[:2]}/{code[2:]}"
        df = pd.read_csv(f, encoding="latin-1", usecols=lambda c: c in
                         ("HomeTeam", "AwayTeam", "FTHG", "FTAG")).dropna()
        t = tabla(df)
        t["temporada"], t["division"] = temporada, DIVISIONES[div]
        registros.append(t)
    todo = pd.concat(registros, ignore_index=True)

    # Division de la temporada siguiente
    temporadas = sorted(todo["temporada"].unique())
    sig = {temporadas[i]: temporadas[i + 1] for i in range(len(temporadas) - 1)}
    clave = todo.set_index(["temporada", "club"])["division"].to_dict()
    def division_siguiente(r):
        s = sig.get(r["temporada"])
        if s is None:
            return "en_curso"
        return clave.get((s, r["club"]), "League One o inferior")
    todo["division_siguiente"] = todo.apply(division_siguiente, axis=1)
    orden = {"Premier League": 1, "Championship": 2, "League One o inferior": 3}
    def movimiento(r):
        if r["division_siguiente"] == "en_curso":
            return "en_curso"
        d = orden[r["division_siguiente"]] - orden[r["division"]]
        return "se_mantiene" if d == 0 else ("ascenso" if d < 0 else "descenso")
    todo["movimiento"] = todo.apply(movimiento, axis=1)

    todo = todo.rename(columns={"puntos": "puntos_sin_sanciones", "posicion": "posicion_sin_sanciones"})
    cols = ["temporada", "division", "club", "partidos", "puntos_sin_sanciones", "dif_goles",
            "posicion_sin_sanciones", "division_siguiente", "movimiento"]
    todo = todo[cols].sort_values(["temporada", "division", "posicion_sin_sanciones"],
                                  ascending=[True, False, True])
    todo.to_csv(OUT / "clubes_temporada.csv", index=False, encoding="utf-8-sig")

    print("Filas:", len(todo))
    print("Clubes distintos:", todo["club"].nunique())
    print(todo.groupby(["temporada", "division"]).size().unstack())


if __name__ == "__main__":
    main()

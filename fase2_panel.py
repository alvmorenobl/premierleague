"""
FASE 2f - Construye el panel financiero club x temporada y valida cada cifra.

Junta las cifras de iXBRL (exactas) y de OCR, y para cada cifra comprueba:
  - CONTRASTE ENTRE AÑOS: la cifra del año t aparece otra vez como "año anterior"
    en las cuentas del año t+1. Si coinciden, la cifra queda validada. Si falta la
    del año t pero existe en t+1, se rellena con esa.
  - IDENTIDADES CONTABLES: activos netos = patrimonio; resultado antes de
    impuestos + impuesto = resultado neto.

Salidas (datos_fase2/):
  panel_largo.csv       una fila por sociedad, cierre y partida, con su estado
  panel_financiero.csv  una fila por sociedad y cierre (tabla ancha), con club y temporada
  calidad_panel.csv     resumen de cobertura y validacion por partida
Uso:  python fase2_panel.py
"""
import numpy as np
import pandas as pd
from pathlib import Path

BASE = Path(__file__).resolve().parent
D2 = BASE / "datos_fase2"

def cerca(a, b):
    return (a - b).abs() <= np.maximum(2, 0.005 * b.abs())

def main():
    ocr = pd.read_csv(D2 / "cifras_ocr_largo.csv", dtype={"numero": str})
    ocr["fuente"] = "ocr"
    ix = pd.read_csv(D2 / "cifras_ixbrl_largo.csv", dtype={"numero": str})
    ix["fuente"] = "ixbrl"
    d = pd.concat([ix, ocr], ignore_index=True)
    # si hay varios documentos para el mismo cierre (cuentas repetidas o modificadas),
    # se queda el que aporta mas partidas; iXBRL tiene prioridad
    n = d.groupby(["numero", "cierre", "documento", "fuente"]).size().rename("n").reset_index()
    n["prio"] = (n.fuente == "ixbrl").astype(int)
    elegido = n.sort_values(["prio", "n"], ascending=False).drop_duplicates(["numero", "cierre"])
    d = d.merge(elegido[["numero", "cierre", "documento"]], on=["numero", "cierre", "documento"])
    d = d.drop_duplicates(["numero", "cierre", "variable"])

    # rejilla completa sociedad x cierre x variable para poder rellenar desde t+1
    d["cie"] = pd.to_datetime(d.cierre)
    d = d.sort_values(["numero", "variable", "cie"])
    g = d.groupby(["numero", "variable"])
    d["sig_anterior"] = g.anterior.shift(-1)
    d["sig_cie"] = g.cie.shift(-1)
    hueco = (d.sig_cie - d.cie).dt.days
    consecutivo = hueco.between(300, 430)
    d["estado"] = "sin_contraste"
    d.loc[consecutivo & d.sig_anterior.notna() & d.actual.notna() & cerca(d.actual, d.sig_anterior), "estado"] = "validada"
    d.loc[consecutivo & d.sig_anterior.notna() & d.actual.notna() & ~cerca(d.actual, d.sig_anterior), "estado"] = "conflicto"
    d.loc[d.fuente == "ixbrl", "estado"] = d.loc[d.fuente == "ixbrl", "estado"].replace({"sin_contraste": "ixbrl", "conflicto": "ixbrl_conflicto"})
    d["valor"] = d.actual

    # cierres que no tenemos (o partidas que faltan) pero aparecen como "año anterior" en t+1
    extra = d[d.anterior.notna()].copy()
    extra["cie"] = extra.cie - pd.DateOffset(years=1)
    extra["cierre_aprox"] = extra.cie.dt.strftime("%Y-%m")
    d["cierre_aprox"] = d.cie.dt.strftime("%Y-%m")
    ya = set(zip(d.numero, d.cierre_aprox, d.variable))
    extra = extra[[(a, b, c) not in ya for a, b, c in zip(extra.numero, extra.cierre_aprox, extra.variable)]]
    extra = extra.assign(valor=extra.anterior, actual=np.nan, estado="desde_año_siguiente",
                         cierre=extra.cie.dt.strftime("%Y-%m-%d"))
    d = pd.concat([d, extra], ignore_index=True)

    # identidades contables por documento
    w = d.pivot_table(index=["numero", "cierre"], columns="variable", values="valor", aggfunc="first")
    flags = pd.DataFrame(index=w.index)
    if {"activos_netos", "patrimonio"} <= set(w.columns):
        ok = cerca(w.activos_netos, w.patrimonio)
        flags["check_balance"] = np.where(w.activos_netos.isna() | w.patrimonio.isna(), "", np.where(ok, "ok", "falla"))
    if {"resultado_antes_impuestos", "impuesto", "resultado_neto"} <= set(w.columns):
        ok = cerca(w.resultado_antes_impuestos + w.impuesto, w.resultado_neto)
        falta = w[["resultado_antes_impuestos", "impuesto", "resultado_neto"]].isna().any(axis=1)
        flags["check_resultados"] = np.where(falta, "", np.where(ok, "ok", "falla"))

    # club, rol y temporada
    mapa = pd.read_csv(BASE / "datos_fase1" / "mapa_sociedades.csv", dtype=str).fillna("")
    rol = {}
    for _, r in mapa.iterrows():
        if r.numero_club: rol.setdefault(r.numero_club, (r.club, "club"))
        if r.numero_grupo: rol.setdefault(r.numero_grupo, (r.club, "grupo"))
    panel = w.join(flags).reset_index()
    panel["club"] = panel.numero.map(lambda x: rol.get(x, ("", ""))[0])
    panel["rol"] = panel.numero.map(lambda x: rol.get(x, ("", ""))[1])
    c = pd.to_datetime(panel.cierre)
    ini = np.where(c.dt.month <= 9, c.dt.year - 1, c.dt.year)
    panel["temporada"] = [f"{a}/{str(a+1)[-2:]}" for a in ini]
    fuente = d.groupby(["numero", "cierre"]).fuente.first()
    panel = panel.merge(fuente.rename("fuente_documento").reset_index(), on=["numero", "cierre"], how="left")
    primeras = ["club", "rol", "numero", "temporada", "cierre", "fuente_documento", "check_balance", "check_resultados"]
    panel = panel[[x for x in primeras if x in panel] + [x for x in panel.columns if x not in primeras]]
    panel.sort_values(["club", "rol", "cierre"]).to_csv(D2 / "panel_financiero.csv", index=False)

    d[["numero", "cierre", "variable", "valor", "actual", "anterior", "estado", "fuente",
       "documento", "pagina", "etiqueta_ocr"]].sort_values(["numero", "cierre", "variable"]).to_csv(D2 / "panel_largo.csv", index=False)

    cal = d.groupby("variable").estado.value_counts().unstack(fill_value=0)
    cal["total"] = cal.sum(axis=1)
    contrastadas = cal.get("validada", 0) + cal.get("conflicto", 0)
    cal["pct_validada_de_contrastadas"] = (cal.get("validada", 0) / contrastadas.replace(0, np.nan) * 100).round(1)
    cal.sort_values("total", ascending=False).to_csv(D2 / "calidad_panel.csv")
    print(cal.sort_values("total", ascending=False).to_string())
    print("\nIdentidades:", {k: flags[k].value_counts().to_dict() for k in flags})
    print(f"\nPanel: {len(panel)} filas (sociedad x cierre), {panel.club.nunique()} clubes")

if __name__ == "__main__":
    main()

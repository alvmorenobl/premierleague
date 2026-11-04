"""
Validacion 2 (muestra NUEVA de 40 documentos, semilla 7, no usada para ajustar reglas).
Revisada a mano contra la imagen de la pagina original (C:\\datos_premier\\validacion2\\x??.png).

Regla de registro: toda cifra extraida de las 6 partidas se reviso; salvo las listadas
abajo como incorrectas o no verificables, el valor extraido coincide con el impreso.
La verdad queda fijada en datos_fase2/auditoria/validacion2_referencia.csv la primera vez
que se ejecuta; despues solo se mide (extractor y panel) contra esa verdad.
"""
import sys
import numpy as np
import pandas as pd

V = ["ingresos", "resultado_antes_impuestos", "activos_netos", "patrimonio", "gastos_personal", "sueldos_salarios"]
# (id, variable) -> cifra verdadera (en miles de libras) cuando el extractor fallo
INCORRECTAS = {
    (2, "ingresos"): 76405.139,          # tomo la columna 2010
    (2, "activos_netos"): -176597.552,   # cifra partida por el OCR
    (5, "patrimonio"): 572329.0,         # el OCR perdio el primer digito
    (8, "ingresos"): 370.078,            # primer ejercicio, una columna; cifra en otra linea
    (16, "resultado_antes_impuestos"): "mal: tomo 'finance costs' (la linea siguiente era la etiqueta)",
    (26, "ingresos"): 150346.0,          # el OCR leyo 160,346
    (30, "ingresos"): 49966.338,         # cifra partida '49,966 338'
    (33, "ingresos"): 549633.0,          # tomo la columna 2022 (formato 6 columnas)
}
FALTAN = {(29, "activos_netos"): -10454.532}   # 'NET LIABILTIIES' (errata en el original)
NO_VERIFICABLES = {(3, "resultado_antes_impuestos"), (10, "resultado_antes_impuestos"), (12, "ingresos"),
                   (17, "resultado_antes_impuestos"), (28, "ingresos")}
EXCLUIR_IDS = set()

def main():
    base = sys.argv[1] if len(sys.argv) > 1 else "."
    ref_f = f"{base}/datos_fase2/auditoria/validacion2_referencia.csv"
    sel = pd.read_csv(f"{base}/datos_fase2/auditoria/muestra_validacion2_docs.csv", dtype={"numero": str}).reset_index(drop=True)
    x = pd.read_csv(f"{base}/datos_fase2/cifras_ocr_largo.csv", dtype={"numero": str})
    try:
        ref = pd.read_csv(ref_f, dtype={"numero": str})
    except FileNotFoundError:
        rows = []
        for k, r in sel.iterrows():
            e = x[x.documento == r.documento].drop_duplicates("variable").set_index("variable").actual
            for v in V:
                if (k, v) in NO_VERIFICABLES:
                    rows.append(dict(id=k, numero=r.numero, cierre=r.cierre, documento=r.documento, variable=v, verdad=np.nan, estado_ref="no_verificable"))
                elif (k, v) in INCORRECTAS:
                    t = INCORRECTAS[(k, v)]
                    rows.append(dict(id=k, numero=r.numero, cierre=r.cierre, documento=r.documento, variable=v,
                                     verdad=t if not isinstance(t, str) else np.nan, estado_ref="verdad_corregida" if not isinstance(t, str) else "incorrecta_sin_cifra"))
                elif (k, v) in FALTAN:
                    rows.append(dict(id=k, numero=r.numero, cierre=r.cierre, documento=r.documento, variable=v, verdad=FALTAN[(k, v)], estado_ref="faltaba"))
                elif pd.notna(e.get(v, np.nan)):
                    rows.append(dict(id=k, numero=r.numero, cierre=r.cierre, documento=r.documento, variable=v, verdad=e[v], estado_ref="extraida_correcta"))
        ref = pd.DataFrame(rows)
        ref.to_csv(ref_f, index=False)
    medir(ref, x, base)

def medir(ref, x, base):
    r = ref[ref.estado_ref != "no_verificable"].copy()
    def evalua(valores):
        res = []
        for _, f in r.iterrows():
            ext = valores.get((f.documento, f.variable), np.nan)
            if f.estado_ref == "incorrecta_sin_cifra":
                res.append("incorrecto" if pd.notna(ext) else "falta")
            elif pd.isna(ext):
                res.append("falta")
            else:
                res.append("correcto" if abs(ext - f.verdad) <= 1 else "incorrecto")
        return pd.Series(res, index=r.index)
    ext = {(a, b): c for a, b, c in zip(x.documento, x.variable, x.actual)}
    r["extractor"] = evalua(ext)
    p = pd.read_csv(f"{base}/datos_fase2/panel_largo.csv", dtype={"numero": str})
    fiable = p[~p.estado.isin(["conflicto"]) & p.sospechosa.fillna("").eq("")]
    pan = {(a, b): c for a, b, c in zip(fiable.documento, fiable.variable, fiable.valor)}
    # el panel puede tomar el valor de la cuenta del año siguiente: se busca por sociedad y cierre
    pan2 = {(n, c, v): val for n, c, v, val in zip(fiable.numero, fiable.cierre, fiable.variable, fiable.valor)}
    # solo por (sociedad, cierre, variable): las filas 'desde_año_siguiente' llevan el documento del ano t+1
    r["panel"] = evalua({(f.documento, f.variable): pan2.get((f.numero, f.documento[:10], f.variable), np.nan) for _, f in r.iterrows()})
    for col in ("extractor", "panel"):
        c = r[r[col].isin(["correcto", "incorrecto"])]
        f = r[r[col].isin(["correcto", "incorrecto", "falta"])]
        print(f"{col:9s}: precision {100*(c[col]=='correcto').mean():.1f}% ({(c[col]=='correcto').sum()}/{len(c)})  "
              f"exhaustividad {100*(f[col]=='correcto').mean():.1f}% ({(f[col]=='correcto').sum()}/{len(f)})")
    print(r[(r.extractor != "correcto") | (r.panel != "correcto")][["id", "variable", "verdad", "extractor", "panel"]].to_string(index=False))

if __name__ == "__main__":
    main()

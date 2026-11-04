"""
Validacion 5 (prueba de aceptacion del PANEL FINAL de la fase 2: reglas automaticas + revision manual).
Muestra NUEVA de 40 cuentas (semilla 31) de club-temporadas del estudio, excluidas las cinco muestras
anteriores. Ninguna regla se ajusto mirando esta muestra; se mide una sola vez.

Revisada a mano contra la imagen de la pagina original (C:\\datos_premier\\validacion5\\v??.png).
Cuando la cifra no se veia en la tira se comprobo en el texto OCR fino (Brighton 2025: suma exacta de
columnas) o se acepto si el panel la habia validado con el comparativo de la cuenta siguiente (Arsenal 2016).
Correccion de la referencia tras medir (no del sistema): en Birmingham 2012 se habia anotado como verdad del
resultado antes de impuestos 15,712,560, leido en la tira. La pagina completa (w01.png) muestra dos lineas con la
misma etiqueta 'before and after taxation': 15,713,587 antes del impuesto (1,027) y 15,712,560 despues. El valor
del extractor (15,713,587) era el correcto; el error era de la referencia.
Las cifras de FALTAN se habian fijado contra el PDF en la revision manual dirigida (mismo documento).
"""
import sys
import numpy as np
import pandas as pd

V = ["ingresos", "resultado_antes_impuestos", "activos_netos", "patrimonio", "gastos_personal", "sueldos_salarios"]

INCORRECTAS = {
    (12, "sueldos_salarios"): 142299.0,             # Man United 2015: impreso entre parentesis; el extractor lo deja negativo
}
FALTAN = {
    (1, "activos_netos"): -3530.184,
    (7, "sueldos_salarios"): 28351.447,
    (8, "gastos_personal"): 27551.318,     # KPI del informe (no hay tabla de personal)
    (11, "ingresos"): 9954.979,
    (11, "resultado_antes_impuestos"): -14675.089,
    (12, "activos_netos"): -41022.0,
}
FALTAN_SIN_CIFRA = {
    (0, "activos_netos"), (5, "activos_netos"), (11, "activos_netos"), (19, "activos_netos"),
    (27, "ingresos"), (27, "resultado_antes_impuestos"), (27, "activos_netos"),   # Everton 2019
}
NO_VERIFICABLES = {(27, "sueldos_salarios"),   # dos tablas (grupo/sociedad)
                   (29, "patrimonio")}         # la linea de patrimonio no aparece en la pagina


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else "."
    ref_f = f"{base}/datos_fase2/auditoria/validacion5_referencia.csv"
    sel = pd.read_csv(f"{base}/datos_fase2/auditoria/muestra_validacion5_docs.csv", dtype={"numero": str}).reset_index(drop=True)
    sel["cierre"] = sel.documento.str[:10]
    x = pd.read_csv(f"{base}/datos_fase2/cifras_ocr_largo.csv", dtype={"numero": str})
    try:
        ref = pd.read_csv(ref_f, dtype={"numero": str})
    except FileNotFoundError:
        rows = []
        for k, r in sel.iterrows():
            e = x[x.documento == r.documento].drop_duplicates("variable").set_index("variable").actual
            for v in V:
                d = dict(id=k, numero=r.numero, cierre=r.cierre, documento=r.documento, variable=v)
                if (k, v) in NO_VERIFICABLES:
                    rows.append({**d, "verdad": np.nan, "estado_ref": "no_verificable"})
                elif (k, v) in INCORRECTAS:
                    t = INCORRECTAS[(k, v)]
                    sin = isinstance(t, str)
                    rows.append({**d, "verdad": np.nan if sin else t, "estado_ref": "incorrecta_sin_cifra" if sin else "verdad_corregida"})
                elif (k, v) in FALTAN:
                    rows.append({**d, "verdad": FALTAN[(k, v)], "estado_ref": "faltaba"})
                elif (k, v) in FALTAN_SIN_CIFRA:
                    rows.append({**d, "verdad": np.nan, "estado_ref": "faltaba_sin_cifra"})
                elif pd.notna(e.get(v, np.nan)):
                    rows.append({**d, "verdad": e[v], "estado_ref": "extraida_correcta"})
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
            elif f.estado_ref == "faltaba_sin_cifra":
                res.append("falta" if pd.isna(ext) else "sin_puntuar")
            elif pd.isna(ext):
                res.append("falta")
            else:
                res.append("correcto" if abs(ext - f.verdad) <= 1 else "incorrecto")
        return pd.Series(res, index=r.index)

    ext = {(a, b): c for a, b, c in zip(x.documento, x.variable, x.actual)}
    r["extractor"] = evalua(ext)
    p = pd.read_csv(f"{base}/datos_fase2/panel_largo.csv", dtype={"numero": str})
    fiable = p[~p.estado.isin(["conflicto"]) & p.sospechosa.fillna("").eq("")]
    # El panel se consulta SOLO por (sociedad, cierre, variable). No por documento: las filas rellenadas
    # 'desde_año_siguiente' llevan el documento de origen (el del ano t+1), y buscar por documento
    # mezclaba el ejercicio t-1 con el t (error de medicion detectado en esta validacion).
    pan2 = {(n, c, v): val for n, c, v, val in zip(fiable.numero, fiable.cierre, fiable.variable, fiable.valor)}
    r["panel"] = evalua({(f.documento, f.variable): pan2.get((f.numero, f.cierre, f.variable), np.nan) for _, f in r.iterrows()})
    est = {(n, c, v): (e, s) for n, c, v, e, s in zip(p.numero, p.cierre, p.variable, p.estado, p.sospechosa)}
    r["estado_panel"] = [str(est.get((f.numero, f.cierre, f.variable), ("", ""))) for _, f in r.iterrows()]
    for col in ("extractor", "panel"):
        c = r[r[col].isin(["correcto", "incorrecto"])]
        f = r[r[col].isin(["correcto", "incorrecto", "falta"])]
        print(f"{col:9s}: precision {100*(c[col]=='correcto').mean():.1f}% ({(c[col]=='correcto').sum()}/{len(c)})  "
              f"exhaustividad {100*(f[col]=='correcto').mean():.1f}% ({(f[col]=='correcto').sum()}/{len(f)})")
    print(r[(r.extractor != "correcto") | (r.panel != "correcto")][["id", "variable", "verdad", "extractor", "panel", "estado_panel"]].to_string(index=False))
    r.to_csv(f"{base}/datos_fase2/auditoria/validacion5_resultado.csv", index=False)


if __name__ == "__main__":
    main()

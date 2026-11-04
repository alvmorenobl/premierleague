"""
Validacion 3 (prueba de aceptacion de la fase 2).
Muestra NUEVA de 40 documentos (semilla 11), excluidas todas las muestras anteriores
(desarrollo, val-1, val-2). Ninguna regla se ajusto mirando esta muestra.

Revisada a mano contra la imagen de la pagina original (C:\\datos_premier\\validacion3\\y??.png)
y, para las cifras que no aparecian en la tira, contra el texto OCR fino de la pagina del estado
financiero, comprobado con la imagen cuando hubo duda.

Regla de registro: toda cifra extraida de las 6 partidas se reviso; salvo las listadas abajo
como incorrectas, faltantes o no verificables, el valor extraido coincide con el impreso.
La verdad queda fijada en datos_fase2/auditoria/validacion3_referencia.csv la primera vez que
se ejecuta; despues solo se mide (extractor y panel) contra esa verdad.

Nota: la columna 'cierre' de muestra_validacion3_docs.csv esta desfasada un ano en algunas filas
(error al construir la muestra, no del inventario ni del panel). Aqui el cierre se toma de los
10 primeros caracteres de 'documento', que coinciden con el inventario.
"""
import sys
import numpy as np
import pandas as pd

V = ["ingresos", "resultado_antes_impuestos", "activos_netos", "patrimonio", "gastos_personal", "sueldos_salarios"]

# (id, variable) -> cifra verdadera (miles de libras) cuando el extractor dio un valor erroneo
INCORRECTAS = {
    (2, "resultado_antes_impuestos"): 272.0,       # formato 4 columnas (sin/con traspasos/total/ano anterior): tomo la 2a columna
    (7, "patrimonio"): 5783.0,                     # leyo 783: el OCR perdio el primer digito
    (8, "sueldos_salarios"): "mal: 0 (sueldos normales 12,242 + excepcionales ilegibles)",
    (13, "patrimonio"): -79667.0,                  # tomo la tabla del informe de administradores (pag 4), no el balance consolidado (pag 9)
    (25, "activos_netos"): -23148.962,             # dos lineas 'Net liabilities' (antes y despues de pensiones): tomo la primera
    (28, "patrimonio"): -110985.02,                # signo: '( 110,985,020)' con espacio tras el parentesis
    (36, "activos_netos"): 3280.877,               # leyo 0.010 (el '.' tras 'Net assets' rompio la linea)
    (38, "resultado_antes_impuestos"): 24091.0,    # leyo 0: formato 4 columnas con etiqueta partida en dos lineas
}
# cifras que existen en el documento y el extractor no dio
FALTAN = {
    (0, "sueldos_salarios"): 15009.136,
    (1, "sueldos_salarios"): 8810.54,
    (6, "gastos_personal"): 7361.0,                # 'Staff costs' en la cuenta de resultados
    (9, "ingresos"): 0.0,                          # 'Turnover -' (primer ejercicio, sin ingresos)
    (13, "activos_netos"): -79667.0,
    (15, "sueldos_salarios"): 79539.268,
    (18, "sueldos_salarios"): 10070.964,
    (37, "sueldos_salarios"): 23095.0,
    (38, "sueldos_salarios"): 69019.0,
}
# existen en el documento, el extractor no las dio y no se pudo fijar la cifra con seguridad
# (cuentan como 'falta' si siguen sin valor; si el panel aporta uno, no se puntua)
FALTAN_SIN_CIFRA = {
    (15, "resultado_antes_impuestos"),
    (37, "activos_netos"), (37, "patrimonio"),    # balance de grupo y de sociedad: falta decidir cual corresponde
}
NO_VERIFICABLES = set()


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else "."
    ref_f = f"{base}/datos_fase2/auditoria/validacion3_referencia.csv"
    sel = pd.read_csv(f"{base}/datos_fase2/auditoria/muestra_validacion3_docs.csv", dtype={"numero": str}).reset_index(drop=True)
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
    r.to_csv(f"{base}/datos_fase2/auditoria/validacion3_resultado.csv", index=False)


if __name__ == "__main__":
    main()

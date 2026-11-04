"""
Validacion 4 (prueba de aceptacion de la fase 2, tras los arreglos de la validacion 3).
Muestra NUEVA de 40 documentos (semilla 23), excluidas todas las muestras anteriores
(desarrollo, val-1, val-2, val-3). Ninguna regla se ajusto mirando esta muestra.

Revisada a mano contra la imagen de la pagina original (C:\\datos_premier\\validacion4\\z??.png,
y w02.png a pagina completa) y, para las cifras que no aparecian en la tira, contra el texto OCR fino.
Cuando una cifra no se podia leer en la imagen pero el panel la habia validado con el comparativo
de la cuenta del ano siguiente (una segunda lectura independiente), se dio por correcta (ids 4 y 31, RAI).

Regla de registro: toda cifra extraida de las 6 partidas se reviso; salvo las listadas abajo,
el valor extraido coincide con el impreso. La verdad queda fijada en validacion4_referencia.csv
la primera vez que se ejecuta; despues solo se mide.
"""
import sys
import numpy as np
import pandas as pd

V = ["ingresos", "resultado_antes_impuestos", "activos_netos", "patrimonio", "gastos_personal", "sueldos_salarios"]

INCORRECTAS = {
    (2, "ingresos"): 11258.0,          # Watford 2010: tomo 'continuing operations' (10,356); el total con adquisiciones es 11,258
    (4, "patrimonio"): -37386.0,       # Ipswich 2010: tomo 'opening shareholders deficit' (cifra del ano anterior)
    (6, "ingresos"): 12706.503,        # Crystal Palace 2011: el OCR leyo '{2,706,503' (perdio el 1)
    (6, "gastos_personal"): "mal: leyo el ano '2011' de la cabecera como importe",
    (16, "ingresos"): 112072.0,        # QPR 2015: el OCR leyo '0 412,072 97,557'
    (21, "ingresos"): 31411.0,         # Cardiff 2016: el OCR leyo 34,414 (la pagina 5 y la imagen dicen 31,411)
    (35, "sueldos_salarios"): 329694.0,  # Man United 2022: impreso entre parentesis; el extractor lo deja negativo
}
FALTAN = {
    (13, "patrimonio"): -5004.668,
    (21, "patrimonio"): -86711.0,      # 'Net deficit'
    (23, "sueldos_salarios"): 14683.507,
    (26, "activos_netos"): 35369.0,    # balance consolidado (pag 9); el de la sociedad (pag 10) es 44,668
    (26, "patrimonio"): 35369.0,
    (35, "patrimonio"): -89755.0,      # NIIF: 'Total equity'
}
FALTAN_SIN_CIFRA = {
    (0, "sueldos_salarios"), (12, "resultado_antes_impuestos"), (12, "patrimonio"),
    (19, "patrimonio"), (22, "sueldos_salarios"),
    (38, "ingresos"), (38, "resultado_antes_impuestos"),   # Everton 2023: cuenta de resultados no localizada
}
NO_VERIFICABLES = {(38, "sueldos_salarios")}   # dos tablas (135,972 y 138,394): no se pudo fijar cual es la del club
# Nota: el id 32 (Middlesbrough Holdings 2020) son cuentas de sociedad inactiva (dormant): no hay cifras.


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else "."
    ref_f = f"{base}/datos_fase2/auditoria/validacion4_referencia.csv"
    sel = pd.read_csv(f"{base}/datos_fase2/auditoria/muestra_validacion4_docs.csv", dtype={"numero": str}).reset_index(drop=True)
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
    r.to_csv(f"{base}/datos_fase2/auditoria/validacion4_resultado.csv", index=False)


if __name__ == "__main__":
    main()

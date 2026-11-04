"""
Registra los veredictos de la validacion visual (muestra nueva de 60 documentos,
semilla 2026) en datos_fase2/auditoria/validacion_referencia.csv y calcula
precision y exhaustividad del extractor.

Veredictos por cifra (revisados contra la imagen de la pagina original):
  'ok'      el valor extraido es correcto
  numero    el valor extraido es incorrecto; el numero es la cifra verdadera
  texto     incorrecto sin cifra verdadera legible en la tira (motivo)
  'nv'      no verificable en la tira (la linea no aparece entera)
  'falta'   la cifra existe en las cuentas pero no se extrajo
"""
import sys
import numpy as np
import pandas as pd

V = ["ingresos", "resultado_antes_impuestos", "activos_netos", "patrimonio", "gastos_personal", "sueldos_salarios"]
OK5 = ["ingresos", "resultado_antes_impuestos", "activos_netos", "patrimonio", "sueldos_salarios"]
OK4 = ["ingresos", "resultado_antes_impuestos", "activos_netos", "sueldos_salarios"]

def todos(vs):
    return {v: "ok" for v in vs}

VER = {
    0: todos(["ingresos", "resultado_antes_impuestos", "activos_netos", "patrimonio"]),
    1: {"patrimonio": "ok"},
    2: todos(V),
    3: {"ingresos": "ok", "patrimonio": "ok", "sueldos_salarios": "ok", "resultado_antes_impuestos": "falta"},
    4: todos(OK5),
    5: {"ingresos": "ok", "resultado_antes_impuestos": "ok", "patrimonio": "ok", "sueldos_salarios": "ok"},
    6: {"ingresos": "ok", "resultado_antes_impuestos": "ok", "activos_netos": "ok", "patrimonio": "ok",
        "gastos_personal": "mal: es la linea de sueldos, no el total de personal"},
    7: {"ingresos": "ok", "patrimonio": "ok", "sueldos_salarios": "ok", "resultado_antes_impuestos": "falta"},
    8: {"ingresos": "ok", "resultado_antes_impuestos": "ok", "patrimonio": "ok"},
    9: {"ingresos": "ok", "resultado_antes_impuestos": "nv", "patrimonio": "ok", "sueldos_salarios": "ok"},
    10: {"ingresos": 74302, "resultado_antes_impuestos": "ok", "activos_netos": "ok", "patrimonio": "ok",
         "gastos_personal": "ok", "sueldos_salarios": "ok"},
    11: todos(OK5),
    12: {"ingresos": "ok", "resultado_antes_impuestos": "nv", "activos_netos": "ok", "patrimonio": "ok", "gastos_personal": "ok"},
    13: todos(OK5),
    14: {"ingresos": "ok", "resultado_antes_impuestos": "mal: -63 es un trozo de otra columna", "patrimonio": "ok"},
    15: {"ingresos": "ok", "resultado_antes_impuestos": "ok", "activos_netos": "ok", "patrimonio": "ok", "gastos_personal": "nv"},
    16: todos(OK5),
    17: {"ingresos": 5505.354, "resultado_antes_impuestos": "ok", "sueldos_salarios": "ok", "activos_netos": "falta"},
    18: {"patrimonio": "ok"},
    19: {"ingresos": "ok", "resultado_antes_impuestos": "nv", "patrimonio": "ok", "sueldos_salarios": "ok"},
    20: {"ingresos": "ok", "resultado_antes_impuestos": "nv", "activos_netos": "ok", "patrimonio": "ok", "gastos_personal": "nv"},
    21: {"ingresos": "ok", "resultado_antes_impuestos": "ok", "patrimonio": "mal: es 'total equity and liabilities'"},
    22: todos(OK5),
    23: {"ingresos": "ok", "resultado_antes_impuestos": "nv", "activos_netos": "ok", "patrimonio": "ok", "sueldos_salarios": "ok"},
    24: {"ingresos": "ok", "resultado_antes_impuestos": "nv", "activos_netos": "ok", "patrimonio": "ok", "sueldos_salarios": "ok"},
    25: todos(["ingresos", "resultado_antes_impuestos", "activos_netos", "patrimonio"]),
    26: {"ingresos": "ok", "resultado_antes_impuestos": "nv", "activos_netos": "ok", "patrimonio": "ok",
         "gastos_personal": "mal: 7.000 no es el gasto de personal"},
    27: {"ingresos": "ok", "resultado_antes_impuestos": "ok", "sueldos_salarios": "ok", "activos_netos": "falta"},
    28: todos(OK5),
    29: {"activos_netos": "ok", "patrimonio": "ok"},
    30: {"activos_netos": "ok", "patrimonio": "ok"},
    31: {"patrimonio": "ok"},
    32: {"ingresos": "ok", "resultado_antes_impuestos": "ok", "sueldos_salarios": "ok", "activos_netos": "falta"},
    33: todos(["ingresos", "resultado_antes_impuestos", "activos_netos", "patrimonio", "gastos_personal"]),
    34: {},   # documento duplicado del 22: no se cuenta dos veces
    35: {"ingresos": 332211, "resultado_antes_impuestos": "nv", "activos_netos": "ok", "patrimonio": "ok", "sueldos_salarios": "ok"},
    36: todos(OK5), 37: todos(OK5),
    38: todos(["ingresos", "resultado_antes_impuestos", "activos_netos", "patrimonio"]),
    39: todos(OK5), 40: todos(OK5), 41: todos(OK5),
    42: {"ingresos": "ok", "resultado_antes_impuestos": "ok", "activos_netos": -80928.554, "sueldos_salarios": "ok"},
    43: todos(OK5),
    44: {"resultado_antes_impuestos": "ok", "activos_netos": "ok", "patrimonio": "ok", "sueldos_salarios": "ok", "ingresos": "falta"},
    45: todos(OK5), 46: todos(OK5), 47: todos(OK5),
    48: todos(OK4),
    49: todos(["ingresos", "resultado_antes_impuestos", "activos_netos", "patrimonio", "gastos_personal"]),
    50: todos(["ingresos", "resultado_antes_impuestos", "activos_netos", "gastos_personal"]),
    51: todos(OK4), 52: todos(OK4),
    53: {"activos_netos": "ok", "sueldos_salarios": "ok", "ingresos": "falta", "resultado_antes_impuestos": "falta"},
    54: todos(OK4),
    55: {"ingresos": "ok", "resultado_antes_impuestos": "ok", "activos_netos": 41774, "patrimonio": "ok", "sueldos_salarios": "ok"},
    56: {"activos_netos": "ok", "patrimonio": "ok"},
    57: {"ingresos": "ok", "resultado_antes_impuestos": "nv", "activos_netos": 134470, "patrimonio": 134470, "sueldos_salarios": "ok"},
    58: todos(V),
    59: {"ingresos": "ok", "resultado_antes_impuestos": "ok", "sueldos_salarios": "ok", "activos_netos": "falta"},
}

def main():
    base = sys.argv[1] if len(sys.argv) > 1 else "."
    sel = pd.read_csv(f"{base}/datos_fase2/auditoria/muestra_validacion_docs.csv", dtype={"numero": str}).reset_index(drop=True)
    ref = f"{base}/datos_fase2/auditoria/validacion_referencia.csv"
    try:
        prev = pd.read_csv(ref, dtype={"numero": str})
    except FileNotFoundError:
        prev = None
    x = pd.read_csv(f"{base}/datos_fase2/cifras_ocr_largo.csv", dtype={"numero": str})
    rows = []
    for k, r in sel.iterrows():
        e = x[x.documento == r.documento].drop_duplicates("variable").set_index("variable").actual
        for v, vv in VER.get(k, {}).items():
            ext = e.get(v, np.nan)
            if prev is not None:   # la verdad queda fijada en el primer registro
                p = prev[(prev.id == k) & (prev.variable == v)]
                verdad = p.verdad.iloc[0] if len(p) else np.nan
                vv0 = p.veredicto.iloc[0] if len(p) else vv
            else:
                vv0 = vv
                verdad = ext if vv == "ok" else (vv if not isinstance(vv, str) else np.nan)
            if vv0 == "nv":
                res = "no_verificable"
            elif pd.notna(verdad):
                res = "correcto" if pd.notna(ext) and abs(ext - float(verdad)) <= 1 else ("falta" if pd.isna(ext) else "incorrecto")
            elif vv0 == "falta":
                res = "correcto_ahora?" if pd.notna(ext) else "falta"
            else:
                res = "incorrecto" if pd.notna(ext) else "falta"
            rows.append(dict(id=k, numero=r.numero, documento=r.documento, variable=v, veredicto=vv0,
                             verdad=verdad, extraido=ext, resultado=res))
    t = pd.DataFrame(rows)
    if prev is None:
        t.to_csv(ref, index=False)
    print(t.resultado.value_counts().to_string())
    c = t[t.resultado.isin(["correcto", "incorrecto"])]
    f = t[t.resultado.isin(["correcto", "incorrecto", "falta"])]
    print(f"precision {100 * (c.resultado == 'correcto').mean():.1f}% ({(c.resultado == 'correcto').sum()}/{len(c)})")
    print(f"exhaustividad {100 * (f.resultado == 'correcto').mean():.1f}% ({(f.resultado == 'correcto').sum()}/{len(f)})")
    print(t[~t.resultado.isin(["correcto", "no_verificable"])][["id", "variable", "verdad", "extraido", "resultado"]].to_string(index=False))

if __name__ == "__main__":
    main()

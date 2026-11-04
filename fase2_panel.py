"""
FASE 2f - Panel financiero club x temporada, con validacion de cada cifra (v2, tras la auditoria).

1. Junta iXBRL (exacto), texto de iXBRL y OCR. Solo documentos del inventario limpio.
2. Por sociedad y cierre se queda con un documento (iXBRL > OCR; el que aporta mas partidas).
3. CONTRASTE ENTRE AÑOS: la cifra del año t debe reaparecer como 'año anterior' en t+1.
   Si no coincide, se CLASIFICA la discrepancia:
     unidades  (x1000 / /1000)      -> se corrige con la lectura coherente con los años vecinos
     signo     (mismo valor, signo opuesto; tipico del impuesto) -> se unifica
     digito    (difiere en 1-2 digitos: error de OCR) -> se elige la que cumple las identidades
     reexpresion (el club cambio la cifra) -> se guardan ambas: publicada y reexpresada
     sin_resolver -> va a la lista de revision manual
4. IDENTIDADES: activos netos = patrimonio; resultado antes de impuestos + impuesto = neto.
5. PLAUSIBILIDAD: ingresos 3-1.000 M£; personal/ingresos 0,2-4; saltos x10 respecto a años vecinos.
6. CORRECCIONES MANUALES: datos_fase2/correcciones_manuales.csv (numero, cierre, variable,
   valor, documento, pagina, motivo) sustituyen a la cifra extraida y quedan registradas.

Salidas (datos_fase2/): panel_largo.csv, panel_financiero.csv, calidad_panel.csv, revision_manual.csv
Uso:  python fase2_panel.py
"""
import numpy as np
import pandas as pd
from pathlib import Path

BASE = Path(__file__).resolve().parent
D2 = BASE / "datos_fase2"
CLAVE = ["ingresos", "gastos_personal", "resultado_antes_impuestos", "activos_netos", "patrimonio",
         "acreedores_cp", "acreedores_lp", "caja"]

def cerca(a, b, rel=0.005):
    return (a - b).abs() <= np.maximum(1.5, rel * b.abs())

def digitos_distintos(a, b):
    sa, sb = str(int(round(abs(a)))), str(int(round(abs(b))))
    if len(sa) != len(sb):
        return 99
    return sum(x != y for x, y in zip(sa, sb))

def main():
    inv = pd.read_csv(D2 / "inventario_cuentas_limpio.csv", dtype=str)
    validos = set(inv.cierre + "_" + inv.transaction_id)
    ocr = pd.read_csv(D2 / "cifras_ocr_largo.csv", dtype={"numero": str}).assign(fuente="ocr")
    ix = pd.read_csv(D2 / "cifras_ixbrl_largo.csv", dtype={"numero": str})
    ix["fuente"] = np.where(ix.bloque == "ixbrl_texto", "ixbrl_texto", "ixbrl")
    d = pd.concat([ix, ocr], ignore_index=True)
    d = d[d.documento.isin(validos)]
    # los gastos de personal son costes: unas cuentas los imprimen entre parentesis y otras no
    per = d.variable.isin(["gastos_personal", "sueldos_salarios", "seguridad_social", "pensiones"])
    d.loc[per, ["actual", "anterior"]] = d.loc[per, ["actual", "anterior"]].abs()
    publicada = (d[d.variable == "cuenta_resultados_publicada"][["numero", "cierre", "actual"]]
                 .drop_duplicates(["numero", "cierre"]).rename(columns={"actual": "pyg_publicada"}))
    d = d[d.variable != "cuenta_resultados_publicada"]

    n = d.groupby(["numero", "cierre", "documento"]).agg(n=("variable", "size"), ix=("fuente", lambda s: (s == "ixbrl").any())).reset_index()
    tipo = dict(zip(inv.cierre + "_" + inv.transaction_id, inv.tipo))
    n["original"] = n.documento.map(lambda x: tipo.get(x) == "AA")
    elegido = n.sort_values(["ix", "original", "n"], ascending=False).drop_duplicates(["numero", "cierre"])
    d = d.merge(elegido[["numero", "cierre", "documento"]], on=["numero", "cierre", "documento"])
    d = d.sort_values("fuente").drop_duplicates(["numero", "cierre", "variable"])   # ixbrl > ixbrl_texto > ocr

    # --- contraste entre años
    d["cie"] = pd.to_datetime(d.cierre)
    d = d.sort_values(["numero", "variable", "cie"]).reset_index(drop=True)
    g = d.groupby(["numero", "variable"])
    d["sig_anterior"] = g.anterior.shift(-1)
    if "reexpresado" not in d:
        d["reexpresado"] = np.nan
    d["sig_reexp"] = g.reexpresado.shift(-1).fillna(False).astype(bool)
    d["sig_cie"] = g.cie.shift(-1)
    d["prev_actual"] = g.actual.shift(1)
    d["next_actual"] = g.actual.shift(-1)
    # un comparativo 0 suele ser un guion leido de la columna equivocada: no sirve de contraste
    hay = d.sig_anterior.notna() & (d.sig_anterior != 0) & d.actual.notna()
    consec = (d.sig_cie - d.cie).dt.days.between(300, 430) & hay
    d["valor"] = d.actual
    d["valor_reexpresado"] = np.nan
    d["estado"] = np.where(d.fuente == "ixbrl", "ixbrl_exacta", "sin_contraste")
    ok = consec & cerca(d.actual, d.sig_anterior)
    d.loc[ok, "estado"] = "validada"
    mal = consec & ~ok

    def tipo_error(a, b):
        sa, sb = str(int(round(abs(a)))), str(int(round(abs(b))))
        if np.sign(a) == -np.sign(b) and abs(abs(a) - abs(b)) <= max(1.5, 0.005 * abs(b)):
            return "signo"
        r = abs(a / b) if b else np.inf
        if 900 <= r <= 1100 or 1 / 1100 <= r <= 1 / 900:
            return "unidades"
        if len(sa) != len(sb):
            corto, largo = sorted((sa, sb), key=len)
            if len(corto) >= 3 and largo.endswith(corto):
                return "truncado"
            if len(largo) - len(corto) == 1 and (largo[1:] == corto or largo[:-1] == corto or
                                                 any(largo[:i] + largo[i+1:] == corto for i in range(len(largo)))):
                return "digito"
            return "otro"
        return "digito" if sum(x != y for x, y in zip(sa, sb)) <= 2 else "otro"

    def lejania(c, ref):
        return abs(np.log(abs(c) / abs(ref))) if c and ref and not np.isnan(ref) else np.inf

    for i in d.index[mal]:
        a, b = d.at[i, "actual"], d.at[i, "sig_anterior"]
        vec = [v for v in (d.at[i, "prev_actual"], d.at[i, "next_actual"]) if pd.notna(v) and v != 0]
        ref = float(np.median(vec)) if vec else np.nan
        t = tipo_error(a, b)
        if t == "signo":
            d.at[i, "estado"] = "validada_signo"
            if d.at[i, "variable"] == "impuesto":
                d.at[i, "valor"] = b
            continue
        la, lb = lejania(a, ref), lejania(b, ref)
        if t == "truncado":
            d.at[i, "valor"] = a if abs(a) > abs(b) else b
            d.at[i, "estado"] = "corregida_ocr"
            continue
        if t == "digito":
            d.at[i, "estado"] = "conflicto_digito"         # se decide con las identidades o queda en conflicto
            continue
        if t == "unidades":
            if np.isinf(la) and np.isinf(lb):
                d.at[i, "estado"] = "conflicto_digito"     # se decide con las identidades
            else:
                d.at[i, "valor"] = a if la <= lb else b
                d.at[i, "estado"] = "corregida_" + ("unidades" if t == "unidades" else "ocr")
            continue
        own_prev = d.at[i, "anterior"]
        if pd.notna(own_prev) and abs(a - own_prev) <= max(1.5, 0.0005 * abs(own_prev)):
            d.at[i, "valor"] = b                          # se leyo dos veces la columna del año anterior
            d.at[i, "estado"] = "corregida_columna"
            continue
        if abs(a - b) <= 0.15 * max(abs(a), abs(b)) and d.at[i, "sig_reexp"]:
            d.at[i, "estado"] = "reexpresion"             # el club cambio la cifra del año anterior y lo indica
            d.at[i, "valor_reexpresado"] = b
            continue
        # sin patron de error de lectura no se adivina: puede ser una reexpresion grande
        # (p. ej. transicion a FRS 102 en 2015-16). Queda en conflicto y fuera del panel fiable.
        d.at[i, "estado"] = "conflicto"
        d.at[i, "valor_reexpresado"] = b

    # años que faltan pero aparecen como comparativo en t+1
    # El comparativo de la cuenta de t+1 se refiere al ejercicio anterior. Si ese ejercicio tiene cuenta propia
    # (aunque su fecha de cierre no sea exactamente un ano antes: cambios de fecha de cierre, ejercicios de 13
    # meses), el hueco se asigna a ESA fecha de cierre; solo si no hay cuenta se crea el cierre t-1 ano.
    # (Antes se creaba siempre t-1 ano y salian club-temporadas duplicadas.)
    extra = d[d.anterior.notna()].copy()
    cierres = d.groupby("numero").cie.apply(lambda s: sorted(set(s))).to_dict()
    def destino(n, c):
        # ejercicios cortos (6-7 meses) o largos (hasta 18 meses) por cambio de fecha de cierre
        cand = [x for x in cierres.get(n, []) if 150 <= (c - x).days <= 560]
        return min(cand, key=lambda x: abs((c - x).days - 365)) if cand else c - pd.DateOffset(years=1)
    extra["cie"] = [destino(n, c) for n, c in zip(extra.numero, extra.cie)]
    clave_existente = set(zip(d.numero, d.cie, d.variable))
    extra = extra[[(x, y, z) not in clave_existente for x, y, z in zip(extra.numero, extra.cie, extra.variable)]]
    extra = extra[extra.anterior != 0]
    extra["reexp_origen"] = extra.reexpresado.fillna(False).astype(bool)
    extra = extra.assign(valor=extra.anterior, actual=np.nan, estado="desde_año_siguiente",
                         cierre=extra.cie.dt.strftime("%Y-%m-%d"), valor_reexpresado=np.nan)
    d = pd.concat([d, extra], ignore_index=True)

    # --- identidades: resuelven los conflictos de digito
    w = d.pivot_table(index=["numero", "cierre"], columns="variable", values="valor", aggfunc="first")
    for c in ["activos_netos", "patrimonio", "resultado_antes_impuestos", "impuesto", "resultado_neto"]:
        if c not in w: w[c] = np.nan
    w["check_balance"] = np.where(w.activos_netos.isna() | w.patrimonio.isna(), "",
                                  np.where(cerca(w.activos_netos, w.patrimonio), "ok", "falla"))
    falta = w[["resultado_antes_impuestos", "impuesto", "resultado_neto"]].isna().any(axis=1)
    w["check_resultados"] = np.where(falta, "", np.where(cerca(w.resultado_antes_impuestos + w.impuesto, w.resultado_neto), "ok", "falla"))
    idx = d.set_index(["numero", "cierre"]).index
    chk_bal = w.check_balance.reindex(idx).values
    chk_res = w.check_resultados.reindex(idx).values
    pertenece_bal = d.variable.isin(["activos_netos", "patrimonio"]).values
    pertenece_res = d.variable.isin(["resultado_antes_impuestos", "impuesto", "resultado_neto"]).values
    cumple = (pertenece_bal & (chk_bal == "ok")) | (pertenece_res & (chk_res == "ok"))
    m = (d.estado == "conflicto_digito").values
    d.loc[m & cumple, "estado"] = "resuelta_identidad"
    d.loc[m & ~cumple, "estado"] = "conflicto"

    # --- plausibilidad
    d["sospechosa"] = ""
    if "reexp_origen" in d:
        d.loc[d.reexp_origen.fillna(False).astype(bool), "sospechosa"] = "comparativo de una cuenta que reexpresa: no es la cifra original"
    ing = d.variable.eq("ingresos")
    d.loc[ing & ~d.valor.abs().between(3000, 1_000_000), "sospechosa"] = "ingresos fuera de 3-1000 M£"
    d = d.sort_values(["numero", "variable", "cierre"])
    gg = d.groupby(["numero", "variable"]).valor
    vec = pd.concat([gg.shift(1), gg.shift(-1)], axis=1).abs().median(axis=1)
    salto = (d.valor.abs() > 10 * vec) | (d.valor.abs() < vec / 10)
    # el salto x10 solo tiene sentido en partidas estables (el resultado o la caja pueden saltar de verdad)
    estables = d.variable.isin(["ingresos", "gastos_personal", "sueldos_salarios"])
    d.loc[salto & estables & (vec > 50) & (d.sospechosa == ""), "sospechosa"] = "salto x10 respecto a años vecinos"

    # --- coherencia interna del documento
    #  a) balance: si activos netos y patrimonio no cuadran y uno esta validado, manda el validado
    #  b) gasto de personal total debe estar entre sueldos y 1,6 x sueldos
    piv = d.pivot_table(index=["numero", "cierre"], columns="variable", values="valor", aggfunc="first")
    est = d.pivot_table(index=["numero", "cierre"], columns="variable", values="estado", aggfunc="first")
    for (num, cie), fila in piv.iterrows():
        an, pa = fila.get("activos_netos"), fila.get("patrimonio")
        if pd.notna(an) and pd.notna(pa) and abs(an - pa) > max(1.5, 0.005 * abs(pa)):
            ea, ep = est.at[(num, cie), "activos_netos"], est.at[(num, cie), "patrimonio"]
            buenos = ("validada", "ixbrl_exacta", "corregida_ocr", "corregida_vecinos")
            k = (d.numero == num) & (d.cierre == cie)
            sa, sp = str(int(round(abs(an)))), str(int(round(abs(pa))))
            if len(sa) != len(sp) and (sa.endswith(sp) or sp.endswith(sa)) and min(len(sa), len(sp)) >= 3:
                largo = an if len(sa) > len(sp) else pa       # el OCR perdio digitos iniciales en la corta
                k = (d.numero == num) & (d.cierre == cie)
                d.loc[k & d.variable.isin(["activos_netos", "patrimonio"]), ["valor"]] = largo
                d.loc[k & d.variable.isin(["activos_netos", "patrimonio"]) & (d.valor != largo), "estado"] = "corregida_identidad"
                continue
            if ep in buenos and ea not in buenos:
                d.loc[k & (d.variable == "activos_netos"), ["valor", "estado"]] = [pa, "corregida_identidad"]
            elif ea in buenos and ep not in buenos:
                d.loc[k & (d.variable == "patrimonio"), ["valor", "estado"]] = [an, "corregida_identidad"]
            else:
                # sin una cifra validada que mande: la de menor garantia (o las dos) queda en conflicto
                rango = lambda e: 2 if e in buenos else (1 if e == "desde_año_siguiente" else 0)
                ra, rp = rango(ea), rango(ep)
                malas = ["activos_netos", "patrimonio"] if ra == rp else (["patrimonio"] if ra > rp else ["activos_netos"])
                d.loc[k & d.variable.isin(malas), "estado"] = "conflicto"
        gp, ss = fila.get("gastos_personal"), fila.get("sueldos_salarios")
        if pd.notna(gp) and pd.notna(ss) and ss > 0 and not (0.98 * ss <= gp <= 1.6 * ss):
            k = (d.numero == num) & (d.cierre == cie) & (d.variable == "gastos_personal")
            d.loc[k, "sospechosa"] = "gasto de personal incoherente con sueldos"

    # --- derivadas por identidad (activos netos = total patrimonio neto)
    fiable = ~d.estado.isin(["conflicto"]) & (d.sospechosa == "")
    claves = set(zip(d.numero, d.cierre, d.variable))
    nuevas = []
    for origen, destino in (("activos_netos", "patrimonio"), ("patrimonio", "activos_netos")):
        for _, r in d[fiable & (d.variable == origen)].iterrows():
            if (r.numero, r.cierre, destino) not in claves:
                nuevas.append({**r.to_dict(), "variable": destino, "actual": np.nan, "anterior": np.nan,
                               "estado": "derivada_identidad", "etiqueta_ocr": f"= {origen}"})
    if nuevas:
        d = pd.concat([d, pd.DataFrame(nuevas)], ignore_index=True)

    # --- correcciones manuales
    fcm = D2 / "correcciones_manuales.csv"
    if fcm.exists():
        cm = pd.read_csv(fcm, dtype={"numero": str})
        for _, r in cm.iterrows():
            k = (d.numero == r.numero) & (d.cierre == r.cierre) & (d.variable == r.variable)
            if k.any():
                d.loc[k, ["valor", "estado", "sospechosa"]] = [r.valor, "corregida_manual", ""]
            else:
                d = pd.concat([d, pd.DataFrame([{"numero": r.numero, "cierre": r.cierre, "variable": r.variable,
                                                 "valor": r.valor, "estado": "corregida_manual", "fuente": "manual",
                                                 "documento": r.documento, "pagina": r.pagina}])], ignore_index=True)

    # --- panel ancho
    mapa = pd.read_csv(BASE / "datos_fase1" / "mapa_sociedades.csv", dtype=str).fillna("")
    rol = {}
    for _, r in mapa.iterrows():
        if r.numero_club: rol.setdefault(r.numero_club, (r.club, "club"))
        if r.numero_grupo: rol.setdefault(r.numero_grupo, (r.club, "grupo"))
    d = d[d.numero.isin(rol)]
    w = d.pivot_table(index=["numero", "cierre"], columns="variable", values="valor", aggfunc="first")
    w2 = d.assign(prob=d.estado.isin(["conflicto", "sin_contraste"]) | (d.sospechosa != "")).groupby(["numero", "cierre"]).prob.sum().rename("n_cifras_dudosas")
    panel = w.join(w2).reset_index()
    panel["club"] = panel.numero.map(lambda x: rol[x][0]); panel["rol"] = panel.numero.map(lambda x: rol[x][1])
    c = pd.to_datetime(panel.cierre)
    ini = np.where(c.dt.month <= 9, c.dt.year - 1, c.dt.year)
    panel["temporada"] = [f"{a}/{str(a + 1)[-2:]}" for a in ini]
    panel = panel.merge(publicada, on=["numero", "cierre"], how="left")
    # duracion del ejercicio y cierre principal de cada temporada (si un cambio de fecha de cierre deja dos
    # cierres en la misma temporada, el principal es el ultimo: el que cubre el final de la temporada)
    panel = panel.sort_values(["numero", "cierre"])
    cc = pd.to_datetime(panel.cierre)
    panel["meses_ejercicio"] = (cc - cc.groupby(panel.numero).shift(1)).dt.days.div(30.44).round()
    panel.loc[panel.meses_ejercicio > 24, "meses_ejercicio"] = np.nan     # hueco entre cuentas, no un ejercicio
    panel["cierre_principal_temporada"] = ~panel.duplicated(["numero", "temporada"], keep="last")

    # --- indicadores de la cuenta (para los modelos de la fase 3)
    inv_aa = inv[inv.tipo == "AA"].copy()
    inv_aa["tipo_cuenta"] = inv_aa.descripcion.str.replace("accounts-(amended-)?with-(accounts-type-)?", "", regex=True)
    info = inv_aa.sort_values("depositada").drop_duplicates(["numero", "cierre"], keep="first")[
        ["numero", "cierre", "tipo_cuenta", "depositada", "dias_fuera_plazo", "fuera_plazo_claro"]]
    panel = panel.merge(info, on=["numero", "cierre"], how="left")
    # sin cuenta propia: la fila solo existe por el comparativo de la cuenta siguiente
    panel["cuenta_depositada"] = panel.tipo_cuenta.notna()
    panel["cuenta_abreviada"] = panel.tipo_cuenta.fillna("").str.contains("small|micro|abridged|total-exemption")
    panel["cuenta_inactiva"] = panel.tipo_cuenta.fillna("").eq("dormant")
    # holdings que no consolidan al club (comprobado en la revision manual): sus cifras no representan al club
    sin_consolidar = {"03912084": None, "07230595": {"2013-06-30", "2014-06-30"}}
    panel["holding_sin_consolidar"] = [n in sin_consolidar and (sin_consolidar[n] is None or c in sin_consolidar[n])
                                       for n, c in zip(panel.numero, panel.cierre)]
    prim = ["club", "rol", "numero", "temporada", "cierre", "meses_ejercicio", "cierre_principal_temporada", "cuenta_depositada",
            "tipo_cuenta", "cuenta_abreviada", "cuenta_inactiva", "holding_sin_consolidar", "depositada", "dias_fuera_plazo",
            "fuera_plazo_claro", "n_cifras_dudosas", "pyg_publicada"]
    panel = panel[prim + [x for x in panel.columns if x not in prim]].sort_values(["club", "rol", "cierre"])
    panel.to_csv(D2 / "panel_financiero.csv", index=False)

    cols = ["numero", "cierre", "variable", "valor", "valor_reexpresado", "actual", "anterior", "sig_anterior",
            "estado", "sospechosa", "fuente", "documento", "pagina", "etiqueta_ocr"]
    d[[x for x in cols if x in d]].sort_values(["numero", "cierre", "variable"]).to_csv(D2 / "panel_largo.csv", index=False)

    # --- revision manual: cifras clave dudosas de club-temporadas en Premier/Championship
    ct = pd.read_csv(BASE / "datos_fase1" / "clubes_temporada.csv")
    dd = d.copy()
    dd["club"] = dd.numero.map(lambda x: rol[x][0])
    cc = pd.to_datetime(dd.cierre); ini = np.where(cc.dt.month <= 9, cc.dt.year - 1, cc.dt.year)
    dd["temporada"] = [f"{a}/{str(a + 1)[-2:]}" for a in ini]
    dd = dd.merge(ct[["club", "temporada", "division"]], on=["club", "temporada"])
    rev = dd[dd.variable.isin(CLAVE) & (dd.estado.isin(["conflicto"]) | (dd.sospechosa != ""))]
    rev[["club", "temporada", "division", "numero", "cierre", "variable", "valor", "valor_reexpresado",
         "estado", "sospechosa", "documento", "pagina"]].sort_values(["club", "temporada"]).to_csv(D2 / "revision_manual.csv", index=False)

    cal = d.groupby("variable").estado.value_counts().unstack(fill_value=0)
    cal["total"] = cal.sum(axis=1)
    cal["sospechosas"] = d[d.sospechosa != ""].groupby("variable").size()
    cal = cal.fillna(0).sort_values("total", ascending=False)
    cal.to_csv(D2 / "calidad_panel.csv")
    print(cal.to_string())
    print("\nbalance:", panel.columns.size, "| identidades balance:", (w.reindex(columns=["activos_netos"]).notna().sum()).to_dict())
    print(f"Revision manual: {len(rev)} cifras clave")
    print(f"Panel: {len(panel)} filas, {panel.club.nunique()} clubes")

if __name__ == "__main__":
    main()

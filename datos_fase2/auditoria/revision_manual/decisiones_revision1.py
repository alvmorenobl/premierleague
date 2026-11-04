"""Decisiones de la revision manual dirigida (4 nov 2026), cifra a cifra contra la imagen de la pagina del PDF
(C:\\datos_premier\\revision\\R00-R28.png). 'ok' = la cifra leida coincide con la impresa (se confirma).
Un numero = la cifra impresa (miles de libras) cuando la lectura era erronea o faltaba.
(item, valor, motivo); variable distinta de la del item: (item, valor, motivo, variable)."""
import sys, pandas as pd, numpy as np

D = [
 (9,"ok",""),(183,"ok",""),
 (154,11808.0,"OCR leyo 7; impreso 11,808"),(245,"ok",""),(64,"ok",""),(65,-3540.590,"balance del grupo, columna grupo"),
 (59,"ok",""),(66,"ok",""),(238,"ok",""),
 (120,"ok",""),(114,"ok",""),(200,79326.0,"OCR leyo 719,326"),(44,"ok",""),(47,"ok",""),(48,"ok",""),
 (266,33204.755,"etiqueta 'Salaries and wages'"),
 (260,46165.0,"formato 6 columnas: se leyo el ano anterior"),(262,"ok",""),(10,"ok",""),
 (274,27015.315,"etiqueta 'Salaries and wages'"),(172,"ok",""),(54,0.0,"primer ejercicio sin ingresos ('-')"),(228,"ok",""),
 (121,272.0,"formato 4 columnas: total"),(122,15903.0,"OCR leyo 45,903"),(32,13227.093,"OCR leyo 0.093"),
 (246,"ok",""),(60,-2116.535,"lectura erronea"),(115,11042.457,"OCR leyo 44,042,457"),(203,20831.699,"lectura erronea"),
 (275,40031.142,"etiqueta 'Salaries and wages'"),(267,38501.292,"etiqueta 'Salaries and wages'"),(162,-17052.0,"OCR leyo 57,052"),
 (0,"ok",""),(61,"ok",""),(116,"ok",""),(268,26811.642,"etiqueta 'Salaries and wages'"),(163,"ok",""),
 (164,-54081.0,"shareholders' funds"),(186,-220.0,"shareholders' funds"),(226,180541.0,"formato 6 columnas: se leyo el ano anterior"),
 (62,90401.306,"lectura erronea"),(178,167.212,"lectura erronea"),(165,-76716.0,"shareholders' funds"),(166,"ok",""),
 (269,"ok",""),(270,"ok",""),(271,23056.799,"etiqueta 'Salaries and wages'"),(139,"ok",""),(277,"ok",""),(278,"ok",""),
 (187,12618.0,"shareholders' funds"),
 (279,24494.616,"etiqueta 'Salaries and wages'"),(175,112072.0,"OCR leyo '0 412,072'"),(197,"ok",""),(198,"ok",""),
 (263,120747.0,"formato 6 columnas: se leyo el ano anterior"),(81,"ok",""),
 (82,"ok",""),(67,"ok",""),(123,"ok",""),(52,"ok",""),
 (53,"ok",""),(101,"ok",""),(102,"ok",""),(156,"ok",""),(221,"ok",""),(15,-180070.882,"lectura erronea"),(141,-41022.0,"'Net (liabilities)/assets'"),
 (195,"ok",""),(158,"ok",""),(159,"ok",""),(2,"ok",""),(3,"ok",""),(16,"ok",""),
 (201,"ok",""),(202,"ok",""),(205,"ok",""),(206,"ok",""),(215,"ok",""),(45,31411.0,"OCR leyo 34,414"),(253,"ok",""),
 (36,"ok",""),(179,"ok",""),(108,"ok",""),(157,125755.0,"OCR leyo 128,755"),(207,"ok",""),(280,-1625.312,"lectura erronea"),
 (281,"ok",""),(176,24697.0,"OCR leyo 26,697"),(167,"ok",""),(135,"ok",""),(230,4027.590,"formato 6 columnas: se leyo el ano anterior"),
 (180,7687.356,"lectura erronea"),(119,"ok",""),
 (239,69779.0,"etiqueta 'Wage and salaries'"),(222,"ok",""),(223,"ok",""),(208,19704.504,"lectura erronea"),(168,"ok",""),
 (83,189159.0,"celdas sombreadas"),(84,127827.0,"celdas sombreadas"),(117,"ok",""),(160,"ok",""),(21,"ok",""),(22,"ok",""),
 (240,82613.0,"etiqueta 'Wage and salaries'"),
 (69,35249.283,"lectura erronea"),(68,150346.0,"OCR leyo 160,346"),(209,"ok",""),(188,"ok",""),(189,"ok",""),(49,"ok",""),(29,"ok",""),
 (37,"ok",""),(109,"ok",""),(110,"ok",""),(111,"ok",""),(283,0.0,"sociedad holding sin ingresos ('-')"),
 (284,0.0,"'There were no staff costs'"),(254,-6742.0,"no leido"),(255,62614.0,"'Total Equity'"),
 (241,41786.0,"etiqueta 'Wage and salaries'"),(256,41786.0,"lectura erronea"),(6,"ok",""),(196,59692.0,"se leyo el ano anterior"),
 (23,"ok",""),(216,"ok",""),(217,"ok",""),(169,"ok",""),
 (118,2838.455,"lectura erronea"),(224,"ok",""),(88,"ok",""),(4,-18335.459,"lectura erronea"),(24,-9060.546,"lectura erronea"),
 (112,"ok",""),(113,"ok",""),(124,"ok",""),
 (244,59711.0,"etiqueta 'Wage and salaries' (periodo de 13 meses)"),(218,"ok",""),(177,19303.0,"OCR leyo 49,303"),(199,"ok",""),
 (103,"ok",""),(181,"ok",""),(89,"ok",""),
 (234,"ok",""),(235,"ok",""),(236,"ok",""),(184,115221.103,"OCR leyo 118,221,103"),(125,25919.909,"signo"),(126,"ok",""),(219,"ok",""),
 (220,"ok",""),(39,"ok",""),(264,"ok",""),(1,163743.904,"lectura erronea"),(129,148403.0,"OCR leyo 448,403"),(161,"ok",""),
 (225,186994.0,"'Staff costs (see note 5)': gasto de personal total","gastos_personal"),
 (17,54019.0,"lectura erronea"),(258,171.0,"lectura erronea"),(140,"ok",""),(92,"ok",""),(7,21368.017,"OCR leyo 24,368,017"),
 (127,"ok",""),(237,"ok",""),
 (185,"ok",""),(128,"ok",""),(134,"ok",""),(50,"ok",""),(46,"ok",""),(148,0.0,"holding sin actividad ('-')"),(149,0.0,"holding sin actividad ('-')"),
 (30,"ok",""),(38,"ok",""),(137,"ok",""),(5,-16081.826,"lectura erronea"),(97,302357.0,"OCR leyo 302,387"),(210,"ok",""),(211,"ok",""),
 (151,0.0,"holding sin actividad ('-')"),(152,0.0,"holding sin actividad ('-')"),
 (138,66823.168,"lectura erronea"),(8,"ok",""),
]

def main(base):
    it = pd.read_csv(f"{base}/../datos_premier_revision_items.csv", dtype={"numero": str}) if False else \
         pd.read_csv(sys.argv[2], dtype={"numero": str})
    l = pd.read_csv(f"{base}/datos_fase2/panel_largo.csv", dtype={"numero": str})
    filas = []
    for t in D:
        item, val, motivo = t[:3]
        r = it[it.item == item].iloc[0]
        var = t[3] if len(t) > 3 else r.variable
        if val == "ok":
            s = l[(l.numero == r.numero) & (l.cierre == r.cierre) & (l.variable == var)]
            val = float(s.actual.iloc[0]) if len(s) and pd.notna(s.actual.iloc[0]) else float(s.valor.iloc[0])
            motivo = "confirmada contra el PDF (la lectura era correcta; el contraste entre anos no coincidia)"
        filas.append(dict(numero=r.numero, cierre=r.cierre, variable=var, valor=val, documento=r.documento,
                          pagina=int(r.pagina), motivo="revision manual 4/11/2026: " + motivo, club=r.club, rol=r.rol))
        if var == "activos_netos":     # el balance muestra la misma cifra como patrimonio
            filas.append({**filas[-1], "variable": "patrimonio"})
    cm = pd.DataFrame(filas)
    cm.to_csv(f"{base}/datos_fase2/correcciones_manuales.csv", index=False)
    print(len(D), "decisiones ->", len(cm), "filas")

if __name__ == "__main__":
    main(sys.argv[1])

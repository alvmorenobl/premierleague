"""Tercera pasada de la revision manual (4 nov 2026): cifras clave que quedaban 'no fijadas con seguridad'.
Pagina completa del PDF a 100 ppp (C:\\datos_premier\\revision3\\*.png), texto del iXBRL, o texto OCR cuando las dos
pasadas (rapida y fina) coinciden. (numero, cierre, variable, valor en miles de libras, documento, pagina, motivo)."""
import sys, pandas as pd

D = [
 ("00036624","2022-06-30","ingresos",181007.0,"2022-06-30_MzM3NTAzMzU2MWFkaXF6a2N4",15,"cuenta de resultados consolidada (celdas sombreadas), vista en imagen"),
 ("00036624","2022-06-30","resultado_antes_impuestos",-44732.0,"2022-06-30_MzM3NTAzMzU2MWFkaXF6a2N4",15,"imagen; cifra original (la cuenta 2023 la reexpresa a -38,413)"),
 ("00036624","2023-06-30","ingresos",172155.0,"2023-06-30_MzQxNjg3ODY3NmFkaXF6a2N4",13,"imagen"),
 ("00036624","2023-06-30","resultado_antes_impuestos",-89090.0,"2023-06-30_MzQxNjg3ODY3NmFkaXF6a2N4",13,"imagen"),
 ("00036624","2024-06-30","ingresos",186902.0,"2024-06-30_MzQ2MTAzMDcwMmFkaXF6a2N4",14,"imagen"),
 ("00036624","2024-06-30","resultado_antes_impuestos",-53222.0,"2024-06-30_MzQ2MTAzMDcwMmFkaXF6a2N4",14,"imagen"),
 ("00036624","2025-06-30","ingresos",196697.0,"2025-06-30_MzUxMzk1MTE2NGFkaXF6a2N4",17,"imagen"),
 ("00036624","2025-06-30","resultado_antes_impuestos",-8609.0,"2025-06-30_MzUxMzk1MTE2NGFkaXF6a2N4",17,"imagen"),
 ("03912084","2012-06-30","ingresos",0.0,"2012-06-30_MzA3NDY0ODQyN2FkaXF6a2N4",8,"holding sin consolidar: solo gastos de administracion, sin cifra de negocio"),
 ("03912084","2012-06-30","activos_netos",0.0,"2012-06-30_MzA3NDY0ODQyN2FkaXF6a2N4",9,"holding sin consolidar: Net assets '-'"),
 ("03912084","2012-06-30","patrimonio",0.0,"2012-06-30_MzA3NDY0ODQyN2FkaXF6a2N4",9,"holding sin consolidar: Total shareholder's funds '-'"),
 ("03912084","2012-06-30","sueldos_salarios",0.0,"2012-06-30_MzA3NDY0ODQyN2FkaXF6a2N4",8,"holding sin consolidar sin personal (sin coste de personal en la cuenta)"),
 ("03912084","2016-06-30","ingresos",0.0,"2016-06-30_MzE3MTYwNDE1MWFkaXF6a2N4",9,"holding sin consolidar: solo gastos de administracion"),
 ("03912084","2016-06-30","activos_netos",0.0,"2016-06-30_MzE3MTYwNDE1MWFkaXF6a2N4",10,"holding sin consolidar: Total shareholder's funds '-'"),
 ("03912084","2016-06-30","patrimonio",0.0,"2016-06-30_MzE3MTYwNDE1MWFkaXF6a2N4",10,"holding sin consolidar"),
 ("03912084","2016-06-30","sueldos_salarios",0.0,"2016-06-30_MzE3MTYwNDE1MWFkaXF6a2N4",9,"holding sin consolidar sin personal"),
 ("07230595","2013-06-30","ingresos",0.0,"2013-06-30_MzA5NzQwMjU1NWFkaXF6a2N4",7,"holding sin consolidar (cuenta solo de la sociedad): sin cifra de negocio"),
 ("07230595","2013-06-30","resultado_antes_impuestos",0.0,"2013-06-30_MzA5NzQwMjU1NWFkaXF6a2N4",7,"holding sin consolidar: resultado '-'"),
 ("07230595","2013-06-30","sueldos_salarios",0.0,"2013-06-30_MzA5NzQwMjU1NWFkaXF6a2N4",7,"holding sin consolidar sin personal"),
 ("07230595","2014-06-30","ingresos",0.0,"2014-06-30_MzExODE0MTc2NmFkaXF6a2N4",7,"'The company has not traded during the year'"),
 ("07230595","2014-06-30","resultado_antes_impuestos",0.0,"2014-06-30_MzExODE0MTc2NmFkaXF6a2N4",7,"'neither profit or loss'"),
 ("07230595","2014-06-30","sueldos_salarios",0.0,"2014-06-30_MzExODE0MTc2NmFkaXF6a2N4",7,"sociedad sin actividad"),
 ("04305508","2014-05-31","ingresos",98691.997,"2014-05-31_MzExNjc1NjQ0OWFkaXF6a2N4",10,"cuenta consolidada, imagen"),
 ("04305508","2014-05-31","resultado_antes_impuestos",1325.873,"2014-05-31_MzExNjc1NjQ0OWFkaXF6a2N4",10,"cuenta consolidada, imagen"),
 ("03642327","2015-06-30","activos_netos",-5663.478,"2015-06-30_MzE0NDgzNTA4MGFkaXF6a2N4",14,"balance consolidado: total sin etiqueta (activos netos), imagen"),
 ("03642327","2015-06-30","patrimonio",-5663.478,"2015-06-30_MzE0NDgzNTA4MGFkaXF6a2N4",14,"por identidad con el total del balance consolidado"),
 ("00053301","2012-06-30","activos_netos",-33340.566,"2012-06-30_MzA3NTUxMTg4MmFkaXF6a2N4",10,"Shareholder's deficit, imagen"),
 ("00053301","2012-06-30","patrimonio",-33340.566,"2012-06-30_MzA3NTUxMTg4MmFkaXF6a2N4",10,"Shareholder's deficit, imagen"),
 ("00053301","2013-06-30","activos_netos",-12653.889,"2013-06-30_MzA5Nzc5MTI0OGFkaXF6a2N4",11,"Shareholder's deficit, imagen"),
 ("00053301","2013-06-30","patrimonio",-12653.889,"2013-06-30_MzA5Nzc5MTI0OGFkaXF6a2N4",11,"Shareholder's deficit, imagen"),
 ("00053301","2014-06-30","activos_netos",18319.413,"2014-06-30_MzEyMTAyMjE5NWFkaXF6a2N4",23,"texto OCR: conciliacion de fondos propios (cierre) = apertura de la cuenta 2015"),
 ("00053301","2014-06-30","patrimonio",18319.413,"2014-06-30_MzEyMTAyMjE5NWFkaXF6a2N4",23,"texto OCR: conciliacion de fondos propios"),
 ("00053301","2015-06-30","activos_netos",30471.057,"2015-06-30_MzEzMzU2NzkxOGFkaXF6a2N4",11,"texto OCR: balance y conciliacion coinciden"),
 ("00053301","2015-06-30","patrimonio",30471.057,"2015-06-30_MzEzMzU2NzkxOGFkaXF6a2N4",11,"texto OCR: balance y conciliacion coinciden"),
 ("07283993","2017-05-31","sueldos_salarios",16409.661,"2017-05-31_MzE5ODI3NTc1OWFkaXF6a2N4",22,"texto OCR (pasada rapida y fina coinciden): 'Salaries and wages'"),
 ("07612487","2012-05-31","sueldos_salarios",0.0,"2012-05-31_MzA4NjQ4MjM5NmFkaXF6a2N4",11,"'During the period, the company had no employees'"),
 ("07612487","2023-05-31","sueldos_salarios",16632.550,"2023-05-31_MzQxMzAzMTM3N2FkaXF6a2N4",0,"iXBRL: texto de la nota Employees"),
 ("06550400","2024-06-30","ingresos",19172.906,"2024-06-30_MzQ1ODg4ODcyMWFkaXF6a2N4",0,"iXBRL: linea Turnover de la cuenta de resultados (nota 3)"),
 ("03912084","2024-06-30","sueldos_salarios",0.0,"2024-06-30_MzQ1NTk5Njg5OWFkaXF6a2N4",6,"holding sin actividad: cuenta de resultados con todas las lineas '-' (sin gastos de administracion ni personal)"),
 ("03912084","2025-06-30","sueldos_salarios",0.0,"2025-06-30_MzUxMTg3OTQ4NWFkaXF6a2N4",6,"holding sin actividad: cuenta de resultados con todas las lineas '-'"),
 ("01621060","2025-06-30","activos_netos",30676.0,"2025-06-30_MzQ5NTY1NzcyNGFkaXF6a2N4",11,"balance consolidado (el de la sociedad, pag 12, es 54,406)"),
 ("01621060","2025-06-30","patrimonio",30676.0,"2025-06-30_MzQ5NTY1NzcyNGFkaXF6a2N4",11,"Equity shareholders' funds del balance consolidado"),
]

def main(base):
    cm = pd.read_csv(f"{base}/datos_fase2/correcciones_manuales.csv", dtype={"numero": str})
    mapa = pd.read_csv(f"{base}/datos_fase1/mapa_sociedades.csv", dtype=str).fillna("")
    rol = {**{r.numero_grupo: (r.club, "grupo") for r in mapa.itertuples() if r.numero_grupo},
           **{r.numero_club: (r.club, "club") for r in mapa.itertuples() if r.numero_club}}
    filas = [dict(numero=n, cierre=c, variable=v, valor=x, documento=d, pagina=p,
                  motivo="revision manual 4/11/2026 (3a pasada): " + m, club=rol.get(n, ("", ""))[0], rol=rol.get(n, ("", ""))[1])
             for n, c, v, x, d, p, m in D]
    cm = pd.concat([cm, pd.DataFrame(filas)], ignore_index=True).drop_duplicates(["numero", "cierre", "variable"], keep="last")
    cm.to_csv(f"{base}/datos_fase2/correcciones_manuales.csv", index=False)
    print(len(D), "decisiones; total correcciones", len(cm))

if __name__ == "__main__":
    main(sys.argv[1])

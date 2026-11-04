"""Segunda pasada de la revision manual (4 nov 2026): cifras clave que seguian sin valor fiable.
PDF: contra la imagen de la pagina (C:\\datos_premier\\revision2\\S00-S11.png).
iXBRL: contra el texto del documento .xhtml (tabla de la cuenta de resultados / balance).
(item de items2.csv, valor en miles de libras, motivo[, variable si es otra])."""
import sys, pandas as pd

D = [
 (26,-35187.0,"Shareholders' deficit"),(25,-5413.0,"nota de impuestos: Loss on ordinary activities before taxation"),
 (70,-18565.0,"nota de impuestos"),(72,35696.064,"'Salaries and wages'"),
 (18,-25323.0,"Closing shareholders' deficit"),(48,24516.0,"Wages and salaries"),
 (0,54694.713,"KPI del informe: Staff costs (sin tabla de personal)","gastos_personal"),(22,-5291.421,"cuenta de resultados"),
 (23,-4291.421,"Shareholders' funds"),(71,-25480.0,"nota de impuestos"),
 (1,53738.939,"KPI del informe: Staff costs","gastos_personal"),(7,-37450.617,"Closing shareholders' deficit"),
 (11,-13309.896,"grupo: Closing shareholders' deficit"),(50,-8357.168,"nota de impuestos"),(8,-52207.606,"Closing shareholders' deficit"),
 (12,11411.242,"grupo: Closing shareholders' funds"),(2,36518.162,"KPI del informe: Staff costs","gastos_personal"),
 (55,20104.668,"Net assets"),
 (75,28351.447,"'Salaries and wages'"),(9,-60714.743,"Closing shareholders' deficit"),(13,12065.086,"grupo: Closing shareholders' funds"),
 (3,27551.318,"KPI del informe: Staff costs","gastos_personal"),(24,102395.970,"cuenta de resultados"),
 (14,1660.531,"grupo: Closing shareholders' funds"),
 (19,-3869.0,"nota de impuestos"),(4,9954.979,"informe estrategico: Turnover"),(5,-14675.089,"nota de impuestos"),
 (35,41990.0,"cuenta de resultados"),(44,128830.0,"cuenta de resultados"),(58,1675.913,"cuenta de resultados consolidada"),
 (60,3613.0,"informe de administradores: profit before taxation £3,613,000"),
 (73,14981.916,"'Salaries and wages'"),
 (10,-127337.682,"Net assets"),(17,9052.899,"Direct + indirect wages and salaries (8,129,047 + 923,852)"),
 (74,17523.131,"'Salaries and wages' (periodo 1/6/18-30/6/19)"),(59,156135.0,"'Salaries and bonuses'"),
 # iXBRL (texto del documento)
 (15,133565.0,"iXBRL: Turnover"),(16,71746.0,"iXBRL: Turnover"),(45,221746.0,"iXBRL: Turnover"),
 (46,-59488.154,"iXBRL: Total equity (59,488,154)"),
 (61,128222.0,"iXBRL: Turnover"),(62,-31615.0,"iXBRL: (Loss) on ordinary activities before taxation"),(63,27867.0,"iXBRL: Total equity"),
]

def main(base, items):
    it = pd.read_csv(items, dtype={"numero": str})
    cm = pd.read_csv(f"{base}/datos_fase2/correcciones_manuales.csv", dtype={"numero": str})
    filas = []
    for t in D:
        item, val, motivo = t[:3]
        r = it[it.item == item].iloc[0]
        var = t[3] if len(t) > 3 else r.variable
        filas.append(dict(numero=r.numero, cierre=r.cierre, variable=var, valor=val, documento=r.documento,
                          pagina=int(r.pagina) if pd.notna(r.pagina) else 0, motivo="revision manual 4/11/2026 (2a pasada): " + motivo,
                          club=r.club, rol=r.rol))
        if var == "activos_netos":
            filas.append({**filas[-1], "variable": "patrimonio"})
    cm = pd.concat([cm, pd.DataFrame(filas)], ignore_index=True).drop_duplicates(["numero", "cierre", "variable"], keep="last")
    cm.to_csv(f"{base}/datos_fase2/correcciones_manuales.csv", index=False)
    print(len(D), "decisiones; total correcciones", len(cm))

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

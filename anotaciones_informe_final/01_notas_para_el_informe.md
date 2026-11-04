# Notas para el informe final: qué hay que mencionar obligatoriamente

Lista viva. Todo lo que no sea "cifra leída tal cual en el estado financiero de la cuenta de ese año" debe declararse en el informe final (sección de datos y metodología). Última actualización: 4 nov 2026.

## 1. Fuentes externas (Deloitte, prensa, webs)
- **No se ha rellenado ninguna cifra del panel con fuentes externas.** Deloitte Football Money League 2023 y 2024, Swiss Ramble, The Guardian, Inside World Football y salarysport.com se usaron **solo para contrastar** 66 cifras (`datos_fase2/auditoria/contraste_externo*.csv`).
- Si alguna vez se rellena una cifra con una fuente externa, se marcará con `fuente = externa` y la referencia exacta. Propuesta: no usarla en el modelo base, solo en un análisis de sensibilidad.
- Hay que explicar que Deloitte y la prensa suelen usar la **matriz del grupo**. Arsenal y Chelsea cuadran ahora exactamente con el grupo (9 de 9 cifras). Deloitte quita a Arsenal la promoción inmobiliaria y los traspasos de la cifra de negocio. Man United sigue en la sociedad del club (su matriz cotiza en EE. UU.: pendiente decidir).

## 2. Cifras del panel que no salen del estado financiero principal del año
Todas están en `datos_fase2/correcciones_manuales.csv`, columna `motivo` (336 filas).

| Origen | Nº | Casos |
|---|---|---|
| KPI del informe estratégico o de administradores (sin tabla en las notas) | 6 | Gasto de personal de Bolton 2011-2014; ingresos de Brentford 2015; resultado antes de impuestos de Watford 2016 |
| Texto del iXBRL leído a mano (no etiqueta XBRL) | 11 | Burnley 2024-25, Forest 2025, Oxford 2025, Watford 2018, Coventry 2023 (sueldos), Rotherham 2024 (ingresos) |
| Texto OCR, sin comprobación visual (las dos pasadas de OCR coinciden o cuadran con la conciliación) | 5 | Patrimonio de Southampton 2014-2015; sueldos de Wigan Holdings 2017 |
| Suma de líneas | 1 | Burton 2018: sueldos = directos + indirectos |
| Nota de impuestos (parte de la cuenta, pero no del estado de resultados) | 6 | Everton 2011, West Ham 2011-12, Southampton 2012, Charlton 2015, Brentford 2015 |
| Ceros de holdings sin actividad o sin consolidar (la cuenta muestra "-" o "no employees") | 17 | Middlesbrough Holdings 2012, 2016, 2024 y 2025; West Brom Group 2013-2014; Coventry 2012 (sueldos) |
| Comparativo de la cuenta del año siguiente (`estado = desde_año_siguiente`) | ~3.000 filas (todas las partidas) | Los que vienen de una cuenta que avisa de reexpresión se marcan como sospechosos y quedan fuera del panel fiable |
| Derivada por identidad, activos netos = patrimonio (`derivada_identidad`) | ~330 filas | |
| Revisión manual contra el PDF, el iXBRL o el texto OCR | 269 decisiones en 3 pasadas (336 filas) | Unas 110 confirmadas; el resto corregidas o completadas |
| Revisión manual de los grupos de Arsenal y Chelsea (4ª pasada) | 188 | Todas las cifras clave de 04250459 y 02536231 entre 2010 y 2025 |

## 3. Decisiones de método que hay que declarar
- **Original frente a reexpresada:** el panel guarda la cifra original publicada. Una reexpresión solo se acepta si la cuenta siguiente lo dice ("restated"); si no, la cifra queda en conflicto. Ejemplo: el resultado de Everton 2022 se guarda como −44.732, aunque la cuenta de 2023 lo reexpresa a −38.413.
- **"Sin evidencia no se corrige":** las cifras dudosas quedan fuera del panel fiable; no se adivinan.
- **Entidad:** se recogen la sociedad del club y, si existe en el mapa, la del grupo.
  - Arsenal y Chelsea: grupo añadido el 4-11-2026, Arsenal Holdings Ltd (04250459) y Chelsea FC Holdings Ltd (02536231). En Chelsea, tras 2022 la cabecera última es Blueco 22 (solo cuentas desde 2023); se usa Chelsea FC Holdings por continuidad.
  - **Hay que declarar** que los resultados de Chelsea incluyen ventas a sociedades hermanas, confirmadas en las cuentas: hoteles (+76,5 M£, 2022/23) y equipo femenino (+198,7 M£, 2023/24). Son no recurrentes e intragrupo, y en el consolidado de Blueco 22 no existirían. Propuesta: marcarlas y hacer un análisis de sensibilidad sin ellas.
  - **Todas las cifras clave de los dos grupos** (188) son de revisión manual (`decisiones_revision4.py`): el extractor no maneja las columnas de grupo y de sociedad.
  - **Middlesbrough Holdings** (todos los años revisados) y **West Brom Group** (2013-2014) son holdings que **no consolidan al club**: sus cifras de "grupo" son cero o casi cero y no representan al club. En la fase 3 hay que usar la sociedad del club en esos casos.
- **Gastos de personal en positivo** aunque la cuenta los imprima entre paréntesis.
- **Huecos estructurales:**
  - cuentas **nunca depositadas**: 10 club-temporadas (`indicadores_club_temporada.csv`, `estado_cuenta = no_depositada`), que además son una señal de riesgo;
  - cuentas **abreviadas** sin cuenta de resultados: 19.
  - Se tratarán con indicadores en el modelo, no se rellenan.
- **Sociedades inactivas** (*dormant*, p. ej. Middlesbrough Holdings 2019-2020): sin cifras.
- **Cambios de fecha de cierre:** hay ejercicios de 6, 7, 10, 11, 13, 14 y 18 meses (columna `meses_ejercicio`). Las cifras de flujo de esos años no son anuales. Hay dos temporadas con dos cierres (Plymouth 2018/19 y Rotherham 2014/15); el principal es el último (`cierre_principal_temporada`).
- **Corrección declarada:** el panel generaba club-temporadas duplicadas con los cambios de fecha de cierre; se corrigió el 4 nov 2026 (ver el diario).

## 4. Calidad medida (para la tabla de validación del informe)
- **Cinco muestras de validación** revisadas cifra a cifra contra el PDF. Solo la **validación 5** es prueba ciega del panel final: **100 % de precisión (175/175)**, y la exhaustividad pasa del 99,4 % al 100 % tras la tercera pasada de revisión. Esa tercera pasada no se ajustó mirando la muestra; se completaron las cifras pendientes de todo el estudio.
- **Historial completo, también las pruebas no superadas** (validaciones 3 y 4): hay que contarlo con honestidad.
- **Correcciones posteriores a la medición que hay que declarar:**
  - una referencia corregida después de medir (Birmingham 2012, dos líneas con la misma etiqueta);
  - el script de medición corregido (busca por sociedad y cierre, no por documento).
- **Cifras clave sin valor fiable:** 36 de 3.332, todas estructurales (17 no depositadas y 19 abreviadas). Listado en `datos_fase2/auditoria/revision_manual/pendientes_tras_revision.csv`.
- **Partidas secundarias** (impuesto, acreedores, caja, provisiones): pendiente de validar con el mismo protocolo; hay que decir cuáles se usan y cómo se validaron.

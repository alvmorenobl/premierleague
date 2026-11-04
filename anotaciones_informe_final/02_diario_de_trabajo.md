# Diario de trabajo (para el informe final)

Registro cronológico de los pasos, hallazgos y decisiones. Los detalles técnicos están en `datos_fase2/auditoria/AUDITORIA_FASE2.md`.

## Hasta el 4 nov 2026: fases 0-2
- **Fase 0 (viabilidad):** el OCR acertó 14 de 14 cifras comprobadas en las cuentas 2024/25 de Liverpool, Everton y Brentford.
- **Fase 1:** 748 club-temporadas, 62 clubes y 84 sociedades. Se resolvieron los cambios de nombre tras una administración ("… Realisations Ltd") con el registro de control (PSC) y a través de los antiguos directivos.
- **Fase 2:**
  - Inventario de 1.259 cuentas; 63 depositadas claramente fuera de plazo.
  - OCR de unas 1.120 cuentas en PDF (31.848 páginas) y lectura de 143 en iXBRL.
  - Auditoría y cinco validaciones:
    - validación 3: no superada (98,1 % / 92,1 %);
    - validación 4: no superada (98,7 % / 89,7 %);
    - validación 5: superada (100 % / 99,4 %).
  - Revisión manual de 227 cifras clave y contraste con 66 cifras publicadas.

## 4 nov 2026: paso 1 tras el cierre, las 34 cifras que no se habían fijado
- **Método:** página completa del PDF a 100 ppp (`C:\datos_premier\revision3`), texto del iXBRL o texto OCR cuando las dos pasadas coinciden. Decisiones en `datos_fase2/auditoria/revision_manual/decisiones_revision3.py`.
- **Everton 2022-2025** (cuenta de resultados con celdas sombreadas, que el OCR no leía):

  | Año | Ingresos | Resultado antes de impuestos |
  |---|---|---|
  | 2022 | 181.007 | −44.732 |
  | 2023 | 172.155 | −89.090 |
  | 2024 | 186.902 | −53.222 |
  | 2025 | 196.697 | −8.609 |

  Las cifras de 2022 (Deloitte, 181,0 M£) y de 2025 (salarysport, 196,7 M£ y −8,6 M£) coinciden con las fuentes externas.
- **Hallazgo:** Middlesbrough Holdings (2012, 2016, 2024 y 2025) y West Brom Group (2013-2014) son holdings sin consolidar o sin actividad: cifras cero. Implicación para la fase 3: en esos años hay que usar la sociedad del club.
- **Otras cifras completadas:**
  - Swansea Holdings 2014: ingresos 98.692 y resultado 1.326;
  - Brentford 2015: balance consolidado, −5.663;
  - Southampton 2012-2015: patrimonio −33.341, −12.654, 18.319 y 30.471;
  - Preston Holdings 2025: balance consolidado, 30.676 (el de la sociedad es 54.406);
  - Wigan Holdings 2017: sueldos 16.410;
  - Coventry 2012: sin empleados; Coventry 2023: sueldos 16.633;
  - Rotherham 2024: ingresos 19.173.
- **Resultado:**
  - cifras clave sin valor fiable: de 70 a **36**, todas estructurales;
  - validación 5: 100 % / 100 %;
  - las validaciones anteriores no empeoran.

## 4 nov 2026: corrección de club-temporadas duplicadas (fallo encontrado al preparar los indicadores)
- **Problema:** unas 57 club-temporadas aparecían dos veces. Cuando un club cambia su fecha de cierre (ejercicios de 6, 7, 13 o 18 meses), el panel creaba un año "fantasma" con el comparativo de la cuenta siguiente, en una fecha de cierre que no existe (por ejemplo, Crystal Palace 2019-07-31 al lado del real 2019-06-30). En la fase 3 eso habría contado temporadas dos veces.
- **Arreglo** (`fase2_panel.py`): el comparativo de la cuenta *t+1* se asigna a la cuenta anterior que sí existe si está entre 150 y 560 días antes. Solo si no hay ninguna se crea el cierre *t−1 año*. El panel pasa de 1.348 a 1.293 filas.
- **Quedan dos casos reales** de dos cierres en la misma temporada (Plymouth 2018/19 y Rotherham 2014/15, por un cambio de diciembre a junio). Se marca `cierre_principal_temporada` (el último) y `meses_ejercicio`. **Ojo en la fase 3:** el cierre principal de esos dos casos es un ejercicio de 6 meses; los flujos (ingresos, resultado) hay que anualizarlos o usar el de 12 meses.
- **Las validaciones no cambian:** 100 % / 98,2 % (val-2), 99,4 % / 98,8 % (val-3), 100 % / 97,1 % (val-4) y 100 % / 100 % (val-5).

## 4 nov 2026: paso 2, indicadores de cuenta
- **`panel_financiero.csv`** tiene columnas nuevas:
  - `cuenta_depositada` (False si la fila solo existe por el comparativo de la cuenta siguiente);
  - `tipo_cuenta`;
  - `cuenta_abreviada` (small, total-exemption, micro, abridged);
  - `cuenta_inactiva` (dormant);
  - `holding_sin_consolidar` (Middlesbrough Holdings todos los años; West Brom Group 2013-2014);
  - `depositada` (fecha), `dias_fuera_plazo` y `fuera_plazo_claro`.
- **`fase2_indicadores.py`** genera `datos_fase2/indicadores_club_temporada.csv`. Clasifica cada una de las 748 club-temporadas del estudio en:
  - **depositada:** 650;
  - **no depositada** con el plazo legal vencido: **10**;
  - **aún no vencida:** 88 (temporadas 2025/26 y 2026/27).
- **Corrección de una cifra anterior:** las cuentas nunca depositadas son **10**, no 9. Faltaba Bolton 2018/19: la sociedad BWFC 2019 Ltd depositó su última cuenta en 2016/17 y entró en administración en mayo de 2019. Lista completa:
  - Portsmouth 2010/11 y 2011/12;
  - Bolton 2017/18 y 2018/19;
  - Derby 2018/19, 2019/20, 2020/21 y 2021/22;
  - Wigan 2019/20;
  - Sheffield Wednesday 2024/25.
- **Uso previsto en la fase 3:** la cuenta no depositada y el retraso en el depósito son variables explicativas (señales de crisis). Las cuentas abreviadas no tienen cuenta de resultados, así que sus ingresos y su resultado quedan vacíos de forma estructural.

## 4 nov 2026: paso 3, matrices de Arsenal y Chelsea (en curso)
- El mapa de sociedades solo tenía la sociedad del club de Arsenal (00109244) y de Chelsea (01965149). Deloitte y la prensa usan las cuentas consolidadas del grupo, y de ahí las diferencias del 4-10 % del contraste externo.
- `fase2_matrices.py` busca las matrices por nombre y sube por la cadena de control (PSC). Hay que ejecutarlo en el ordenador del usuario, porque la API de Companies House no es accesible desde el entorno de Claude. La salida (`datos_fase1/matrices_candidatas.csv`) se revisará antes de tocar el mapa.

## 4 nov 2026: paso 4, diagnóstico de las partidas secundarias (antes de validarlas)
Base: 789 club-temporadas del estudio con cierre principal, sin holdings que no consolidan.

| Partida | Cobertura |
|---|---|
| Caja | 96,5 % |
| Deudores | 96,7 % |
| Intangibles (jugadores) | 95,6 % |
| Inmovilizado material | 94,6 % |
| Impuesto | 94,4 % |
| Activo circulante neto | 93,3 % |
| Total activos menos pasivo corriente | 89,2 % |
| Beneficio por traspasos | 87,6 % |
| Resultado neto | 87,1 % |
| Intereses pagados | 81,4 % |
| Acreedores a corto plazo | 79,5 % |
| Acreedores a largo plazo | 68,3 % |
| Provisiones | 45,4 % |
| Amortización de jugadores | 17,5 % |

**Identidades:**
- Activo menos pasivo corriente + acreedores a largo + provisiones = activos netos: cuadra solo en el **44,9 %** (de 704). Faltan partidas en la ecuación (periodificaciones e ingresos diferidos, pensiones, impuesto diferido), y "acreedores a largo" vacío no siempre significa cero.
- Resultado antes de impuestos + impuesto = resultado neto: cuadra en el **84,5 %** (de 663). El fallo suele ser el impuesto, que recoge el número de nota.

**Conclusión:** las partidas secundarias **no son fiables todavía**. Hay que validarlas con el mismo protocolo que las clave antes de usarlas en la fase 3. Prioridad: acreedores, caja y deuda por traspasos, por el riesgo y el contagio. Las deudas por traspasos ni siquiera se extraen aún: están en la nota de acreedores.

## 4 nov 2026: paso 3, matrices de Arsenal y Chelsea
`fase2_matrices.py` (ejecutado por el usuario, salida en `datos_fase1/matrices_candidatas.csv`) recorre la cadena de control (PSC) desde la sociedad del club y busca por nombre.

**Arsenal:** club 00109244 → Arsenal (AFC Holdings) Ltd 05659803 (19 cuentas, ninguna de grupo: no consolida) → **Arsenal Holdings Ltd 04250459** (24 cuentas, 23 de grupo, 2002-2025) → E. S. Kroenke. **Se elige 04250459** como grupo: es la cabecera consolidada de todo el periodo y la que usan las fuentes externas (Deloitte, etc.).

**Chelsea:** club 01965149 → **Chelsea FC Holdings Ltd 02536231** (35 cuentas, 31 de grupo, 1991-2025). Por encima: Fordstam Ltd 04784127 (Abramovich, controlador hasta el 30-5-2022, cuentas de grupo hasta 2024) y, desde 2022, Blueco 22 Midco → Blueco 22 Ltd 13949552 → 22 Holdco 14075518 (solo cuentas 2023-2025). **Se elige 02536231**: es la única consolidada continua a través del cambio de propiedad y da una serie homogénea. Fordstam y Blueco 22 se descartan como grupo (ninguna cubre el periodo entero).

**Para el informe:**
- Explica la diferencia del 4-10 % de Arsenal y Chelsea en el contraste externo: el panel tenía la sociedad del club; las fuentes usan el grupo. Tras añadir el grupo, repetir el contraste.
- Chelsea FC Holdings no es la cabecera última tras 2022 (lo es Blueco 22). Las operaciones con sociedades hermanas del grupo Blueco (según la prensa, la venta de los hoteles y del equipo femenino a sociedades del mismo propietario) generan resultados dentro de Chelsea FC Holdings que no existirían en el consolidado de Blueco 22. **Por comprobar en las cuentas** cuando se extraigan; si se confirma, marcarlo como partida no recurrente/intragrupo.
- `mapa_sociedades.csv`: añadidos `numero_grupo` 04250459 (Arsenal) y 02536231 (Chelsea).

Siguiente: inventario, descarga, OCR/iXBRL y extracción de esas dos sociedades (el usuario lo ejecuta; los scripts son reanudables y solo procesan lo nuevo).

## 4 nov 2026: paso 3 completado, cifras de los grupos Arsenal y Chelsea
- El usuario ejecutó el inventario, la descarga y el OCR: 34 cuentas de grupo, 1.456 páginas, 12 minutos.
- El extractor automático confunde estas cuentas: columnas de grupo y de sociedad, cuenta de resultados en tres columnas por año, y unidades en libras en un año de Arsenal. Por eso **las 188 cifras clave de los dos grupos se fijaron a mano** (`decisiones_revision4.py`): ingresos, gasto de personal, sueldos, resultado antes de impuestos, activos netos y patrimonio, de 2010 a 2025.
- **Comprobaciones:**
  - 172 de las 188 aparecen en la cuenta del año siguiente;
  - las 5 que no aparecen son reexpresiones declaradas (FRS 102 en 2015 y sueldos de Arsenal 2018), y se guarda la original;
  - 11 son de 2025, sin cuenta siguiente: se comprobaron en imagen o por suma de la nota.
- **Contraste externo:** las 9 cifras de Arsenal y Chelsea cuadran con el grupo. Deloitte quita a Arsenal la promoción inmobiliaria y los traspasos de la cifra de negocio, y la cuenta sale exacta.
- **Confirmado en las cuentas de Chelsea:** venta de los hoteles a Blueco 22 Properties (+76,5 M£ en 2022/23) y del equipo femenino a Blueco 22 Midco (+198,7 M£ en 2023/24). Sin el equipo femenino, el resultado de 2023/24 (+128,4 M£) habría sido de unos −70 M£.
- **Incidencia:** `fase2_extraer_ixbrl.py` ejecutado en Windows no reproduce 34 filas de 5 sociedades. Se restauró el archivo validado y queda pendiente investigar la causa.
- **Siguiente:** paso 4, validar las partidas secundarias.

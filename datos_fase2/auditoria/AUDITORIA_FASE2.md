# Auditoría y validación de la fase 2 (actualizado el 4 nov 2026) — FASE 2 CERRADA

## 1. Auditoría inicial: qué estaba mal
- **Fase 1 (clubes y temporadas):** correcta. Hay 6 descensos causados por sanciones: Portsmouth 11/12, Wigan 19/20, Sheffield Wednesday 20/21, Derby 21/22, Reading 22/23 y Leicester 25/26.
- **Cobertura:** 650 de 660 club-temporadas vencidas tienen cuenta. Los 10 huecos son cuentas **nunca depositadas** por clubes en crisis, y se tratan como señal del modelo. (Corregido el 4 nov 2026: antes ponía 651 y 9; faltaba Bolton 2018/19.)
- **Errores encontrados y corregidos:**
  - 5 cuentas de Tottenham de los años 1920 colocadas en 2020-26; se excluyen por fecha imposible.
  - Aston Villa Ltd no consolida al club; se retira como grupo.
- **Extracción v1** (30 documentos revisados a mano): 95,5 % de precisión y 79 % de exhaustividad. Causas:
  1. títulos FRS 102/NIIF no reconocidos;
  2. espacio leído como separador de miles;
  3. ejercicios de una sola columna;
  4. fechas leídas como cifras;
  5. unidades decididas página a página;
  6. elección de página por número de coincidencias;
  7. tope de 18 páginas por documento.

## 2. Arreglos aplicados
- **Localizador v2** (`fase2_reglas.py`): títulos UK GAAP, FRS 102 y NIIF, preferencia por el consolidado y erratas frecuentes del OCR.
- **OCR complementario:** 2.381 páginas nuevas.
- **Lector v2** (`fase2_extraer_cifras.py`):
  - separadores de miles y cifras partidas;
  - formatos de 1, 2, 3, 4 y 6 columnas;
  - una sola unidad por documento;
  - etiquetas partidas entre líneas;
  - "net liabilities" impreso sin paréntesis;
  - la página siguiente se usa solo si es continuación del mismo estado.
- **iXBRL:**
  - se acepta la dimensión "Original";
  - se lee el texto cuando la cifra no está etiquetada, con la unidad calibrada con las cifras que sí lo están;
  - las iXBRL con ingresos pasan de 56 a 102 de 143.
- **Panel** (`fase2_panel.py`):
  - contraste entre años con clasificación del error: unidades, signo, dígito, truncado o columna equivocada;
  - una reexpresión real se conserva con sus dos valores;
  - sin un patrón de error claro no se corrige nada: la cifra queda en conflicto y fuera del panel fiable;
  - identidades contables;
  - plausibilidad;
  - correcciones manuales documentadas.

## 3. Validación (verificación visual contra el PDF original)
| Muestra | Uso | Extractor (precisión / exhaustividad) | Panel fiable (precisión / exhaustividad) |
|---|---|---|---|
| Desarrollo, 30 docs | ajuste de reglas | 82/83 correctas | – |
| Validación 1, 60 docs (semilla 2026) | ajuste de reglas tras medirla | 95,3 % / 91,7 % antes → 99,6 % / 97,4 % después | – |
| **Validación 2, 40 docs nuevos (semilla 7)** | **medida sin ajustar el extractor** | **95,3 % / 94,7 %** | 99,4 % / 94,2 % (*) |

(*) Las reglas del panel se retocaron después de ver la validación 2, así que esta cifra del panel es optimista.

**Criterios de aceptación** (precisión ≥ 99 %, exhaustividad ≥ 97 %): **todavía NO cumplidos de forma independiente.**

Errores pendientes del extractor, vistos en la validación 2:
- columna del año anterior en formatos con separador "|" o de 6 columnas (2);
- cifra partida por el OCR (1);
- dígito mal leído (2);
- etiqueta continuada en la línea siguiente (1);
- primer ejercicio con la cifra en otra línea (1).

## 4. Validación 3: prueba de aceptación (4 nov 2026) — NO SUPERADA

Antes de medirla se corrigieron los errores de la validación 2 (que pasó a 98,2 % / 98,2 % en el extractor y 100 % / 97,1 % en el panel, ya contaminada).
Después se tomó una muestra nueva de 40 cuentas (semilla 11), excluyendo las tres muestras anteriores. Se revisaron cifra a cifra contra la imagen del PDF y se midió una sola vez, sin tocar reglas.

| | Precisión | Exhaustividad | Criterio |
|---|---|---|---|
| Extractor | 94,8 % (146/154) | 88,0 % (146/166) | ≥ 99 % / ≥ 97 % |
| **Panel fiable** | **98,1 % (152/155)** | **92,1 % (152/165)** | ≥ 99 % / ≥ 97 % |

**Conclusión: la fase 2 no se da por cerrada.** El panel no puede usarse todavía para los modelos de la fase 3.

Corrección de medición (no de reglas): el script buscaba el valor del panel por documento, y las filas rellenadas desde la cuenta del año siguiente llevan el documento de ese año. Eso mezclaba ejercicios. Ahora se busca por (sociedad, cierre, variable). La validación 2 da el mismo resultado con la búsqueda corregida.

Errores que llegan al panel fiable (3):
1. **Preston 2012, patrimonio.** El panel cambió el −1.216 correcto por −4.216, el comparativo del año siguiente, que el OCR había leído mal. La regla de dígito elige el valor del año siguiente sin ninguna prueba de cuál de los dos está bien.
2. **Nottingham Forest (01630402) 2012, patrimonio.** Se tomó −14.362 de una tabla del informe de administradores en vez del −79.667 del balance consolidado. El panel no lo detectó: activos netos (−79.667) y patrimonio (−14.362) no cuadran, pero la identidad no se comprobó porque los dos valores venían de documentos distintos.
3. **Swansea 2018, sueldos.** Se rellenó con el comparativo reexpresado del año siguiente (79.775 frente a los 79.539 originales, un 0,3 % de diferencia). No es un error de lectura, sino de criterio: hay que decidir y documentar si el panel guarda la cifra original o la reexpresada.

Errores del extractor que el panel retuvo como conflicto (no llegan al panel fiable, pero dejan huecos):
- formato de 4 columnas (sin traspasos / traspasos / total / año anterior), resultado antes de impuestos tomado de la columna equivocada o leído como 0 (Leeds 2012, Southampton 2024);
- "Net assets ." leído como 0,010 (Sheffield United 2024);
- sueldos = 0 con líneas "normales" y "excepcionales" (Norwich 2011).

Corregidos por el panel: un primer dígito perdido (5.783) y un signo con espacio tras el paréntesis (Blackburn 2021). También dos líneas "Net liabilities" antes y después de pensiones, resueltas por la identidad.

Faltas principales (exhaustividad): sueldos no extraídos en 7 cuentas (la mayoría los recupera el panel desde el año siguiente), "Staff costs" solo en la cuenta de resultados, turnover "–" en el primer ejercicio, Preston 2025 con balance de grupo y de sociedad sin extraer, y el resultado antes de impuestos de Swansea 2018.

Otro problema detectado, fuera de las 6 partidas medidas: la variable `impuesto` recoge a menudo el número de nota (valores como 5, 8, 11 o 0,011). Hay que corregirla o excluirla antes de usarla.

## 5. Arreglos tras la validación 3 y validación 4 (4 nov 2026) — NO SUPERADA

**Arreglos aplicados** (los dos scripts, `fase2_extraer_cifras.py` y `fase2_panel.py`):
- **Panel:**
  - un desacuerdo de dígito con el año siguiente ya no se decide por cercanía a los años vecinos: solo lo resuelve la identidad activos netos = patrimonio, y si no, queda en conflicto;
  - la identidad se comprueba sobre los valores finales, aunque vengan de documentos distintos;
  - los gastos de personal se guardan en positivo.
- **Extractor:**
  - sueldos con erratas de OCR ("salanes", "andsalaries", letra suelta delante);
  - se sigue buscando la tabla de personal hasta encontrar los sueldos y, si no, se busca en todo el documento la de mayor importe que sea plausible frente a los ingresos;
  - líneas "normales/excepcionales";
  - cifras partidas "10, 886,881";
  - guiones sueltos en formatos de 4 columnas;
  - prioridad a la página que lleva el título del estado;
  - número de nota en cuentas en libras.
- **Control de regresiones:** el desarrollo queda en 82/83 y la validación 1 en 99,6 % / 97,4 %, igual que antes. La validación 2 queda en 98,8 % / 98,8 % (extractor) y 100 % / 96,5 % (panel). Ese 96,5 % pierde una cifra a propósito: una reexpresión grande pasa a conflicto.
- **Comparación de datos:** frente a la versión anterior, de las 6 partidas medidas cambian 13 cifras, y todas pasan de una cifra sin sentido a la real.

**Validación 4:** muestra nueva de 40 cuentas (semilla 23), que excluye las cuatro anteriores. Se midió una sola vez.

| | Precisión | Exhaustividad |
|---|---|---|
| Extractor (código anterior → nuevo) | 96,2 % → 95,7 % | 85,3 % → 88,7 % |
| **Panel fiable (anterior → nuevo)** | **96,9 % → 98,7 %** | **88,6 % → 89,7 %** |

Errores que llegan al panel fiable (2). Los dos tienen la misma causa: la regla de **reexpresión** da por buena la cifra leída cuando difiere menos de un 15 % del comparativo del año siguiente.
1. **Watford 2010, ingresos.** Se leyó "continuing operations" (10.356) en vez del total con adquisiciones (11.258), y el comparativo de 2011 decía 11.258.
2. **QPR 2015, ingresos.** Se leyó la columna del año anterior (97.557), y el comparativo de 2016 decía 112.072.

Una diferencia pequeña entre años **no prueba** una reexpresión: también la produce una lectura equivocada. Esta regla hay que endurecerla.

Huecos principales (exhaustividad):
- cifras correctas retenidas en conflicto por las reglas nuevas (Ipswich 2010, Crystal Palace 2011 y 2015);
- patrimonio sin leer con etiquetas "Net deficit", "Total equity" (NIIF) y "Shareholders' funds" con número de nota;
- cuenta de resultados de Everton 2023 sin localizar;
- tabla de sueldos sin OCR fino en 3 cuentas.

Errores del extractor que el panel retuvo: dígitos mal leídos por el OCR ("{2,706,503", "34,414"), "opening shareholders' deficit" y el año leído como cifra.

**Conclusión:** cada validación nueva encuentra tipos de error nuevos, cada vez menos frecuentes. La precisión del panel se acerca al 99 %, pero la exhaustividad (~90 %) está lejos del 97 %. Con reglas automáticas por sí solas no se llega a los criterios en un plazo razonable.

## 6. Cierre de la fase 2 (4 nov 2026)

### 6.1 Reglas más estrictas en el panel y en el extractor
- **Reexpresión solo con evidencia:** una diferencia menor del 15 % con el comparativo del año siguiente solo se acepta como reexpresión si la cuenta siguiente dice "restated", "re-presented" o "reclassified". Si no lo dice, queda en conflicto. Así se corrigen Watford 2010 y QPR 2015.
- **Huecos rellenados con comparativos reexpresados:** se marcan como sospechosos, porque no son la cifra original publicada.
- **Activos netos = patrimonio neto:** si falta una de las dos, se deriva de la otra cuando esta es fiable (estado `derivada_identidad`).
- **Extractor:**
  - se descarta el "opening shareholders' deficit";
  - una línea cuyas únicas cifras son años no tiene importes;
  - se acepta el balance NIIF que solo muestra "Total equity";
  - cada cifra lleva una marca `reexpresado` si su página avisa de una reexpresión.

### 6.2 Revisión manual dirigida
Objetivo: las cifras clave (ingresos, resultado antes de impuestos, activos netos/patrimonio, sueldos o gasto de personal) de **todas las club-temporadas del estudio** que seguían en conflicto o vacías. Cada una se comprobó contra la imagen de la página del PDF, o contra el texto del iXBRL.

- **Primera pasada:** 184 cifras. Hojas `C:\datos_premier\revision\R00-R28.png`; decisiones en `revision_manual/decisiones_revision1.py`.
- **Segunda pasada:** 43 cifras. La página se buscó en todo el documento (`S00-S11.png`) y se usó el iXBRL para 7 cuentas; decisiones en `revision_manual/decisiones_revision2.py`.
- **Resultado:** 294 filas en `datos_fase2/correcciones_manuales.csv`, cada una con documento, página y motivo. En unas 110 se confirmó la lectura; en el resto se corrigió o se completó.
- **Tipos de error encontrados en la revisión:**
  - dígitos mal leídos por el OCR ("448,403" por 148,403; "719,326" por 79,326…);
  - formato de 6 columnas leído en la columna del año anterior (West Ham, Tottenham, Watford, Southampton);
  - etiquetas no reconocidas ("Salaries and wages", "Wage and salaries", "Net deficit");
  - celdas sombreadas (Everton);
  - cifras solo en el informe estratégico (KPI de Bolton).

**Qué queda sin valor fiable:** 70 de 3.332 cifras clave (`revision_manual/pendientes_tras_revision.csv`).
- 17 son cuentas nunca depositadas, que son una señal de riesgo en sí mismas.
- 19 son cuentas abreviadas, que no publican cuenta de resultados.
- 34 no se pudieron fijar con seguridad; quedan vacías, sin adivinar:
  - Everton 2022-2025: cuenta de resultados en celdas sombreadas o solo en millones;
  - Middlesbrough Holdings;
  - Southampton: balance de la sociedad;
  - West Brom Holdings 2013-14;
  - otras sueltas.

### 6.3 Validación 5: prueba de aceptación del panel final — SUPERADA
Muestra nueva de 40 cuentas (semilla 31) de club-temporadas del estudio, que excluye las cinco muestras anteriores. Se midió una sola vez.

| | Precisión | Exhaustividad | Criterio |
|---|---|---|---|
| Extractor automático | 99,4 % (168/169) | 92,3 % (168/182) | – |
| **Panel fiable final** | **100 % (175/175)** | **99,4 % (175/176)** | ≥ 99 % / ≥ 97 % ✔ |

Corrección de la referencia, no del sistema: en Birmingham 2012 se había anotado mal la verdad del resultado antes de impuestos. La cuenta imprime dos líneas con la misma etiqueta: 15.713.587 antes del impuesto y 15.712.560 después. El extractor tenía la cifra correcta. Se comprobó en la página completa (`w01.png`).

Las validaciones anteriores con el panel final (ya contaminadas, solo como control):

| Validación | Precisión | Exhaustividad |
|---|---|---|
| Validación 2 | 100 % | 98,2 % |
| Validación 3 | 99,4 % | 97,6 % |
| Validación 4 | 100 % | 95,4 % |

### 6.4 Contraste externo (≥ 30 club-años) — SUPERADO
`contraste_externo.csv` recoge 66 cifras publicadas de ingresos y de resultado antes de impuestos. Las fuentes son la Deloitte Football Money League 2023 y 2024, los hilos de Swiss Ramble, The Guardian e Inside World Football, y salarysport.com. Los resultados están en `contraste_externo_resultado.csv`.

- El panel tiene valor para **63 de las 66**.
- **46 coinciden con una diferencia menor del 2,5 %**; la mayoría con diferencia 0 o de redondeo.
- **Diferencias sistemáticas del 4-10 % en Arsenal, Chelsea y Man United.** El panel recoge la sociedad del club; Deloitte y la prensa usan la matriz del grupo (Arsenal Holdings, Chelsea FC Holdings, Manchester United plc). Es un tema de entidad, no un error de lectura; se comprobó Arsenal 2025 en el texto de la cuenta. **Para la fase 3 conviene añadir esas matrices al mapa de sociedades.**
- **Brighton 2023/24:** la web externa dice 3,9 M£ de resultado. El panel tiene 75,1 M£, que es la cifra que la propia cuenta de 2025 publica como comparativo de 2024. Se da por error de la fuente externa.
- **Everton 2021/22 y 2024/25:** sin valor en el panel (es una de las 34 pendientes).
- **Ningún error de unidades ni de año.**

### 6.5 Criterios de aceptación: estado final
| Criterio | Estado |
|---|---|
| Precisión ≥ 99 % en una muestra ciega | ✔ 100 % (validación 5) |
| Exhaustividad ≥ 97 % | ✔ 99,4 % |
| 0 errores de unidades | ✔ (validaciones 3-5 y contraste externo) |
| Identidades contables | ✔ (activos netos = patrimonio, aplicada sobre los valores finales) |
| Contraste entre años ≥ 98 % | ✔ (las cifras sin contraste o en conflicto quedan fuera del panel fiable o se revisaron a mano) |
| Contraste externo ≥ 30 club-años | ✔ 63 comparaciones; sin errores de lectura |
| Trazabilidad | ✔ (cada cifra con documento y página; cada corrección manual con motivo) |

**La fase 2 queda cerrada.** Limitaciones que hay que tener en cuenta en la fase 3:
1. Las 70 cifras clave sin valor fiable de la sección 6.2.
2. Arsenal y Chelsea están sin matriz de grupo.
3. La variable `impuesto` y las partidas secundarias (acreedores, caja, provisiones) no se validaron con el mismo rigor. Antes de usarlas en un modelo hay que validarlas o limitarse a las cifras clave.
4. El panel fiable excluye las cifras en conflicto; el modelo debe tratar esos huecos explícitamente.

## 6 bis. Añadido tras el cierre: grupos de Arsenal y Chelsea (4 nov 2026)
- **Sociedades añadidas al mapa** (`fase2_matrices.py`, cadena de control PSC): Arsenal Holdings Ltd (04250459) y Chelsea FC Holdings Ltd (02536231, antes Chelsea FC plc). 34 cuentas de grupo de 2009 a 2025, OCR nuevo.
- **El extractor automático no sirve para estas cuentas.** Tienen columnas de grupo y de sociedad, y la cuenta de resultados lleva "sin traspasos / traspasos / total"; además hay un año (Arsenal 2015 y 2016) leído en libras en lugar de miles. Por eso las **cifras clave de los 32 club-años (2010-2025) se fijaron todas a mano**: 188 decisiones en `revision_manual/decisiones_revision4.py`. Fuentes: texto OCR de las dos pasadas, el resumen de 5 años de la propia cuenta (Arsenal) y la imagen de la página cuando el OCR no era claro (Arsenal 2015, 2022, 2024 y 2025; Chelsea 2010, 2013, 2016, 2017, 2023 y 2025).
- **Contraste interno** (`revision_manual/contraste_t1_grupos_arsenal_chelsea.csv`): cada cifra se busca en la cuenta del año siguiente. Resultado: 172 aparecen, 11 son de 2025 (no hay cuenta siguiente) y 5 no aparecen. Las 5 son reexpresiones declaradas: la adopción de FRS 102 en 2016 (Arsenal 2015: RAI, personal y sueldos; Chelsea 2015: RAI) y una pequeña reexpresión de los sueldos de Arsenal 2018 (210.141 pasa a 209.165). Se guarda la cifra original.
- **Contraste externo, repetido:** las 9 cifras externas de Arsenal y Chelsea cuadran ahora con el grupo. Chelsea 2018/19, 2021/22, 2022/23 y 2024/25, y Arsenal 2024/25, coinciden al redondeo. En Arsenal 2021/22 y 2022/23, Deloitte (367,1 y 463,1) es la cifra de negocio del grupo sin promoción inmobiliaria ni traspasos: 371.907 − 2.830 − 1.978 = 367.099, y 466.685 − 2.128 − 1.457 = 463.100. Las diferencias del 4-10 % de la sección 6 se explicaban, por tanto, por usar la sociedad del club y no el grupo.
- **Partidas intragrupo de Chelsea** que hay que tratar como no recurrentes (vistas en las cuentas): beneficio de 76.524 por vender los hoteles a Blueco 22 Properties (2022/23) y de 198.749 por vender el equipo femenino a Blueco 22 Midco (2023/24). En 2024/25 la línea del resultado antes de impuestos aparece rotulada por error como "after taxation".
- **El resto del panel no cambia:** comparado con la versión anterior, solo dos filas ya duplicadas de 06550400 2013-12-31 cambian de orden.
- **Reproducibilidad, pendiente:** al volver a ejecutar `fase2_extraer_ixbrl.py` en Windows salen 34 filas distintas en 5 sociedades (00053703, 00104194, 00315421, 01630402 y 07698872), con otra etiqueta elegida para la misma partida. Se restauró el archivo validado (`cifras_ixbrl_largo.csv` del commit anterior). Hay que averiguar la causa (¿versión de BeautifulSoup o lxml?) antes de la fase 3.

## 7. Archivos de esta carpeta (`datos_fase2/auditoria/`)
| Archivo | Contenido |
|---|---|
| `muestra_documentos.csv` | Las 30 cuentas de la auditoría inicial (muestra de desarrollo) |
| `muestra_referencia_resultados.csv` | Cifras verdaderas de esas 30 cuentas, revisadas a mano |
| `muestra_validacion_docs.csv` / `validacion_referencia.csv` | Validación 1: 60 cuentas y sus cifras verdaderas |
| `muestra_validacion2_docs.csv` / `validacion2_referencia.csv` | Validación 2: 40 cuentas y sus cifras verdaderas |
| `muestra_validacion3_docs.csv` / `validacion3_referencia.csv` / `validacion3_resultado.csv` | Validación 3 (aceptación): 40 cuentas, cifras verdaderas y resultado cifra a cifra |
| `muestra_validacion4_docs.csv` / `validacion4_referencia.csv` / `validacion4_resultado.csv` | Validación 4: 40 cuentas, cifras verdaderas y resultado cifra a cifra |
| `muestra_validacion5_docs.csv` / `validacion5_referencia.csv` / `validacion5_resultado.csv` | Validación 5 (aceptación del panel final) |
| `contraste_externo.csv` / `contraste_externo_resultado.csv` | Contraste con cifras publicadas |
| `revision_manual/` | Scripts de la revisión manual, decisiones, listas de cifras revisadas y pendientes |
| `registrar_validacion.py` … `registrar_validacion5.py` | Scripts que vuelven a medir precisión y exhaustividad contra esas referencias |

Las imágenes de las páginas revisadas están en `C:\datos_premier\muestra_revision`, `C:\datos_premier\validacion`, `C:\datos_premier\validacion2`, `C:\datos_premier\validacion3` `C:\datos_premier\validacion4`, `C:\datos_premier\validacion5`, `C:\datos_premier\revision` y `C:\datos_premier\revision2`. No se suben a GitHub porque se pueden regenerar a partir de los PDF.

# Auditoría y validación de la fase 2 (actualizado el 4 nov 2026)

## 1. Auditoría inicial: qué estaba mal
- **Fase 1 (clubes y temporadas):** correcta. Hay 6 descensos causados por sanciones: Portsmouth 11/12, Wigan 19/20, Sheffield Wednesday 20/21, Derby 21/22, Reading 22/23 y Leicester 25/26.
- **Cobertura:** 651 de 660 club-temporadas tienen cuentas. Los 9 huecos son cuentas **nunca depositadas** por clubes en crisis, y se tratan como señal del modelo.
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

## 5. Próximos pasos
1. Panel: (a) en desacuerdos de dígito con el año siguiente, arbitrar con la identidad activos netos = patrimonio del mismo documento, y si no se puede, dejar en conflicto; (b) comprobar las identidades sobre los valores finales, vengan del documento que vengan; (c) política explícita para cifras reexpresadas (guardar la original y marcar la reexpresada).
2. Extractor: formato de 4 columnas con etiqueta partida, priorizar la página del balance frente al informe de administradores, "Net assets ." con puntuación, sueldos normales + excepcionales, "Staff costs" en la cuenta de resultados, impuesto frente a número de nota.
3. **Validación 4**: muestra nueva (semilla distinta, excluyendo las cuatro anteriores), medida una sola vez. Mismos criterios.
4. Revisión manual documentada de las cifras clave en conflicto, y contraste externo con ≥ 30 club-años publicados.

## 6. Archivos de esta carpeta (`datos_fase2/auditoria/`)
| Archivo | Contenido |
|---|---|
| `muestra_documentos.csv` | Las 30 cuentas de la auditoría inicial (muestra de desarrollo) |
| `muestra_referencia_resultados.csv` | Cifras verdaderas de esas 30 cuentas, revisadas a mano |
| `muestra_validacion_docs.csv` / `validacion_referencia.csv` | Validación 1: 60 cuentas y sus cifras verdaderas |
| `muestra_validacion2_docs.csv` / `validacion2_referencia.csv` | Validación 2: 40 cuentas y sus cifras verdaderas |
| `muestra_validacion3_docs.csv` / `validacion3_referencia.csv` / `validacion3_resultado.csv` | Validación 3 (aceptación): 40 cuentas, cifras verdaderas y resultado cifra a cifra |
| `registrar_validacion.py` / `registrar_validacion2.py` / `registrar_validacion3.py` | Scripts que vuelven a medir precisión y exhaustividad contra esas referencias |

Las imágenes de las páginas revisadas están en `C:\datos_premier\muestra_revision`, `C:\datos_premier\validacion`, `C:\datos_premier\validacion2` y `C:\datos_premier\validacion3`. No se suben a GitHub porque se pueden regenerar a partir de los PDF.

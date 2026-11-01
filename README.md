# Riesgo financiero individual y sistémico en el fútbol inglés

### Un test de estrés para la era del regulador

> **Estado:** en desarrollo, fase 2 de 5 (recopilación de cuentas).
> **Última actualización:** noviembre de 2026.
> **Datos:** solo fuentes públicas (Companies House, football-data.co.uk).

---

## Índice

1. [De qué va el proyecto](#1-de-qué-va-el-proyecto)
2. [Por qué ahora](#2-por-qué-ahora)
3. [Preguntas de investigación](#3-preguntas-de-investigación)
4. [Fases del proyecto y estado actual](#4-fases-del-proyecto-y-estado-actual)
5. [Resultados obtenidos hasta ahora](#5-resultados-obtenidos-hasta-ahora)
6. [Estructura del repositorio y qué contiene cada archivo](#6-estructura-del-repositorio-y-qué-contiene-cada-archivo)
7. [Cómo ejecutarlo desde otro ordenador](#7-cómo-ejecutarlo-desde-otro-ordenador)
8. [Decisiones de diseño y lecciones aprendidas](#8-decisiones-de-diseño-y-lecciones-aprendidas)
9. [Limitaciones conocidas](#9-limitaciones-conocidas)
10. [Glosario](#10-glosario)
11. [Fuentes](#11-fuentes)

---

## 1. De qué va el proyecto

Los clubes de fútbol ingleses pierden dinero de forma estructural. En la Championship (la segunda división) los salarios suelen superar el 100 % de los ingresos, y en los últimos quince años varios clubes históricos han entrado en **administración** (el equivalente británico al concurso de acreedores): Portsmouth, Bolton, Wigan, Derby y Sheffield Wednesday.

Este proyecto quiere **medir ese riesgo con datos públicos** y responder a dos preguntas:

1. **Riesgo individual:** ¿se puede anticipar, con años de antelación, qué club va a acabar en problemas financieros graves (administración, sanción por incumplir las normas, impago)?
2. **Riesgo sistémico:** los clubes se deben dinero entre sí porque los traspasos se pagan a plazos. Si un club cae, ¿cuántos otros arrastra y cuánto?

Para ello combinamos:

- **Contabilidad:** cuentas anuales depositadas en el registro mercantil británico (Companies House).
- **Derecho deportivo:** las normas financieras de la Premier League y de la EFL (Championship) y cómo han cambiado entre 2010 y 2026.
- **Economía y finanzas:** modelos de quiebra, calidad del beneficio, redes de contagio.
- **Ciencia de datos:** extracción automática (APIs, OCR), aprendizaje automático y análisis de redes.

**Ámbito:** los **62 clubes** que han jugado en la Premier League o en la Championship entre las temporadas 2010/11 y 2026/27.

---

## 2. Por qué ahora

- **Regulador nuevo.** El Independent Football Regulator (IFR) abre las solicitudes de licencia provisional entre noviembre de 2026 y febrero de 2027. Por primera vez, un organismo independiente va a vigilar la salud financiera de los clubes.
- **Normas nuevas en la Premier y la Championship.** Desde la temporada 2026/27 las antiguas normas de pérdidas máximas (PSR en la Premier, P&S en la EFL) se sustituyen por un **límite de gasto en plantilla en proporción a los ingresos** (SCR). La Premier League añade además unas **reglas de solidez financiera** (SSR).
- **Sanciones recientes.** Everton, Nottingham Forest, Leicester y Sheffield Wednesday han perdido puntos por incumplir normas financieras o por problemas de pagos.

Un análisis que compare **cómo habrían funcionado las normas antiguas y las nuevas** sobre quince años de datos reales es útil para clubes, ligas y regulador.

---

## 3. Preguntas de investigación

| # | Pregunta | Módulo |
|---|----------|--------|
| P1 | ¿Qué señales contables anticipan la crisis de un club con 1-3 años de antelación? | Modelo de riesgo individual |
| P2 | ¿Qué clubes "maquillan" su resultado (venta del estadio al propietario, plusvalías de cantera, patrocinios de empresas vinculadas)? | Índice de calidad del beneficio |
| P3 | ¿Cómo se propaga una quiebra por la red de deudas de traspasos? | Red de contagio y test de estrés |
| P4 | ¿Qué normas (PSR, SCR, SSR) habrían detectado antes y mejor los casos reales? | Evaluación de las normas |

---

## 4. Fases del proyecto y estado actual

```
Fase 0  Viabilidad                 ██████████  100 %  ✅ completada
Fase 1  Universo de clubes         ██████████  100 %  ✅ completada
Fase 2  Recopilación de cuentas    █░░░░░░░░░   10 %  🔄 en curso
Fase 3  Modelos de riesgo          ░░░░░░░░░░    0 %  ⏳ pendiente
Fase 4  Red de contagio y estrés   ░░░░░░░░░░    0 %  ⏳ pendiente
Fase 5  Evaluación y publicación   ░░░░░░░░░░    0 %  ⏳ pendiente
```

### Fase 0: Viabilidad ✅

**Objetivo:** comprobar que los datos públicos sirven antes de invertir meses de trabajo.

**Qué se hizo:**
- Registro en la API de Companies House y prueba con 4 clubes elegidos por ser casos distintos:
  - **Sheffield Wednesday:** club en crisis, cuentas en formato digital.
  - **Everton, Brentford y Liverpool:** grandes clubes cuyas cuentas son PDF escaneados (imágenes).
- Descarga del perfil de cada empresa, su historial de cuentas, sus préstamos garantizados (*charges*), sus administradores y sus tres últimas cuentas anuales.
- Dos vías de extracción:
  - **iXBRL** (formato digital): lectura directa de las cifras etiquetadas.
  - **PDF escaneado:** OCR (reconocimiento de texto en imágenes), primero rápido para localizar las páginas clave y después en alta resolución sobre esas páginas.

**Resultado:** **viabilidad confirmada.**
- Del iXBRL de Sheffield Wednesday salieron 784 cifras; el patrimonio neto negativo coincide con lo publicado en prensa.
- El OCR de las cuentas 2024/25 de Liverpool, Everton y Brentford acertó **14 de 14 cifras** comprobadas contra datos publicados.

### Fase 1: Universo de clubes ✅

**Objetivo:** saber qué clubes estudiar, en qué división estuvo cada uno cada temporada y qué empresa del registro mercantil corresponde a cada club.

**Qué se hizo:**
1. **Tabla clubes-temporada.** Con los resultados de todos los partidos de Premier y Championship desde 2010/11 (football-data.co.uk) se reconstruyó la clasificación de cada temporada. Salen **748 filas (club × temporada) y 62 clubes**. Para cada uno se sabe si ascendió, descendió o se quedó.
2. **Mapa club → sociedad.** Un club no es una empresa sino a menudo varias: la sociedad del club, un holding que la controla, una empresa del estadio… Además, cuando un club entra en administración su sociedad suele **cambiar de nombre** ("… Realisations Limited") y se crea otra nueva. Se resolvió en cuatro pasos:
   - búsqueda por nombre (229 candidatos);
   - búsqueda dirigida de los casos que no aparecieron;
   - consulta del registro de control (PSC, *quién controla a quién*) para los casos dudosos;
   - búsqueda a través de los antiguos directivos para las sociedades renombradas tras una administración.

**Resultado:** **84 sociedades** (club y grupo) asignadas a los 62 clubes; 61 filas con confianza alta y 6 con confianza media.

### Fase 2: Recopilación de cuentas 🔄 (fase actual)

**Objetivo:** construir un **panel financiero**, una tabla con las principales cifras de cada club en cada año: ingresos, salarios, amortizaciones, resultado, deuda, deudas por traspasos, patrimonio, etc.

**Pasos:**
- [x] Script de inventario de cuentas preparado (`fase2_inventario_cuentas.py`).
- [ ] Ejecutar el inventario: cuántas cuentas hay y en qué formato (iXBRL o PDF).
- [ ] Descargar las cuentas.
- [ ] Extraer las cifras: iXBRL automático; PDF con OCR más reglas de localización.
- [ ] Validar con identidades contables (activo = pasivo + patrimonio, etc.) y con cifras publicadas.
- [ ] Calcular los retrasos en el depósito de cuentas (señal de problemas).

### Fase 3: Modelos de riesgo individual ⏳

- **Variable a predecir:** administración, sanción de puntos, cuentas con duda sobre la continuidad del negocio (*going concern*), depósito fuera de plazo.
- **Modelos:** regresión logística penalizada y modelo de supervivencia en tiempo discreto, con *gradient boosting* como comparación.
- **Validación:** temporal (se entrena con el pasado y se prueba con el futuro), calibración e interpretabilidad (SHAP).
- **Índice de calidad del beneficio:** adaptación al fútbol de los modelos de Beneish y Altman.
- **Texto:** análisis de las notas de *going concern* con técnicas de lenguaje natural (NLP).

### Fase 4: Red de contagio y test de estrés ⏳

- Reconstrucción de la red de deudas por traspasos entre clubes (métodos de máxima entropía / RAS, porque solo se conocen los totales de cada club).
- Simulación de quiebras con los modelos **Eisenberg-Noe** y **DebtRank**.
- Incorporación de la regla de "acreedores futbolísticos": en una administración los demás clubes cobran íntegro pero tarde, así que el golpe es de **liquidez** más que de solvencia.

### Fase 5: Evaluación de normas y publicación ⏳

- Tratar cada norma (PSR, P&S, SCR, SSR, UEFA) como un clasificador: ¿a quién habría señalado y cuándo?
- Las normas se guardan como **parámetros en un archivo de configuración**, para poder actualizarlas si el regulador o las ligas las cambian.
- Publicación: informe, panel interactivo y artículo en LinkedIn.

---

## 5. Resultados obtenidos hasta ahora

### Validación del OCR (cuentas 2024/25, miles de £)

| Club | Concepto | Valor extraído |
|------|----------|---------------:|
| Liverpool | Ingresos | 702.722 |
| Liverpool | Resultado antes de impuestos | 15.212 |
| Liverpool | Gastos de personal | 427.727 |
| Liverpool | Beneficio por venta de jugadores | 53.268 |
| Everton | Ingresos | 196.697 |
| Everton | Resultado antes de impuestos | −8.609 |
| Brentford | Ingresos | 173.076 |
| Brentford | Beneficio por venta de jugadores | 27.236 |
| Brentford | Resultado antes de impuestos | −20.527 |

*Todas las cifras comprobadas (14/14) coinciden con las publicadas.*

### Hallazgos de la fase 1

- **Las sociedades cambian de nombre al quebrar.** Las antiguas sociedades de Bolton (`BWFC2019 Ltd`), Derby (`DC Realisations 1 Ltd`, todavía en administración) y Wigan (`Latics Realisations Ltd`) no aparecen buscando por el nombre del club. Si no se incluyen, el modelo solo vería clubes que sobrevivieron (**sesgo de supervivencia**).
- **Algunas matrices no están en el registro británico:** Manchester United plc (Islas Caimán) y la matriz de Birmingham City (cotiza en Hong Kong). De esos clubes solo tendremos las cuentas del club.
- **Normativa de 2010 a 2026:** la Premier y la Championship han tenido normas distintas y cambiantes (detalle en el documento del proyecto):

| Periodo | Premier League | Championship (EFL) |
|---------|----------------|--------------------|
| 2012-2016 | STCC (control de salarios), desde 2013 | FFP anual (pérdida máxima por temporada) |
| 2016-2026 | PSR: pérdida máxima de £105 m en 3 años | P&S: pérdida máxima de £39 m en 3 años |
| 2026/27 en adelante | SCR (85 % de los ingresos) + SSR (solidez) | SCR (85 % + aportaciones del propietario) |

---

## 6. Estructura del repositorio y qué contiene cada archivo

```
premierleague/
├── README.md                       ← este documento
├── requirements.txt                ← librerías de Python necesarias
├── .gitignore                      ← archivos que NO se suben a GitHub
├── api-premier-key.text            ← tu clave de la API (NO se sube; la creas tú)
│
├── fase0_prueba.py                 ← Fase 0: prueba de viabilidad con 4 clubes
├── ocr_rapido.py                   ← Fase 0: OCR rápido de un PDF escaneado
├── localizar_paginas.py            ← Fase 0: encuentra las páginas clave en el OCR rápido
├── ocr_selectivo.py                ← Fase 0: OCR de alta calidad solo en páginas clave
├── ocr_paginas.py                  ← Fase 0: OCR completo (versión inicial, lenta)
│
├── fase1_descargas.py              ← Fase 1: descarga resultados de partidos
├── fase1_clubes_temporada.py       ← Fase 1: construye la tabla club × temporada
├── fase1_sociedades.py             ← Fase 1: busca la sociedad de cada club
├── fase1_sociedades_pendientes.py  ← Fase 1: busca los clubes que no aparecieron
├── fase1_sociedades_cierre.py      ← Fase 1: búsqueda avanzada + quién controla a quién
├── fase1_sociedades_antiguas.py    ← Fase 1: sociedades renombradas tras una quiebra
│
├── fase2_inventario_cuentas.py     ← Fase 2: inventario de todas las cuentas depositadas
│
├── datos_fase0/                    ← resultados de la prueba de viabilidad
└── datos_fase1/                    ← tablas de clubes y sociedades
```

### 6.1 Archivos de configuración

| Archivo | Qué es |
|---------|--------|
| `.gitignore` | Lista de archivos que git ignora: la clave de la API, cachés de Python y datos brutos pesados que se pueden volver a descargar. |
| `requirements.txt` | Librerías de Python que hay que instalar (`requests`, `pandas`, `beautifulsoup4`). |
| `api-premier-key.text` | **Tu clave personal de la API.** Una sola línea con la clave, sin espacios. **Nunca se sube a GitHub** ni se escribe dentro del código. |

### 6.2 Scripts de la fase 0 (viabilidad)

| Script | Qué hace | Entrada | Salida |
|--------|----------|---------|--------|
| `fase0_prueba.py` | Comprueba la clave. Para 4 clubes (Sheffield Wednesday, Everton, Brentford, Liverpool): busca la empresa, descarga perfil, historial de cuentas, *charges* y administradores, calcula los retrasos en el depósito de cuentas, descarga las 3 últimas cuentas (iXBRL si existe, si no PDF) y extrae todas las cifras etiquetadas del iXBRL. | Clave de la API | `datos_fase0/<club>/…`, `cifras_ixbrl.csv`, `cifras_clave.csv`, `informe_fase0.txt` |
| `ocr_rapido.py` | Pasa un PDF escaneado por OCR a baja resolución (110 ppp, escala de grises). Es rápido y basta para *localizar* contenido, no para leer cifras con precisión. | Un PDF | `ocr_rapido/<pdf>/pag_NNN.txt` |
| `localizar_paginas.py` | Busca palabras clave en el OCR rápido para identificar qué página contiene cada estado financiero: cuenta de resultados, balance, flujos de caja, acreedores, deudores, personal, intangibles, *going concern*, partes vinculadas. | Carpeta del OCR rápido | `paginas_clave.json` |
| `ocr_selectivo.py` | OCR de alta calidad (300 ppp) solo sobre las páginas indicadas. Uso: `python ocr_selectivo.py archivo.pdf 14,15,19` | PDF y lista de páginas | `ocr/<pdf>/pag_NNN.txt` |
| `ocr_paginas.py` | Primera versión: OCR de *todas* las páginas a 250 ppp. Funciona pero es demasiado lenta; se sustituyó por la combinación rápido + selectivo. Se conserva como referencia. | Un PDF | Texto por página |

> **¿Por qué dos pasadas de OCR?** El OCR de alta calidad tarda unos 5 segundos por página. Unas cuentas tienen 40-60 páginas y solo interesan 5-8. La pasada rápida localiza las páginas útiles y la lenta solo se aplica a esas.

### 6.3 Scripts de la fase 1 (universo de clubes)

| Script | Qué hace | Salida |
|--------|----------|--------|
| `fase1_descargas.py` | Descarga los resultados de todos los partidos de Premier (`E0`) y Championship (`E1`) desde 2010/11 de football-data.co.uk. También intenta descargar datos de Transfermarkt (competiciones europeas); esa descarga **falla desde algunas redes** y no es imprescindible. | `datos_fase1/raw/fd_<temporada>_<E0/E1>.csv` |
| `fase1_clubes_temporada.py` | Reconstruye la clasificación de cada temporada (puntos, diferencia de goles, posición) **sin descontar sanciones**, y deduce el movimiento de cada club: ascenso, descenso o permanencia. No necesita internet. | `datos_fase1/clubes_temporada.csv` |
| `fase1_sociedades.py` | Para los 62 clubes, busca en Companies House las empresas cuyo nombre encaja, descarta fundaciones, peñas, equipos femeninos o academias y descarga el perfil de cada candidata. | `datos_fase1/candidatos_sociedades.csv` |
| `fase1_sociedades_pendientes.py` | Repite la búsqueda con nombres alternativos para los clubes que no aparecieron (p. ej. Crystal Palace se llama "CPFC Limited") e incluye los nombres anteriores de cada sociedad. | `datos_fase1/candidatos_pendientes.csv` |
| `fase1_sociedades_cierre.py` | (1) Búsqueda avanzada, que incluye sociedades disueltas. (2) Consulta del registro PSC para ver la cadena de control club → holding → propietario. | `datos_fase1/antiguas.csv`, `datos_fase1/control_psc.csv` |
| `fase1_sociedades_antiguas.py` | Encuentra las sociedades renombradas tras una administración buscando a sus antiguos directivos y listando todas las empresas en las que fueron administradores. | `datos_fase1/sociedades_via_directivos.csv` |

### 6.4 Scripts de la fase 2 (cuentas)

| Script | Qué hace | Salida |
|--------|----------|--------|
| `fase2_inventario_cuentas.py` | Para las 84 sociedades del mapa, lista todas las cuentas depositadas desde 2009: fecha de cierre, fecha de depósito, tipo (completas, abreviadas, consolidadas…) y formatos disponibles (iXBRL y/o PDF). **No descarga documentos**: sirve para planificar. Se puede relanzar y continúa donde se quedó. | `datos_fase2/inventario_cuentas.csv` |

### 6.5 Datos

#### `datos_fase0/`

| Archivo / carpeta | Contenido |
|-------------------|-----------|
| `<club>/perfil.json` | Ficha de la empresa: estado, fecha de creación, actividad, plazos de cuentas. |
| `<club>/historial_cuentas.json` | Todas las cuentas depositadas con sus fechas. |
| `<club>/charges.json` | Préstamos con garantía (hipotecas, pignoraciones de derechos de TV…). |
| `<club>/officers.json` | Administradores y secretarios, con sus fechas de nombramiento y cese. |
| `<club>/candidatos_busqueda.json` | Resultados brutos de la búsqueda de la empresa. |
| `<club>/cuentas/` | Cuentas descargadas (PDF o XHTML). *Ignoradas por git a partir de ahora.* |
| `<club>/ocr_rapido/`, `<club>/ocr/` | Texto extraído por OCR, por página. |
| `cifras_ixbrl.csv` | Todas las cifras etiquetadas extraídas del iXBRL (una fila por cifra). |
| `cifras_clave.csv` | Selección de las cifras principales. |
| `cifras_clave_ocr_2024_25.csv` | Cifras extraídas por OCR de las cuentas 2024/25. |
| `validacion_ocr_2024_25.csv` | Comparación OCR frente a datos publicados (14/14 correctas). |
| `informe_fase0.txt` | Resumen legible de la prueba. |

#### `datos_fase1/`

| Archivo | Contenido | Columnas principales |
|---------|-----------|----------------------|
| `clubes_temporada.csv` | 748 filas, una por club y temporada. | `temporada`, `division` (E0 = Premier, E1 = Championship), `club`, `partidos`, `puntos_sin_sanciones`, `dif_goles`, `posicion_sin_sanciones`, `division_siguiente`, `movimiento` |
| `candidatos_sociedades.csv` | 229 empresas candidatas de la primera búsqueda. | `club`, `numero`, `nombre`, `estado`, `creada`, `actividad_sic`, `ultimas_cuentas_tipo`, `historial_insolvencia`… |
| `candidatos_pendientes.csv` | Candidatos de la búsqueda dirigida. | Las mismas, más `nombres_anteriores` |
| `antiguas.csv` | Resultados de la búsqueda avanzada. | `club`, `numero`, `nombre`, `estado`, `creada`, `disuelta` |
| `control_psc.csv` | Quién controla a cada sociedad dudosa. | `numero`, `controlador`, `numero_controlador`, `desde`, `hasta` |
| `sociedades_via_directivos.csv` | Sociedades encontradas a través de antiguos directivos. | `club`, `directivo`, `numero`, `nombre`, `estado`, `nombrado`, `cese` |
| **`mapa_sociedades.csv`** | **Tabla final: qué sociedad corresponde a cada club en cada periodo.** Es la entrada de la fase 2. | `club`, `numero_club`, `sociedad_club`, `numero_grupo`, `sociedad_grupo`, `temporadas`, `confianza`, `nota` |
| `raw/` | CSV originales de football-data (ignorados por git). | |

> **Nota sobre los nombres de los clubes:** se usa la grafía de football-data.co.uk (`Man United`, `Nott'm Forest`, `Sheffield Weds`, `Peterboro`…), que es la clave común de todas las tablas.

---

## 7. Cómo ejecutarlo desde otro ordenador

### 7.1 Requisitos

| Requisito | Para qué | Obligatorio |
|-----------|----------|-------------|
| Python 3.10 o superior (recomendado: [Anaconda](https://www.anaconda.com/download)) | Ejecutar los scripts | Sí |
| Git | Clonar el repositorio | Sí |
| Cuenta y clave de la API de Companies House | Descargar datos del registro mercantil | Sí, para las fases 0, 1 y 2 |
| Poppler (`pdftoppm`) y Tesseract OCR | Leer los PDF escaneados | Solo para el OCR |

### 7.2 Paso 1: clonar el repositorio

```bash
git clone https://github.com/alvmorenobl/premierleague.git
cd premierleague
```

### 7.3 Paso 2: instalar las librerías

```bash
pip install -r requirements.txt
```

Con Anaconda, `pandas` y `requests` ya vienen instaladas; puede que solo falte `beautifulsoup4`.

### 7.4 Paso 3: conseguir la clave de la API de Companies House (gratis, unos 10 minutos)

1. Entra en <https://developer.company-information.service.gov.uk/> y crea una cuenta. Desde agosto de 2026 el acceso es con **GOV.UK One Login**.
2. Ve a **Your applications → Create an application**.
   - *Application name:* p. ej. `Football Finance Research`
   - *Description:* solo letras, espacios y guiones, **sin puntos ni comas**; p. ej. `Academic research on football club finances`
   - *Environment:* **Live**
3. Dentro de la aplicación pulsa **Create new key** y elige el tipo **REST**.
4. Copia la clave con el botón de copiar.
5. En la carpeta del proyecto crea un archivo llamado **`api-premier-key.text`** y pega la clave en una sola línea, sin espacios ni comillas.

> ⚠️ **Seguridad**
> - El archivo de la clave está en `.gitignore`, así que git no lo sube.
> - **No pegues la clave** dentro de ningún script, chat ni captura de pantalla.
> - Si la clave se expone, bórrala en el portal y crea una nueva.

**Límite de la API:** 600 peticiones cada 5 minutos. Los scripts hacen una pausa de unos 0,6 s entre peticiones y esperan 60 s si reciben el aviso de límite (error 429).

### 7.5 Paso 4: instalar las herramientas de OCR (opcional)

Solo hacen falta si vas a leer PDF escaneados.

- **Windows:**
  - Tesseract: instalador de [UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki).
  - Poppler: [poppler-windows](https://github.com/oschwartz10612/poppler-windows/releases), descomprimir y añadir la carpeta `bin` al PATH.
- **macOS:** `brew install tesseract poppler`
- **Linux:** `sudo apt install tesseract-ocr poppler-utils`

Comprueba que funcionan con `tesseract --version` y `pdftoppm -v`.

### 7.6 Paso 5: ejecutar en orden

Abre una terminal (en Windows, **Anaconda Prompt**) **dentro de la carpeta del proyecto** y ejecuta:

| Orden | Comando | Tiempo aprox. | Necesita internet | Resultado |
|------:|---------|---------------|:-----------------:|-----------|
| 1 | `python fase0_prueba.py` | 2-3 min | ✅ | Prueba con 4 clubes (opcional, solo demostrativo) |
| 2 | `python fase1_descargas.py` | 1-2 min | ✅ | Resultados de partidos 2010-2027 |
| 3 | `python fase1_clubes_temporada.py` | segundos | ❌ | `clubes_temporada.csv` |
| 4 | `python fase1_sociedades.py` | 5-8 min | ✅ | Candidatos de sociedades |
| 5 | `python fase1_sociedades_pendientes.py` | 1-2 min | ✅ | Candidatos de los casos difíciles |
| 6 | `python fase1_sociedades_cierre.py` | < 1 min | ✅ | Búsqueda avanzada y cadena de control |
| 7 | `python fase1_sociedades_antiguas.py` | ~1 min | ✅ | Sociedades renombradas tras quiebras |
| 8 | `python fase2_inventario_cuentas.py` | 10-15 min | ✅ | Inventario de cuentas |

> **Importante:** `mapa_sociedades.csv` **no lo genera ningún script automáticamente.** Es el resultado de revisar los candidatos de los pasos 4-7 (con justificación en la columna `nota`). Ya está incluido en el repositorio, así que **para reproducir la fase 2 basta con ejecutar el paso 8.**

**OCR de un PDF escaneado (opcional):**

```bash
python ocr_rapido.py ruta/al/archivo.pdf          # 1. OCR rápido de todo el PDF
python localizar_paginas.py ruta/a/ocr_rapido/... # 2. localiza las páginas clave
python ocr_selectivo.py ruta/al/archivo.pdf 14,15 # 3. OCR fino de esas páginas
```

### 7.7 Problemas frecuentes

| Problema | Causa | Solución |
|----------|-------|----------|
| `FileNotFoundError: api-premier-key.text` | No has creado el archivo de la clave o estás en otra carpeta | Crea el archivo y ejecuta los scripts desde la carpeta del proyecto (`cd premierleague`) |
| Error `401` | Clave incorrecta, con espacios, o creada como tipo distinto de REST | Revisa el archivo; si hace falta, crea una clave nueva |
| Error `429` | Demasiadas peticiones | El script espera solo; si se corta, vuelve a lanzarlo |
| `WinError 10060` en Transfermarkt | Tu red no llega a ese servidor | No es imprescindible; ignóralo |
| `ModuleNotFoundError: bs4` | Falta la librería | `pip install beautifulsoup4` |
| Aviso `LF will be replaced by CRLF` al hacer `git add` | Diferencia de saltos de línea entre Windows y Linux | Inofensivo. Para quitarlo: `git config core.autocrlf true` |
| `tesseract` o `pdftoppm` no encontrados | No están instalados o no están en el PATH | Ver el paso 4 |

---

## 8. Decisiones de diseño y lecciones aprendidas

1. **Solo datos públicos.** Cualquier persona puede reproducir el trabajo y no depende de que un club quiera colaborar.
2. **Sociedad del club como unidad principal y grupo como secundaria.** Las normas de la Premier y de la EFL miran al club *y a su grupo*, así que se guardan ambos.
3. **Un club puede tener varias sociedades a lo largo del tiempo.** El mapa tiene una fila por club *y periodo* (p. ej. Derby: sociedad antigua hasta 2022 y nueva desde 2024).
4. **Incluir los clubes que quebraron** para evitar el sesgo de supervivencia.
5. **Clasificaciones "sin sanciones".** Se calculan los puntos deportivos sin restar sanciones; las sanciones se añadirán como variable aparte, porque son justamente lo que queremos explicar.
6. **Las normas son parámetros, no código.** Las normas financieras cambian casi cada temporada, así que se guardan en configuración para poder actualizarlas sin rehacer el análisis.
7. **La Premier y la Championship son el núcleo; la UEFA es secundaria.** Las normas de la UEFA solo afectan a los clubes que juegan en Europa y se usan como contexto.
8. **Automatización por partes.** Cada paso es un script corto, reanudable y que guarda su resultado en CSV, para poder revisar a mano lo dudoso.

---

## 9. Limitaciones conocidas

- **Cuentas abreviadas.** Algunos clubes pequeños (Doncaster, Scunthorpe, Wycombe, Yeovil) presentan cuentas reducidas con pocas cifras.
- **Matrices extranjeras.** Las cuentas de Manchester United plc (Islas Caimán) y de la matriz de Birmingham (Hong Kong) no están en Companies House.
- **PDF escaneados.** Muchos clubes grandes depositan imágenes; el OCR funciona pero hay que validar cada cifra.
- **Formatos distintos.** Cada club presenta su cuenta de resultados con un diseño diferente (p. ej. Everton usa seis columnas), y estandarizarlo es parte del trabajo de la fase 2.
- **Cuentas modificadas (AAMD).** Algunas cuentas se vuelven a depositar corregidas y aparecen duplicadas; falta filtrarlas en el cálculo de retrasos.
- **Competiciones europeas.** La tabla de participación europea está pendiente porque la fuente prevista (Transfermarkt) no es accesible desde todas las redes.

---

## 10. Glosario

| Término | Significado |
|---------|-------------|
| **Administración** | Procedimiento de insolvencia británico, parecido al concurso de acreedores. En el fútbol inglés implica sanción de puntos. |
| **Companies House** | Registro mercantil del Reino Unido. Todas las sociedades depositan allí sus cuentas anuales. |
| **iXBRL** | Formato digital de cuentas en el que cada cifra lleva una etiqueta legible por máquina. |
| **OCR** | Reconocimiento óptico de caracteres: convierte una imagen de texto en texto. |
| **PSC** | *Persons with Significant Control*: registro público de quién controla cada sociedad. |
| **Charges** | Préstamos o deudas con garantía sobre bienes de la sociedad. |
| **Going concern** | Empresa en funcionamiento. Si los auditores o administradores dudan de que la empresa pueda seguir operando, lo deben indicar en las cuentas. |
| **PSR** | *Profitability and Sustainability Rules* de la Premier League (2016-2026): pérdida máxima de £105 m en tres años. |
| **P&S** | Normas equivalentes de la EFL: pérdida máxima de £39 m en tres años en la Championship. |
| **SCR** | *Squad Cost Ratio*: gasto en plantilla limitado a un porcentaje de los ingresos. En vigor en Premier y Championship desde 2026/27. |
| **SSR** | *Sustainability and Systemic Resilience*: tests de liquidez y solvencia de la Premier League desde 2026/27. |
| **IFR** | *Independent Football Regulator*: regulador independiente del fútbol inglés. |
| **DebtRank / Eisenberg-Noe** | Modelos para simular cómo se propagan las pérdidas en una red de deudas. |
| **SHAP** | Método para explicar qué variables pesan en cada predicción de un modelo. |

---

## 11. Fuentes

- **Companies House API:** <https://developer.company-information.service.gov.uk/>
- **Football-Data.co.uk:** resultados históricos, <https://www.football-data.co.uk/>
- **Premier League Handbook:** normas financieras de cada temporada.
- **EFL Regulations:** normas de la Championship.
- **Deloitte Annual Review of Football Finance.**
- Literatura académica: Szymanski; Plumley, Wilson y Ramchandani; Alaminos y Fernández; Eisenberg y Noe (2001); Battiston et al. (DebtRank, 2012).

---

*Proyecto de investigación independiente. No está afiliado a la Premier League, la EFL, la UEFA ni a ningún club.*

# Individual and Systemic Financial Risk in English Football

### A stress test for the regulator era

> **Status:** in progress. Phases 0–2 completed (validated financial panel); next: phase 3 (risk models).
> **Last updated:** November 2026.
> **Data:** public sources only (Companies House, football-data.co.uk).

---

## Contents

1. [What the project is about](#1-what-the-project-is-about)
2. [Why now](#2-why-now)
3. [Research questions](#3-research-questions)
4. [Project phases and current status](#4-project-phases-and-current-status)
5. [Results so far](#5-results-so-far)
6. [Repository structure and what each file contains](#6-repository-structure-and-what-each-file-contains)
7. [How to run it on another computer](#7-how-to-run-it-on-another-computer)
8. [Design decisions and lessons learned](#8-design-decisions-and-lessons-learned)
9. [Known limitations](#9-known-limitations)
10. [Glossary](#10-glossary)
11. [Sources](#11-sources)

---

## 1. What the project is about

English football clubs lose money structurally. In the Championship (the second tier), wages often exceed 100 % of revenue, and over the last fifteen years several historic clubs have gone into **administration** (the British insolvency procedure): Portsmouth, Bolton, Wigan, Derby and Sheffield Wednesday.

This project aims to **measure that risk with public data** and answer two questions:

1. **Individual risk:** can we anticipate, years in advance, which club will end up in serious financial trouble (administration, sanctions for breaking the rules, missed payments)?
2. **Systemic risk:** clubs owe each other money because transfer fees are paid in instalments. If one club fails, how many others does it drag down, and by how much?

To do this, the project combines:

- **Accounting:** annual accounts filed with the UK companies register (Companies House).
- **Sports regulation:** the financial rules of the Premier League and the EFL (Championship) and how they changed between 2010 and 2026.
- **Economics and finance:** bankruptcy models, earnings quality, contagion networks.
- **Data science:** automated extraction (APIs, OCR), machine learning and network analysis.

**Scope:** the **62 clubs** that played in the Premier League or the Championship between the 2010/11 and 2026/27 seasons.

---

## 2. Why now

- **A new regulator.** The Independent Football Regulator (IFR) opens applications for provisional licences between November 2026 and February 2027. For the first time, an independent body will oversee the financial health of clubs.
- **New rules in the Premier League and the Championship.** From the 2026/27 season, the old maximum-loss rules (PSR in the Premier League, P&S in the EFL) are replaced by a **cap on squad spending as a share of revenue** (SCR). The Premier League also adds **financial resilience rules** (SSR).
- **Recent sanctions.** Everton, Nottingham Forest, Leicester and Sheffield Wednesday have been deducted points for breaking financial rules or for payment problems.

An analysis that compares **how the old and the new rules would have performed** on fifteen years of real data is useful for clubs, leagues and the regulator.

---

## 3. Research questions

| # | Question | Module |
|---|----------|--------|
| Q1 | Which accounting signals anticipate a club's crisis 1–3 years in advance? | Individual risk model |
| Q2 | Which clubs "dress up" their results (selling the stadium to the owner, academy player sales, sponsorships from related companies)? | Earnings quality index |
| Q3 | How does a bankruptcy spread through the network of transfer debts? | Contagion network and stress test |
| Q4 | Which rules (PSR, SCR, SSR) would have detected the real cases earlier and better? | Rule evaluation |

---

## 4. Project phases and current status

```
Phase 0  Feasibility                ██████████  100 %  completed
Phase 1  Universe of clubs          ██████████  100 %  completed
Phase 2  Collection of accounts     ██████████  100 %  completed
Phase 3  Risk models                ░░░░░░░░░░    0 %  next
Phase 4  Contagion network & stress ░░░░░░░░░░    0 %  pending
Phase 5  Evaluation & publication   ░░░░░░░░░░    0 %  pending
```

### Phase 0: Feasibility (completed)

**Goal:** check that public data is good enough before investing months of work.

**What was done:**
- Registration with the Companies House API and a test with 4 clubs chosen because they are different cases:
  - **Sheffield Wednesday:** a club in crisis, with accounts in digital format.
  - **Everton, Brentford and Liverpool:** large clubs whose accounts are scanned PDFs (images).
- Download of each company's profile, filing history, secured loans (*charges*), officers and its last three annual accounts.
- Two extraction routes:
  - **iXBRL** (digital format): direct reading of the tagged figures.
  - **Scanned PDF:** OCR (optical character recognition), first a fast pass to locate the key pages and then a high-resolution pass on those pages only.

**Result:** **feasibility confirmed.**
- 784 figures were extracted from Sheffield Wednesday's iXBRL; the negative equity matches what was reported in the press.
- The OCR of the 2024/25 accounts of Liverpool, Everton and Brentford got **14 out of 14 figures** right when checked against published data.

### Phase 1: Universe of clubs (completed)

**Goal:** know which clubs to study, which division each one was in every season, and which company in the register corresponds to each club.

**What was done:**
1. **Club-season table.** Using the results of every Premier League and Championship match since 2010/11 (football-data.co.uk), the league table of every season was rebuilt. The result is **748 rows (club × season) and 62 clubs**. For each one we know whether it was promoted, relegated or stayed.
2. **Club → company map.** A club is not one company but often several: the club company, a holding company that controls it, a stadium company… In addition, when a club goes into administration its company usually **changes its name** ("… Realisations Limited") and a new one is created. This was solved in four steps:
   - search by name (229 candidates);
   - targeted search for the cases that did not appear;
   - lookup in the register of control (PSC, *who controls whom*) for unclear cases;
   - search through former directors for companies renamed after an administration.

**Result:** **84 companies** (club and group) assigned to the 62 clubs; 61 rows with high confidence and 6 with medium confidence.

### Phase 2: Collection of accounts (completed)

**Goal:** build a **financial panel**, a table with the main figures of each club in each year (revenue, wages, profit, equity, debt, etc.), with proven reliability.

**What was done:**
1. **Inventory and download.** 1,259 valid annual accounts were identified for the 84 companies and all of them were downloaded: about 1,120 as scanned PDFs and 143 in iXBRL. The filing delay of each set of accounts was also calculated: 63 were clearly filed late.
2. **OCR.** A fast pass (110 dpi) went through 31,848 pages to locate the financial statements, and a fine pass (300 dpi) read those pages, plus a complementary pass over 2,381 more pages.
3. **Rule-based extraction** (`fase2_extraer_cifras.py`) and **iXBRL** (`fase2_extraer_ixbrl.py`): labels, columns, units and layouts from 1 to 6 columns.
4. **Validated panel** (`fase2_panel.py`):
   - each figure for year *t* is checked against the comparative figure repeated in the accounts for *t+1*;
   - discrepancies are classified: units, sign, digit, truncation, column or restatement;
   - accounting identities are applied;
   - **nothing is corrected without evidence**: the figure is flagged as a conflict and left out of the reliable panel.
5. **Targeted manual review.** 227 key figures for the club-seasons in the study were checked against the PDF and documented one by one in `datos_fase2/correcciones_manuales.csv`.
6. **Audit and blind validation.** Five samples of 30–60 accounts were used, each reviewed figure by figure against the PDF image; the samples used to tune the rules were considered "contaminated" and do not count as evidence. Everything is in `datos_fase2/auditoria/AUDITORIA_FASE2.md`.

**Result (validation 5, new blind sample, measured only once):**

| | Precision | Recall |
|---|---|---|
| Final reliable panel | **100 %** (175/175) | **99.4 %** (175/176) |

- **Check against 63 published figures** (Deloitte, press): no reading errors. The 4–10 % differences for Arsenal, Chelsea and Man United are because the panel uses the club company, not the group's parent company.
- **Key figures without a reliable value:** 70 out of 3,332. Of these, 17 are accounts that were never filed, 19 are abbreviated accounts and 34 are documented as pending.

**Limitations for phase 3:**
- The group parent companies of Arsenal and Chelsea are missing.
- Secondary items (tax, creditors, cash) do not have the same level of validation.
- Gaps in the reliable panel must be handled explicitly in the models.

### Phase 3: Individual risk models (next)

- **Target variable:** administration, points deduction, accounts with a *going concern* warning, late filing.
- **Models:** penalised logistic regression and a discrete-time survival model, with *gradient boosting* as a benchmark.
- **Validation:** temporal (train on the past, test on the future), calibration and interpretability (SHAP).
- **Earnings quality index:** adaptation of the Beneish and Altman models to football.
- **Text:** analysis of *going concern* notes with natural language processing (NLP).

### Phase 4: Contagion network and stress test (pending)

- Reconstruction of the network of transfer debts between clubs (maximum entropy / RAS methods, because only each club's totals are known).
- Default simulation with the **Eisenberg-Noe** and **DebtRank** models.
- Inclusion of the "football creditor" rule: in an administration, other clubs are paid in full but late, so the shock hits **liquidity** rather than solvency.

### Phase 5: Rule evaluation and publication (pending)

- Treat each rule (PSR, P&S, SCR, SSR, UEFA) as a classifier: which clubs would it have flagged, and when?
- The rules are stored as **parameters in a configuration file**, so they can be updated if the regulator or the leagues change them.
- Publication: report, interactive dashboard and a LinkedIn article.

---

## 5. Results so far

### OCR validation (2024/25 accounts, £ thousands)

| Club | Item | Extracted value |
|------|------|----------------:|
| Liverpool | Revenue | 702,722 |
| Liverpool | Profit before tax | 15,212 |
| Liverpool | Staff costs | 427,727 |
| Liverpool | Profit on player sales | 53,268 |
| Everton | Revenue | 196,697 |
| Everton | Profit before tax | −8,609 |
| Brentford | Revenue | 173,076 |
| Brentford | Profit on player sales | 27,236 |
| Brentford | Profit before tax | −20,527 |

*All figures checked (14/14) match the published ones.*

### Phase 1 findings

- **Companies change their name when they go bust.** The former companies of Bolton (`BWFC2019 Ltd`), Derby (`DC Realisations 1 Ltd`, still in administration) and Wigan (`Latics Realisations Ltd`) do not show up when searching by the club's name. If they were left out, the model would only see clubs that survived (**survivorship bias**).
- **Some parent companies are not in the UK register:** Manchester United plc (Cayman Islands) and Birmingham City's parent company (listed in Hong Kong). For those clubs only the club company's accounts are available.
- **Rules from 2010 to 2026:** the Premier League and the Championship have had different, changing rules (details in the project document):

| Period | Premier League | Championship (EFL) |
|--------|----------------|--------------------|
| 2012–2016 | STCC (wage control), from 2013 | Annual FFP (maximum loss per season) |
| 2016–2026 | PSR: maximum loss of £105m over 3 years | P&S: maximum loss of £39m over 3 years |
| 2026/27 onwards | SCR (85 % of revenue) + SSR (resilience) | SCR (85 % + owner contributions) |

---

## 6. Repository structure and what each file contains

```
premierleague/
├── README.md                       ← this document
├── requirements.txt                ← required Python libraries
├── .gitignore                      ← files that are NOT pushed to GitHub
├── api-premier-key.text            ← your API key (NOT pushed; you create it)
│
├── fase0_prueba.py                 ← Phase 0: feasibility test with 4 clubs
├── ocr_rapido.py                   ← Phase 0: fast OCR of a scanned PDF
├── localizar_paginas.py            ← Phase 0: finds the key pages in the fast OCR
├── ocr_selectivo.py                ← Phase 0: high-quality OCR on key pages only
├── ocr_paginas.py                  ← Phase 0: full OCR (initial, slow version)
│
├── fase1_descargas.py              ← Phase 1: downloads match results
├── fase1_clubes_temporada.py       ← Phase 1: builds the club × season table
├── fase1_sociedades.py             ← Phase 1: finds each club's company
├── fase1_sociedades_pendientes.py  ← Phase 1: searches for the clubs that did not appear
├── fase1_sociedades_cierre.py      ← Phase 1: advanced search + who controls whom
├── fase1_sociedades_antiguas.py    ← Phase 1: companies renamed after a bankruptcy
│
├── fase2_inventario_cuentas.py     ← Phase 2: inventory of all filed accounts
│
├── datos_fase0/                    ← feasibility test results
└── datos_fase1/                    ← club and company tables
```

*File, folder and column names are kept in Spanish, as in the code.*

### 6.1 Configuration files

| File | What it is |
|------|------------|
| `.gitignore` | List of files git ignores: the API key, Python caches and heavy raw data that can be downloaded again. |
| `requirements.txt` | Python libraries to install (`requests`, `pandas`, `beautifulsoup4`). |
| `api-premier-key.text` | **Your personal API key.** A single line with the key, no spaces. **It is never pushed to GitHub** nor written inside the code. |

### 6.2 Phase 0 scripts (feasibility)

| Script | What it does | Input | Output |
|--------|--------------|-------|--------|
| `fase0_prueba.py` | Checks the key. For 4 clubs (Sheffield Wednesday, Everton, Brentford, Liverpool): finds the company, downloads its profile, filing history, *charges* and officers, calculates filing delays, downloads the last 3 accounts (iXBRL if available, otherwise PDF) and extracts every tagged figure from the iXBRL. | API key | `datos_fase0/<club>/…`, `cifras_ixbrl.csv`, `cifras_clave.csv`, `informe_fase0.txt` |
| `ocr_rapido.py` | Runs OCR on a scanned PDF at low resolution (110 dpi, greyscale). It is fast and good enough to *locate* content, not to read figures accurately. | A PDF | `ocr_rapido/<pdf>/pag_NNN.txt` |
| `localizar_paginas.py` | Searches for keywords in the fast OCR to identify which page contains each financial statement: income statement, balance sheet, cash flow, creditors, debtors, staff, intangibles, *going concern*, related parties. | Fast OCR folder | `paginas_clave.json` |
| `ocr_selectivo.py` | High-quality OCR (300 dpi) only on the given pages. Usage: `python ocr_selectivo.py file.pdf 14,15,19` | PDF and list of pages | `ocr/<pdf>/pag_NNN.txt` |
| `ocr_paginas.py` | First version: OCR of *all* pages at 250 dpi. It works but is too slow; it was replaced by the fast + selective combination. Kept for reference. | A PDF | Text per page |

> **Why two OCR passes?** High-quality OCR takes about 5 seconds per page. A set of accounts has 40–60 pages and only 5–8 of them matter. The fast pass finds the useful pages and the slow pass is applied only to those.

### 6.3 Phase 1 scripts (universe of clubs)

| Script | What it does | Output |
|--------|--------------|--------|
| `fase1_descargas.py` | Downloads the results of every Premier League (`E0`) and Championship (`E1`) match since 2010/11 from football-data.co.uk. It also tries to download Transfermarkt data (European competitions); that download **fails from some networks** and is not essential. | `datos_fase1/raw/fd_<season>_<E0/E1>.csv` |
| `fase1_clubes_temporada.py` | Rebuilds each season's league table (points, goal difference, position) **without deducting sanctions**, and works out each club's movement: promotion, relegation or staying. Does not need internet access. | `datos_fase1/clubes_temporada.csv` |
| `fase1_sociedades.py` | For the 62 clubs, searches Companies House for companies whose name matches, discards foundations, supporters' clubs, women's teams or academies, and downloads each candidate's profile. | `datos_fase1/candidatos_sociedades.csv` |
| `fase1_sociedades_pendientes.py` | Repeats the search with alternative names for the clubs that did not appear (e.g. Crystal Palace is "CPFC Limited") and includes each company's previous names. | `datos_fase1/candidatos_pendientes.csv` |
| `fase1_sociedades_cierre.py` | (1) Advanced search, which includes dissolved companies. (2) Lookup in the PSC register to see the chain of control club → holding → owner. | `datos_fase1/antiguas.csv`, `datos_fase1/control_psc.csv` |
| `fase1_sociedades_antiguas.py` | Finds companies renamed after an administration by searching for their former directors and listing every company where they were officers. | `datos_fase1/sociedades_via_directivos.csv` |

### 6.4 Phase 2 scripts (accounts)

| Script | What it does | Output |
|--------|--------------|--------|
| `fase2_inventario_cuentas.py` | For the 84 companies in the map, lists every set of accounts filed since 2009: year-end date, filing date, type (full, abbreviated, consolidated…) and available formats (iXBRL and/or PDF). **It does not download documents**: it is for planning. It can be re-run and resumes where it left off. | `datos_fase2/inventario_cuentas.csv` |

### 6.5 Data

#### `datos_fase0/`

| File / folder | Content |
|---------------|---------|
| `<club>/perfil.json` | Company profile: status, incorporation date, activity, accounts deadlines. |
| `<club>/historial_cuentas.json` | Every set of accounts filed, with its dates. |
| `<club>/charges.json` | Secured loans (mortgages, pledges of TV rights…). |
| `<club>/officers.json` | Directors and secretaries, with their appointment and resignation dates. |
| `<club>/candidatos_busqueda.json` | Raw results of the company search. |
| `<club>/cuentas/` | Downloaded accounts (PDF or XHTML). *Ignored by git from now on.* |
| `<club>/ocr_rapido/`, `<club>/ocr/` | Text extracted by OCR, per page. |
| `cifras_ixbrl.csv` | Every tagged figure extracted from the iXBRL (one row per figure). |
| `cifras_clave.csv` | Selection of the main figures. |
| `cifras_clave_ocr_2024_25.csv` | Figures extracted by OCR from the 2024/25 accounts. |
| `validacion_ocr_2024_25.csv` | OCR vs. published data comparison (14/14 correct). |
| `informe_fase0.txt` | Readable summary of the test. |

#### `datos_fase1/`

| File | Content | Main columns |
|------|---------|--------------|
| `clubes_temporada.csv` | 748 rows, one per club and season. | `temporada`, `division` (E0 = Premier League, E1 = Championship), `club`, `partidos`, `puntos_sin_sanciones`, `dif_goles`, `posicion_sin_sanciones`, `division_siguiente`, `movimiento` |
| `candidatos_sociedades.csv` | 229 candidate companies from the first search. | `club`, `numero`, `nombre`, `estado`, `creada`, `actividad_sic`, `ultimas_cuentas_tipo`, `historial_insolvencia`… |
| `candidatos_pendientes.csv` | Candidates from the targeted search. | The same, plus `nombres_anteriores` |
| `antiguas.csv` | Results of the advanced search. | `club`, `numero`, `nombre`, `estado`, `creada`, `disuelta` |
| `control_psc.csv` | Who controls each unclear company. | `numero`, `controlador`, `numero_controlador`, `desde`, `hasta` |
| `sociedades_via_directivos.csv` | Companies found through former directors. | `club`, `directivo`, `numero`, `nombre`, `estado`, `nombrado`, `cese` |
| **`mapa_sociedades.csv`** | **Final table: which company corresponds to each club in each period.** It is the input for phase 2. | `club`, `numero_club`, `sociedad_club`, `numero_grupo`, `sociedad_grupo`, `temporadas`, `confianza`, `nota` |
| `raw/` | Original football-data CSVs (ignored by git). | |

> **Note on club names:** the spelling used by football-data.co.uk (`Man United`, `Nott'm Forest`, `Sheffield Weds`, `Peterboro`…) is used as the common key across all tables.

---

## 7. How to run it on another computer

### 7.1 Requirements

| Requirement | What for | Required |
|-------------|----------|----------|
| Python 3.10 or later (recommended: [Anaconda](https://www.anaconda.com/download)) | Running the scripts | Yes |
| Git | Cloning the repository | Yes |
| Companies House account and API key | Downloading data from the companies register | Yes, for phases 0, 1 and 2 |
| Poppler (`pdftoppm`) and Tesseract OCR | Reading scanned PDFs | Only for OCR |

### 7.2 Step 1: clone the repository

```bash
git clone https://github.com/alvmorenobl/premierleague.git
cd premierleague
```

### 7.3 Step 2: install the libraries

```bash
pip install -r requirements.txt
```

With Anaconda, `pandas` and `requests` are already installed; you may only need `beautifulsoup4`.

### 7.4 Step 3: get a Companies House API key (free, about 10 minutes)

1. Go to <https://developer.company-information.service.gov.uk/> and create an account. Since August 2026, access is through **GOV.UK One Login**.
2. Go to **Your applications → Create an application**.
   - *Application name:* e.g. `Football Finance Research`
   - *Description:* letters, spaces and hyphens only, **no full stops or commas**; e.g. `Academic research on football club finances`
   - *Environment:* **Live**
3. Inside the application, click **Create new key** and choose the **REST** type.
4. Copy the key with the copy button.
5. In the project folder, create a file called **`api-premier-key.text`** and paste the key on a single line, with no spaces or quotes.

> **Security**
> - The key file is listed in `.gitignore`, so git does not push it.
> - **Do not paste the key** into any script, chat or screenshot.
> - If the key is exposed, delete it in the portal and create a new one.

**API limit:** 600 requests every 5 minutes. The scripts pause for about 0.6 s between requests and wait 60 s if they receive the rate-limit warning (error 429).

### 7.5 Step 4: install the OCR tools (optional)

Only needed if you are going to read scanned PDFs.

- **Windows:**
  - Tesseract: [UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki) installer.
  - Poppler: [poppler-windows](https://github.com/oschwartz10612/poppler-windows/releases), unzip it and add the `bin` folder to the PATH.
- **macOS:** `brew install tesseract poppler`
- **Linux:** `sudo apt install tesseract-ocr poppler-utils`

Check that they work with `tesseract --version` and `pdftoppm -v`.

### 7.6 Step 5: run in order

Open a terminal (on Windows, **Anaconda Prompt**) **inside the project folder** and run:

| Order | Command | Approx. time | Needs internet | Result |
|------:|---------|--------------|:--------------:|--------|
| 1 | `python fase0_prueba.py` | 2–3 min | Yes | Test with 4 clubs (optional, demo only) |
| 2 | `python fase1_descargas.py` | 1–2 min | Yes | Match results 2010–2027 |
| 3 | `python fase1_clubes_temporada.py` | seconds | No | `clubes_temporada.csv` |
| 4 | `python fase1_sociedades.py` | 5–8 min | Yes | Company candidates |
| 5 | `python fase1_sociedades_pendientes.py` | 1–2 min | Yes | Candidates for the difficult cases |
| 6 | `python fase1_sociedades_cierre.py` | < 1 min | Yes | Advanced search and chain of control |
| 7 | `python fase1_sociedades_antiguas.py` | ~1 min | Yes | Companies renamed after bankruptcies |
| 8 | `python fase2_inventario_cuentas.py` | 10–15 min | Yes | Inventory of accounts |

> **Important:** `mapa_sociedades.csv` **is not generated automatically by any script.** It is the result of reviewing the candidates from steps 4–7 (with the reasoning in the `nota` column). It is already included in the repository, so **to reproduce phase 2 you only need to run step 8.**

**OCR of a scanned PDF (optional):**

```bash
python ocr_rapido.py path/to/file.pdf             # 1. fast OCR of the whole PDF
python localizar_paginas.py path/to/ocr_rapido/... # 2. finds the key pages
python ocr_selectivo.py path/to/file.pdf 14,15     # 3. fine OCR of those pages
```

### 7.7 Common problems

| Problem | Cause | Solution |
|---------|-------|----------|
| `FileNotFoundError: api-premier-key.text` | You have not created the key file or you are in another folder | Create the file and run the scripts from the project folder (`cd premierleague`) |
| Error `401` | Wrong key, with spaces, or created as a type other than REST | Check the file; if needed, create a new key |
| Error `429` | Too many requests | The script waits on its own; if it stops, run it again |
| `WinError 10060` on Transfermarkt | Your network cannot reach that server | Not essential; ignore it |
| `ModuleNotFoundError: bs4` | Missing library | `pip install beautifulsoup4` |
| Warning `LF will be replaced by CRLF` when running `git add` | Line-ending difference between Windows and Linux | Harmless. To remove it: `git config core.autocrlf true` |
| `tesseract` or `pdftoppm` not found | Not installed or not in the PATH | See step 4 |

---

## 8. Design decisions and lessons learned

1. **Public data only.** Anyone can reproduce the work, and it does not depend on any club agreeing to collaborate.
2. **Club company as the main unit and group as secondary.** Premier League and EFL rules look at the club *and its group*, so both are stored.
3. **A club can have several companies over time.** The map has one row per club *and period* (e.g. Derby: old company until 2022 and new one from 2024).
4. **Include the clubs that went bust** to avoid survivorship bias.
5. **"Without sanctions" league tables.** Sporting points are calculated without deducting sanctions; sanctions will be added as a separate variable, because they are exactly what we want to explain.
6. **Rules are parameters, not code.** Financial rules change almost every season, so they are stored in configuration so they can be updated without redoing the analysis.
7. **The Premier League and the Championship are the core; UEFA is secondary.** UEFA rules only affect clubs playing in Europe and are used as context.
8. **Step-by-step automation.** Each step is a short, resumable script that saves its result as CSV, so unclear cases can be reviewed by hand.

---

## 9. Known limitations

- **Abbreviated accounts.** Some small clubs (Doncaster, Scunthorpe, Wycombe, Yeovil) file reduced accounts with few figures.
- **Foreign parent companies.** The accounts of Manchester United plc (Cayman Islands) and of Birmingham's parent company (Hong Kong) are not in Companies House.
- **Scanned PDFs.** Many large clubs file images; OCR works but every figure has to be validated.
- **Different layouts.** Each club presents its income statement with a different layout (e.g. Everton uses six columns), and standardising it is part of the phase 2 work.
- **Amended accounts (AAMD).** Some accounts are re-filed with corrections and appear twice; they still need to be filtered out when calculating delays.
- **European competitions.** The European participation table is pending because the planned source (Transfermarkt) is not reachable from every network.

---

## 10. Glossary

| Term | Meaning |
|------|---------|
| **Administration** | British insolvency procedure. In English football it carries a points deduction. |
| **Companies House** | The UK companies register. Every company files its annual accounts there. |
| **iXBRL** | Digital accounts format in which every figure carries a machine-readable tag. |
| **OCR** | Optical character recognition: converts an image of text into text. |
| **PSC** | *Persons with Significant Control*: public register of who controls each company. |
| **Charges** | Loans or debts secured on the company's assets. |
| **Going concern** | If the auditors or directors doubt that the company can keep operating, they must say so in the accounts. |
| **PSR** | Premier League *Profitability and Sustainability Rules* (2016–2026): maximum loss of £105m over three years. |
| **P&S** | The equivalent EFL rules: maximum loss of £39m over three years in the Championship. |
| **SCR** | *Squad Cost Ratio*: squad spending capped at a percentage of revenue. In force in the Premier League and the Championship from 2026/27. |
| **SSR** | *Sustainability and Systemic Resilience*: Premier League liquidity and solvency tests from 2026/27. |
| **IFR** | *Independent Football Regulator*: the independent regulator of English football. |
| **DebtRank / Eisenberg-Noe** | Models that simulate how losses spread through a network of debts. |
| **SHAP** | Method that explains which variables drive each prediction of a model. |

---

## 11. Sources

- **Companies House API:** <https://developer.company-information.service.gov.uk/>
- **Football-Data.co.uk:** historical results, <https://www.football-data.co.uk/>
- **Premier League Handbook:** financial rules for each season.
- **EFL Regulations:** Championship rules.
- **Deloitte Annual Review of Football Finance.**
- Academic literature: Szymanski; Plumley, Wilson and Ramchandani; Alaminos and Fernández; Eisenberg and Noe (2001); Battiston et al. (DebtRank, 2012).

---

*Independent research project. Not affiliated with the Premier League, the EFL, UEFA or any club.*

"""
FASE 2c - OCR de todas las cuentas en PDF (pensado para dejarlo de noche).

Para cada PDF descargado por fase2_descarga_cuentas.py:
  1. Pasada RAPIDA de todas las paginas (110 ppp): sirve para localizar.
     Si una pagina ya trae texto digital, se usa ese texto y no se hace OCR.
  2. LOCALIZA las paginas clave por palabras (resultados, balance, flujos de caja,
     acreedores, deudores, personal, intangibles, going concern, partes
     vinculadas, informe del auditor).
  3. Pasada FINA (300 ppp) solo de esas paginas: de ahi saldran las cifras.

Usa varios nucleos a la vez y es reanudable (si se corta, se relanza y sigue).

Entrada : C:\\datos_premier\\cuentas   (o la carpeta que pases como 1er argumento)
Salida  : C:\\datos_premier\\ocr\\<numero>\\<documento>\\
              rapido\\pag_NNN.txt, fino\\pag_NNN.txt, paginas_clave.json, hecho.json

Uso:
  python fase2_ocr_nocturno.py --comprobar   comprueba que Tesseract y Poppler funcionan
  python fase2_ocr_nocturno.py --prueba      procesa 2 PDF y estima el tiempo total
  python fase2_ocr_nocturno.py               procesa todo (varias horas)
"""
import json, os, re, shutil, subprocess, sys, tempfile, time
from multiprocessing import Pool, cpu_count
from pathlib import Path
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
ORIGEN = Path(ARGS[0]) if ARGS else Path(r"C:\datos_premier\cuentas")
DESTINO = ORIGEN.parent / "ocr"
MAX_FINAS = 18          # maximo de paginas en alta resolucion por documento

REGLAS = {
    "resultados": [r"profit and loss account|income statement|statement of comprehensive income", r"turnover|revenue"],
    "balance": [r"balance sheet", r"net (current )?(assets|liabilities)|total equity|shareholders"],
    "flujos_caja": [r"cash ?flow", r"operating activities"],
    "acreedores": [r"creditors", r"registration|transfer fee|players"],
    "deudores": [r"debtors", r"registration|transfer fee|players"],
    "personal": [r"staff costs|wages and salaries|employee"],
    "intangibles": [r"intangible", r"registration|player"],
    "continuidad": [r"going concern"],
    "partes_vinculadas": [r"related part"],
    "auditor": [r"independent auditor"],
}

# --- localizar programas (PATH, instalacion de conda o rutas tipicas de Windows)
def preparar_path():
    extra = [r"C:\Program Files\Tesseract-OCR", r"C:\Program Files (x86)\Tesseract-OCR"]
    for raiz in [Path(r"C:\poppler"), Path(r"C:\Program Files\poppler")]:
        if raiz.exists():
            extra += [str(p.parent) for p in raiz.rglob("pdftoppm.exe")]
    conda = Path(sys.prefix) / "Library" / "bin"
    extra.append(str(conda))
    os.environ["PATH"] = os.pathsep.join(extra + [os.environ.get("PATH", "")])
    os.environ["OMP_THREAD_LIMIT"] = "1"   # 1 hilo por proceso: el paralelismo lo ponemos nosotros

def comprobar():
    ok = True
    for prog in ["tesseract", "pdftoppm", "pdfinfo", "pdftotext"]:
        ruta = shutil.which(prog)
        print(f"  {prog:10s} {'OK  ' + ruta if ruta else 'NO ENCONTRADO'}")
        ok &= bool(ruta)
    if ok:
        v = subprocess.run(["tesseract", "--version"], capture_output=True, text=True)
        print("  ", (v.stdout or v.stderr).splitlines()[0])
    return ok

def run(cmd):
    flags = 0x08000000 if os.name == "nt" else 0   # sin ventanas emergentes en Windows
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", creationflags=flags)

def n_paginas(pdf):
    for l in run(["pdfinfo", str(pdf)]).stdout.splitlines():
        if l.startswith("Pages:"):
            return int(l.split()[1])
    return 0

def ocr_pagina(pdf, p, dpi, psm):
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp) / "img"
        run(["pdftoppm", "-r", str(dpi), "-gray", "-f", str(p), "-l", str(p), "-png",
             "-singlefile", str(pdf), str(base)])
        return run(["tesseract", f"{base}.png", "stdout", "--psm", str(psm)]).stdout

def procesar(pdf):
    t0 = time.time()
    out = DESTINO / pdf.parent.name / pdf.stem
    if (out / "hecho.json").exists():
        return pdf.name, 0, 0, 0.0, "ya hecho"
    (out / "rapido").mkdir(parents=True, exist_ok=True)
    (out / "fino").mkdir(exist_ok=True)
    try:
        n = n_paginas(pdf)
        digitales = 0
        textos = {}
        for p in range(1, n + 1):
            f = out / "rapido" / f"pag_{p:03d}.txt"
            if f.exists():
                textos[p] = f.read_text(encoding="utf-8"); continue
            t = run(["pdftotext", "-layout", "-f", str(p), "-l", str(p), str(pdf), "-"]).stdout
            if len(t.strip()) > 200:
                digitales += 1
                (out / "fino" / f"pag_{p:03d}.txt").write_text(t, encoding="utf-8")
            else:
                t = ocr_pagina(pdf, p, 110, 3)
            f.write_text(t, encoding="utf-8"); textos[p] = t
        clave = {}
        for p, t in textos.items():
            tl = t.lower()
            for cat, pats in REGLAS.items():
                if all(re.search(x, tl) for x in pats):
                    clave.setdefault(cat, []).append(p)
        (out / "paginas_clave.json").write_text(json.dumps(clave, indent=1), encoding="utf-8")
        finas = sorted({p for ps in clave.values() for p in ps})
        # prioridad: estados principales primero si hay demasiadas
        if len(finas) > MAX_FINAS:
            orden = ["resultados", "balance", "flujos_caja", "acreedores", "deudores",
                     "personal", "intangibles", "continuidad", "partes_vinculadas", "auditor"]
            sel = []
            for c in orden:
                for p in clave.get(c, []):
                    if p not in sel and len(sel) < MAX_FINAS:
                        sel.append(p)
            finas = sorted(sel)
        for p in finas:
            f = out / "fino" / f"pag_{p:03d}.txt"
            if not f.exists():
                f.write_text(ocr_pagina(pdf, p, 300, 6), encoding="utf-8")
        seg = time.time() - t0
        (out / "hecho.json").write_text(json.dumps(
            {"pdf": str(pdf), "paginas": n, "digitales": digitales, "finas": finas,
             "segundos": round(seg, 1)}, indent=1), encoding="utf-8")
        return pdf.name, n, len(finas), seg, "ok"
    except Exception as e:
        return pdf.name, 0, 0, time.time() - t0, f"ERROR {e}"

def main():
    preparar_path()
    if "--comprobar" in sys.argv:
        print("Comprobando programas:")
        print("Todo listo." if comprobar() else "\nFalta algo: revisa la instalacion.")
        return
    if not comprobar():
        sys.exit("\nFaltan programas. Ejecuta primero: python fase2_ocr_nocturno.py --comprobar")
    pdfs = sorted(ORIGEN.rglob("*.pdf"))
    if not pdfs:
        sys.exit(f"No hay PDF en {ORIGEN}. Ejecuta antes fase2_descarga_cuentas.py")
    pendientes = [p for p in pdfs if not (DESTINO / p.parent.name / p.stem / "hecho.json").exists()]
    if "--prueba" in sys.argv:
        pendientes = pendientes[:2]
    nucleos = max(1, cpu_count() - 2)
    print(f"\n{len(pdfs)} PDF en total, {len(pendientes)} pendientes. Usando {nucleos} procesos.")
    print(f"Resultados en {DESTINO}\n")
    t0, hechos, pags, suma = time.time(), 0, 0, 0.0
    with Pool(nucleos) as pool:
        for nombre, n, nf, seg, estado in pool.imap_unordered(procesar, pendientes):
            hechos += 1; pags += n; suma += seg
            transc = time.time() - t0
            resto = transc / hechos * (len(pendientes) - hechos) / 3600
            print(f"[{hechos}/{len(pendientes)}] {nombre}: {n} pag, {nf} finas, "
                  f"{seg:.0f}s {estado} | quedan ~{resto:.1f} h", flush=True)
    total_h = (time.time() - t0) / 3600
    print(f"\nListo: {hechos} documentos, {pags} paginas en {total_h:.2f} h")
    if "--prueba" in sys.argv and hechos:
        n_total = len([p for p in pdfs if not (DESTINO / p.parent.name / p.stem / "hecho.json").exists()])
        print(f"Estimacion para los {n_total} restantes: ~{suma/hechos*n_total/nucleos/3600:.1f} h "
              f"(aprox., en paralelo)")

if __name__ == "__main__":
    main()

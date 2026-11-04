"""
FASE 2c-bis - OCR complementario tras la auditoria.

La auditoria mostro que la primera localizacion de paginas no reconocia los titulos
modernos (Statement of financial position, Statement of profit or loss...) y que el
tope de 18 paginas dejo fuera paginas clave. Este script:
  1. vuelve a localizar las paginas con las reglas nuevas (fase2_reglas.py) usando el
     OCR rapido ya hecho (no repite esa pasada);
  2. guarda la nueva localizacion en paginas_clave_v2.json;
  3. pasa en alta calidad (300 ppp) SOLO las paginas que aun no lo estaban.

Entrada/salida: C:\\datos_premier\\ocr\\<numero>\\<documento>\\ (y los PDF de C:\\datos_premier\\cuentas)
Uso:
  python fase2_ocr_complemento.py --prueba   (5 documentos)
  python fase2_ocr_complemento.py            (todo; se puede relanzar y continua)
"""
import json, sys, time
from multiprocessing import Pool, cpu_count
from pathlib import Path

import fase2_ocr_nocturno as N      # reutiliza deteccion de programas y OCR de pagina
import fase2_reglas as R

ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
CUENTAS = Path(ARGS[0]) if ARGS else Path(r"C:\datos_premier\cuentas")
OCR = CUENTAS.parent / "ocr"

def procesar(doc):
    t0 = time.time()
    if (doc / "hecho_v2.json").exists():
        return doc.name, 0, 0.0, "ya hecho"
    try:
        pdf = CUENTAS / doc.parent.name / f"{doc.name}.pdf"
        textos = {int(f.stem.split("_")[1]): f.read_text(encoding="utf-8", errors="replace")
                  for f in (doc / "rapido").glob("pag_*.txt")}
        loc, cons = R.localizar(textos)
        (doc / "paginas_clave_v2.json").write_text(json.dumps(
            {"paginas": loc, "consolidadas": sorted(p for p, c in cons.items() if c)}, indent=1), encoding="utf-8")
        nuevas = 0
        paginas = sorted({p for ps in loc.values() for p in ps})
        # para resultados y balance se anade tambien la pagina siguiente (estados que ocupan 2 paginas)
        for tipo in ("resultados", "balance"):
            for p in loc.get(tipo, [])[:1]:
                if p + 1 in textos:
                    paginas.append(p + 1)
        for p in sorted(set(paginas)):
            f = doc / "fino" / f"pag_{p:03d}.txt"
            if not f.exists():
                f.parent.mkdir(exist_ok=True)
                f.write_text(N.ocr_pagina(pdf, p, 300, 6), encoding="utf-8")
                nuevas += 1
        (doc / "hecho_v2.json").write_text(json.dumps({"nuevas": nuevas, "segundos": round(time.time() - t0, 1)}), encoding="utf-8")
        return doc.name, nuevas, time.time() - t0, "ok"
    except Exception as e:
        return doc.name, 0, time.time() - t0, f"ERROR {e}"

def main():
    N.preparar_path()
    if not N.comprobar():
        sys.exit("Faltan programas (Tesseract/Poppler).")
    docs = sorted(h.parent for h in OCR.glob("*/*/hecho.json"))
    pend = [d for d in docs if not (d / "hecho_v2.json").exists()]
    if "--prueba" in sys.argv:
        pend = pend[:5]
    nuc = max(1, cpu_count() - 2)
    print(f"\n{len(docs)} documentos, {len(pend)} pendientes. {nuc} procesos.\n")
    t0, n, tot = time.time(), 0, 0
    with Pool(nuc) as pool:
        for nombre, nuevas, seg, estado in pool.imap_unordered(procesar, pend):
            n += 1; tot += nuevas
            resto = (time.time() - t0) / n * (len(pend) - n) / 60
            print(f"[{n}/{len(pend)}] {nombre}: {nuevas} paginas nuevas, {seg:.0f}s {estado} | quedan ~{resto:.0f} min", flush=True)
    print(f"\nListo: {n} documentos, {tot} paginas nuevas en alta calidad, {(time.time()-t0)/60:.1f} min")

if __name__ == "__main__":
    main()

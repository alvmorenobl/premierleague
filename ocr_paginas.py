"""
OCR de cuentas escaneadas (PDF de imagenes) -> un .txt por pagina.
Reanudable: si una pagina ya tiene .txt, la salta.
Requiere: pdftoppm (poppler) y tesseract instalados.
Uso: python ocr_paginas.py ruta1.pdf [ruta2.pdf ...]
"""
import subprocess, sys, tempfile
from pathlib import Path

def n_paginas(pdf):
    out = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout
    for l in out.splitlines():
        if l.startswith("Pages:"):
            return int(l.split()[1])
    return 0

def ocr_pdf(pdf: Path, dpi=250):
    destino = pdf.parent.parent / "ocr" / pdf.stem
    destino.mkdir(parents=True, exist_ok=True)
    n = n_paginas(pdf)
    for p in range(1, n + 1):
        txt = destino / f"pag_{p:03d}.txt"
        if txt.exists():
            continue
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "img"
            subprocess.run(["pdftoppm", "-r", str(dpi), "-f", str(p), "-l", str(p), "-png",
                            "-singlefile", str(pdf), str(base)], check=True,
                           stderr=subprocess.DEVNULL)
            # --psm 6: bloque de texto uniforme, conserva bien las filas de las tablas
            r = subprocess.run(["tesseract", f"{base}.png", "stdout", "--psm", "6"],
                               capture_output=True, text=True)
            txt.write_text(r.stdout, encoding="utf-8")
        print(f"{pdf.name} pagina {p}/{n}", flush=True)
    print(f"HECHO {pdf}", flush=True)

if __name__ == "__main__":
    for ruta in sys.argv[1:]:
        ocr_pdf(Path(ruta))

"""
OCR rapido a baja resolucion (solo para localizar paginas clave). Reanudable.
Uso: python ocr_rapido.py archivo.pdf [...]
"""
import subprocess, sys, tempfile
from pathlib import Path

def n_paginas(pdf):
    for l in subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout.splitlines():
        if l.startswith("Pages:"):
            return int(l.split()[1])
    return 0

for ruta in sys.argv[1:]:
    pdf = Path(ruta)
    destino = pdf.parent.parent / "ocr_rapido" / pdf.stem
    destino.mkdir(parents=True, exist_ok=True)
    for p in range(1, n_paginas(pdf) + 1):
        txt = destino / f"pag_{p:03d}.txt"
        if txt.exists():
            continue
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "img"
            subprocess.run(["pdftoppm", "-r", "110", "-gray", "-f", str(p), "-l", str(p), "-png",
                            "-singlefile", str(pdf), str(base)], check=True, stderr=subprocess.DEVNULL)
            r = subprocess.run(["tesseract", f"{base}.png", "stdout", "--psm", "3"],
                               capture_output=True, text=True)
            txt.write_text(r.stdout, encoding="utf-8")
    print("HECHO", pdf, flush=True)

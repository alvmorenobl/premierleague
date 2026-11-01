"""
OCR de alta calidad solo de las paginas indicadas.
Uso: python ocr_selectivo.py archivo.pdf 14,15,19
"""
import subprocess, sys, tempfile
from pathlib import Path
pdf = Path(sys.argv[1]); paginas = [int(x) for x in sys.argv[2].split(",")]
destino = pdf.parent.parent / "ocr" / pdf.stem
destino.mkdir(parents=True, exist_ok=True)
for p in paginas:
    txt = destino / f"pag_{p:03d}.txt"
    if txt.exists() and txt.stat().st_size > 0:
        continue
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp) / "img"
        subprocess.run(["pdftoppm", "-r", "300", "-gray", "-f", str(p), "-l", str(p), "-png",
                        "-singlefile", str(pdf), str(base)], check=True, stderr=subprocess.DEVNULL)
        r = subprocess.run(["tesseract", f"{base}.png", "stdout", "--psm", "6"], capture_output=True, text=True)
        txt.write_text(r.stdout, encoding="utf-8")
    print("ok", pdf.stem, p, flush=True)

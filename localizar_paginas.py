"""
Localiza las paginas clave de unas cuentas a partir del OCR rapido.
Uso: python localizar_paginas.py carpeta_ocr_rapido
"""
import json, re, sys
from pathlib import Path

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
}

def clasificar(carpeta: Path):
    res = {}
    for txt in sorted(carpeta.glob("pag_*.txt")):
        t = txt.read_text(encoding="utf-8").lower()
        p = int(txt.stem.split("_")[1])
        for cat, patrones in REGLAS.items():
            if all(re.search(pt, t) for pt in patrones):
                res.setdefault(cat, []).append(p)
    return res

if __name__ == "__main__":
    for c in sys.argv[1:]:
        r = clasificar(Path(c))
        print(c); print(json.dumps(r))
        (Path(c) / "paginas_clave.json").write_text(json.dumps(r, indent=1))

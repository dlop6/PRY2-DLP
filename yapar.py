"""CLI principal de YAPar.

Uso:
    python yapar.py parser.yalp -l lexer.yal -o theparser.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Agregar src/ al path para importar los módulos del proyecto
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from codeGenerator import generateParserFile
from lr0Visualizer import generateLr0Diagram
from slrGenerator import (
    SLRConflictError,
    augmentGrammar,
    buildGotoTable,
    buildLr0States,
    buildSlrParserTable,
)
from yalexReader import validateTokensInYalex
from yalpReader import YAParError, parseYalp


def _buildArgParser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="yapar",
        description="Generador de parsers SLR a partir de archivos .yalp",
    )
    ap.add_argument("yalp_file", nargs="?", default=None, help="Archivo .yalp")
    ap.add_argument("-l", "--lexer", default=None, help="Archivo lexer .yal")
    ap.add_argument("-o", "--output", default=None, help="Archivo de salida (.py)")
    return ap


def main(argv: list[str] | None = None) -> int:
    ap = _buildArgParser()
    args = ap.parse_args(argv)

    if not args.yalp_file:
        print("Error: debe especificar un archivo .yalp.")
        return 1
    if not args.lexer:
        print("Error: debe especificar el lexer con -l lexer.yal.")
        return 1
    if not args.output:
        print("Error: debe especificar el archivo de salida con -o nombre_salida.")
        return 1

    # 1. Leer y validar gramática
    try:
        grammar = parseYalp(args.yalp_file)
    except YAParError as exc:
        print(str(exc))
        return 1
    except FileNotFoundError:
        print(f"Error: no se encontró el archivo '{args.yalp_file}'.")
        return 1

    # 2. Validar que los tokens del .yalp estén también en el .yal
    tokenErrors = validateTokensInYalex(grammar.tokens, args.lexer)
    if tokenErrors:
        for err in tokenErrors:
            print(err)
        return 1

    # 3. Construir tabla SLR
    try:
        table = buildSlrParserTable(grammar)
    except SLRConflictError as exc:
        print(str(exc))
        print("La gramática no es SLR. No se generó parser.")
        return 1

    # 4. Generar diagrama LR(0)
    aug = augmentGrammar(grammar)
    states = buildLr0States(aug)
    gotoTable = buildGotoTable(aug, states)
    outputBase = Path(args.output).with_suffix("")
    diagramPath = str(outputBase) + "Lr0.png"
    try:
        generateLr0Diagram(states, gotoTable, diagramPath)
        print(f"Diagrama LR(0) guardado en: {diagramPath}")
    except Exception as exc:  # noqa: BLE001
        print(f"Advertencia: no se pudo generar el diagrama LR(0): {exc}")

    # 5. Generar theparser.py
    generateParserFile(grammar, table, args.output)
    print(f"Parser generado exitosamente: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

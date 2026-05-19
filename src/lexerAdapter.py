"""Adaptador de tokens: formato estándar y funciones de lectura/filtrado.

Formato de token:
    {"type": "TOKEN_1", "lexeme": "valor", "line": 1, "column": 1}

Formato de error léxico:
    {"type": "LEXICAL_ERROR", "lexeme": "@", "line": 2, "column": 4,
     "message": "símbolo no reconocido"}
"""

from __future__ import annotations

LEXICAL_ERROR = "LEXICAL_ERROR"
END_MARKER = "$"


def makeToken(
    tokenType: str,
    lexeme: str,
    line: int = 1,
    column: int = 1,
) -> dict:
    return {"type": tokenType, "lexeme": lexeme, "line": line, "column": column}


def makeLexicalError(
    lexeme: str,
    line: int = 1,
    column: int = 1,
    message: str = "símbolo no reconocido",
) -> dict:
    return {
        "type": LEXICAL_ERROR,
        "lexeme": lexeme,
        "line": line,
        "column": column,
        "message": message,
    }


def filterIgnoredTokens(tokens: list[dict], ignoreTokens: set[str]) -> list[dict]:
    """Elimina tokens cuyo tipo esté en ignoreTokens."""
    return [t for t in tokens if t["type"] not in ignoreTokens]


def tokenizeSimple(path: str, validTokens: set[str]) -> list[dict]:
    """Lee un archivo donde cada palabra es un tipo de token o un lexema desconocido.

    Las palabras que estén en validTokens se producen como tokens válidos.
    Todo lo demás se trata como LEXICAL_ERROR.
    No usa expresiones regulares.
    """
    tokensOut: list[dict] = []
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    for lineNum, rawLine in enumerate(lines, 1):
        pairs = _splitWithColumns(rawLine.rstrip("\n"))
        for word, col in pairs:
            if not word:
                continue
            if word in validTokens:
                tokensOut.append(makeToken(word, word, lineNum, col))
            else:
                tokensOut.append(makeLexicalError(word, lineNum, col))
    return tokensOut


def _splitWithColumns(line: str) -> list[tuple[str, int]]:
    """Divide una línea en (palabra, columna_inicio) sin usar regex."""
    results: list[tuple[str, int]] = []
    i = 0
    n = len(line)
    while i < n:
        if line[i] in (" ", "\t"):
            i += 1
            continue
        start = i
        while i < n and line[i] not in (" ", "\t"):
            i += 1
        results.append((line[start:i], start + 1))
    return results

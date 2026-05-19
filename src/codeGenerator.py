"""Generador de theparser.py: serializa Grammar y ParserTable en un script Python standalone."""

from __future__ import annotations

from grammarModel import Grammar, Production
from slrGenerator import Accept, ParserTable, Reduce, Shift


def generateParserFile(
    grammar: Grammar,
    table: ParserTable,
    outputPath: str,
) -> None:
    """Escribe outputPath con el parser SLR embebido y listo para ejecutarse."""
    code = _buildParserSource(grammar, table)
    with open(outputPath, "w", encoding="utf-8") as f:
        f.write(code)


# ---------------------------------------------------------------------------
# Serialización de tablas
# ---------------------------------------------------------------------------

def _serializeTokens(tokens: set[str]) -> str:
    items = ", ".join(f'"{t}"' for t in sorted(tokens))
    return "{" + items + "}"


def _serializeProductions(productions: list[Production]) -> str:
    lines = []
    for prod in productions:
        right = ", ".join(f'"{s}"' for s in prod.right)
        if prod.right:
            lines.append(f'    ("{prod.left}", ({right},))')
        else:
            lines.append(f'    ("{prod.left}", ())')
    return "[\n" + ",\n".join(lines) + "\n]"


def _serializeAction(action: dict) -> str:
    lines = []
    for (state, token), act in sorted(action.items()):
        if isinstance(act, Shift):
            val = f'("shift", {act.state})'
        elif isinstance(act, Reduce):
            val = f'("reduce", {act.productionIndex})'
        elif isinstance(act, Accept):
            val = '("accept",)'
        else:
            continue
        lines.append(f'    ({state}, "{token}"): {val}')
    return "{\n" + ",\n".join(lines) + "\n}"


def _serializeGoto(goto: dict) -> str:
    lines = []
    for (state, symbol), target in sorted(goto.items()):
        lines.append(f'    ({state}, "{symbol}"): {target}')
    return "{\n" + ",\n".join(lines) + "\n}"


# ---------------------------------------------------------------------------
# Template del parser generado (sin importar nada del proyecto)
# ---------------------------------------------------------------------------

_PARSER_TEMPLATE = '''\
# Parser SLR generado automáticamente por YAPar.
# No modificar manualmente.

TOKENS = {tokens}

IGNORE_TOKENS = {ignoreTokens}

# Producciones: (lhs, (sym1, sym2, ...))
PRODUCTIONS = {productions}

# ACTION[(estado, token)] = ("shift", n) | ("reduce", i) | ("accept",)
ACTION = {action}

# GOTO[(estado, noTerminal)] = estadoDestino
GOTO = {goto}

# ---------------------------------------------------------------------------
# Runtime: tokenizador simple y algoritmo SLR
# ---------------------------------------------------------------------------

_LEXICAL_ERROR = "LEXICAL_ERROR"
_END = "$"


def _splitWithColumns(line):
    """Divide una línea en [(palabra, columna)] sin usar regex."""
    results = []
    i = 0
    n = len(line)
    while i < n:
        if line[i] in (" ", "\\t"):
            i += 1
            continue
        start = i
        while i < n and line[i] not in (" ", "\\t"):
            i += 1
        results.append((line[start:i], start + 1))
    return results


def tokenize(path):
    """Lee el archivo y devuelve lista de tokens."""
    tokensOut = []
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    for lineNum, rawLine in enumerate(lines, 1):
        for word, col in _splitWithColumns(rawLine.rstrip("\\n")):
            if not word:
                continue
            if word in TOKENS:
                tokensOut.append({{"type": word, "lexeme": word, "line": lineNum, "column": col}})
            else:
                tokensOut.append({{
                    "type": _LEXICAL_ERROR,
                    "lexeme": word,
                    "line": lineNum,
                    "column": col,
                    "message": "símbolo no reconocido",
                }})
    return tokensOut


def _filterIgnored(tokens):
    return [t for t in tokens if t["type"] not in IGNORE_TOKENS]


def parse(tokens):
    """Ejecuta el parser SLR. Devuelve True si la entrada es aceptada."""
    tokens = _filterIgnored(tokens)
    inputSeq = list(tokens) + [{{"type": _END, "lexeme": _END, "line": 0, "column": 0}}]
    stack = [0]
    pos = 0

    while True:
        state = stack[-1]
        current = inputSeq[pos]
        tokenType = current["type"]

        if tokenType == _LEXICAL_ERROR:
            line = current.get("line", "?")
            col = current.get("column", "?")
            lexeme = current.get("lexeme", "?")
            detail = current.get("message", "símbolo no reconocido")
            print(f"Error léxico en línea {{line}}, columna {{col}}.")
            print(f"Símbolo: \'{{lexeme}}\'")
            print(f"Detalle: {{detail}}.")
            return False

        action = ACTION.get((state, tokenType))

        if action is None:
            expected = sorted(tok for (s, tok) in ACTION if s == state)
            line = current.get("line", "?")
            col = current.get("column", "?")
            lexeme = current.get("lexeme", tokenType)
            print(f"Error sintáctico en línea {{line}}, columna {{col}}.")
            print(f"Token recibido: {{tokenType}} (\'{{lexeme}}\')")
            if expected:
                print(f"Tokens esperados: {{', '.join(expected)}}.")
            else:
                print("No se esperaban más tokens.")
            return False

        kind = action[0]

        if kind == "shift":
            stack.append(action[1])
            pos += 1

        elif kind == "reduce":
            lhs, rhs = PRODUCTIONS[action[1]]
            n = len(rhs)
            if n > 0:
                del stack[-n:]
            topState = stack[-1]
            gotoState = GOTO.get((topState, lhs))
            if gotoState is None:
                print(f"Error interno: GOTO[{{topState}}, {{lhs}}] no definido.")
                return False
            stack.append(gotoState)

        elif kind == "accept":
            print("Parsing exitoso: entrada aceptada.")
            return True


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Uso: python theparser.py <archivo_entrada>")
        sys.exit(1)

    inputPath = sys.argv[1]
    try:
        tks = tokenize(inputPath)
    except FileNotFoundError:
        print(f"Error: no se encontró el archivo \'{{inputPath}}'.")
        sys.exit(1)

    ok = parse(tks)
    sys.exit(0 if ok else 1)
'''


def _buildParserSource(grammar: Grammar, table: ParserTable) -> str:
    return _PARSER_TEMPLATE.format(
        tokens=_serializeTokens(grammar.tokens),
        ignoreTokens=_serializeTokens(grammar.ignoreTokens),
        productions=_serializeProductions(table.productions),
        action=_serializeAction(table.action),
        goto=_serializeGoto(table.goto),
    )

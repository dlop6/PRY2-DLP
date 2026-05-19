"""Runtime del parser SLR: algoritmo shift/reduce/accept sobre una lista de tokens."""

from __future__ import annotations

from slrGenerator import Accept, ParserTable, Reduce, Shift

END_TOKEN_TYPE = "$"
LEXICAL_ERROR_TYPE = "LEXICAL_ERROR"


def filterIgnoredTokens(tokens: list[dict], ignoreTokens: set[str]) -> list[dict]:
    """Elimina tokens cuyo tipo esté en ignoreTokens."""
    return [t for t in tokens if t["type"] not in ignoreTokens]


def parseTokens(
    tokens: list[dict],
    table: ParserTable,
    ignoreTokens: set[str] | None = None,
) -> bool:
    """Ejecuta el parser SLR sobre la lista de tokens.

    Imprime mensajes en cada situación y devuelve True si la entrada es aceptada.
    """
    if ignoreTokens:
        tokens = filterIgnoredTokens(tokens, ignoreTokens)

    endToken = {
        "type": END_TOKEN_TYPE,
        "lexeme": END_TOKEN_TYPE,
        "line": 0,
        "column": 0,
    }
    inputSeq: list[dict] = list(tokens) + [endToken]

    stack: list[int] = [0]
    pos = 0

    while True:
        state = stack[-1]
        current = inputSeq[pos]
        tokenType = current["type"]

        if tokenType == LEXICAL_ERROR_TYPE:
            line = current.get("line", "?")
            col = current.get("column", "?")
            lexeme = current.get("lexeme", "?")
            detail = current.get("message", "símbolo no reconocido")
            print(f"Error léxico en línea {line}, columna {col}.")
            print(f"Símbolo: '{lexeme}'")
            print(f"Detalle: {detail}.")
            return False

        action = table.action.get((state, tokenType))

        if action is None:
            expected = sorted(
                tok for (s, tok), _ in table.action.items() if s == state
            )
            line = current.get("line", "?")
            col = current.get("column", "?")
            lexeme = current.get("lexeme", tokenType)
            print(f"Error sintáctico en línea {line}, columna {col}.")
            print(f"Token recibido: {tokenType} ('{lexeme}')")
            if expected:
                print(f"Tokens esperados: {', '.join(expected)}.")
            else:
                print("No se esperaban más tokens.")
            return False

        if isinstance(action, Shift):
            stack.append(action.state)
            pos += 1

        elif isinstance(action, Reduce):
            prod = table.productions[action.productionIndex]
            n = len(prod.right)
            if n > 0:
                del stack[-n:]
            topState = stack[-1]
            gotoState = table.goto.get((topState, prod.left))
            if gotoState is None:
                print(f"Error interno: GOTO[{topState}, {prod.left}] no definido.")
                return False
            stack.append(gotoState)

        elif isinstance(action, Accept):
            print("Parsing exitoso: entrada aceptada.")
            return True

"""Lector del archivo YALex (.yal): extrae los nombres de tokens definidos.

Se usa para validar que los tokens declarados en el .yalp también estén
presentes en el lexer correspondiente.

No usa expresiones regulares. Busca el patrón '-> TOKEN_NAME' manualmente.
"""

from __future__ import annotations


def extractYalexTokens(path: str) -> set[str]:
    """Lee un archivo .yal y devuelve el conjunto de nombres de tokens definidos.

    Los tokens se detectan como palabras en MAYÚSCULA que aparecen
    inmediatamente después de '->' en el archivo.
    """
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    content = _removeOcamlComments(content)
    tokens: set[str] = set()
    i = 0
    n = len(content)

    while i < n:
        # Buscar '->'
        pos = content.find("->", i)
        if pos == -1:
            break
        j = pos + 2
        # Saltar espacios y tabulaciones
        while j < n and content[j] in (" ", "\t"):
            j += 1
        # Leer el identificador siguiente
        start = j
        while j < n and (content[j].isalnum() or content[j] == "_"):
            j += 1
        word = content[start:j]
        if word and word[0].isupper() and _isValidTokenName(word):
            tokens.add(word)
        i = pos + 2

    return tokens


def validateTokensInYalex(
    yalpTokens: set[str],
    yalPath: str,
) -> list[str]:
    """Valida que todos los tokens del .yalp estén definidos en el .yal.

    Devuelve lista de mensajes de error (vacía si todo está bien).
    """
    errors: list[str] = []
    try:
        yalexTokens = extractYalexTokens(yalPath)
    except FileNotFoundError:
        return [f"Error: no se encontró el archivo lexer '{yalPath}'."]
    except OSError as exc:
        return [f"Error al leer el lexer: {exc}"]

    for token in sorted(yalpTokens):
        if token not in yalexTokens:
            errors.append(
                f"Error: el token '{token}' está declarado en el archivo YAPar "
                f"pero no está definido en el archivo YALex '{yalPath}'."
            )
    return errors


# ---------------------------------------------------------------------------
# Internos
# ---------------------------------------------------------------------------

def _removeOcamlComments(text: str) -> str:
    """Elimina comentarios OCaml (* ... *) sin usar regex."""
    result: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        if text[i:i + 2] == "(*":
            depth = 1
            i += 2
            while i < n and depth > 0:
                if text[i:i + 2] == "(*":
                    depth += 1
                    i += 2
                elif text[i:i + 2] == "*)":
                    depth -= 1
                    i += 2
                else:
                    i += 1
        else:
            result.append(text[i])
            i += 1
    return "".join(result)


def _isValidTokenName(name: str) -> bool:
    if not name or not name[0].isupper():
        return False
    return all(c.isupper() or c.isdigit() or c == "_" for c in name)

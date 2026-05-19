from grammarModel import Grammar, Production


class YAParError(Exception):
    pass


def _removeComments(text: str) -> str:
    result = []
    i = 0
    while i < len(text):
        start = text.find("/*", i)
        if start == -1:
            result.append(text[i:])
            break
        result.append(text[i:start])
        end = text.find("*/", start + 2)
        if end == -1:
            raise YAParError("Error YAPar: comentario sin cerrar.")
        comment = text[start:end + 2]
        result.append("\n" * comment.count("\n"))
        i = end + 2
    return "".join(result)


def _splitSections(text: str) -> tuple[str, str]:
    parts = text.split("%%")
    if len(parts) < 2:
        raise YAParError("Error YAPar: falta separador %% entre tokens y producciones.")
    if len(parts) > 2:
        raise YAParError("Error YAPar: se encontró más de un separador %%.")
    return parts[0], parts[1]


def _isValidToken(name: str) -> bool:
    if not name:
        return False
    if not name[0].isupper():
        return False
    return all(c.isupper() or c.isdigit() or c == "_" for c in name)


def _parseTokens(tokenSection: str) -> set[str]:
    tokens: set[str] = set()
    for line in tokenSection.splitlines():
        line = line.strip()
        if not line.startswith("%token"):
            continue
        rest = line[len("%token"):].strip()
        if not rest:
            raise YAParError("Error YAPar: declaración %token sin tokens.")
        for name in rest.split():
            if not _isValidToken(name):
                raise YAParError(
                    f"Error YAPar: token inválido '{name}'. Los tokens deben estar en mayúscula."
                )
            if name in tokens:
                raise YAParError(f"Error YAPar: token duplicado '{name}'.")
            tokens.add(name)
    return tokens


def _parseIgnore(tokenSection: str, tokens: set[str]) -> set[str]:
    ignore: set[str] = set()
    for line in tokenSection.splitlines():
        line = line.strip()
        if not line.startswith("IGNORE"):
            continue
        rest = line[len("IGNORE"):].strip()
        if not rest:
            raise YAParError("Error YAPar: declaración IGNORE sin tokens.")
        for name in rest.split():
            if name not in tokens:
                raise YAParError(
                    f"Error YAPar: token ignorado no declarado '{name}'."
                )
            ignore.add(name)
    return ignore


def _parseProductions(prodSection: str) -> list[Production]:
    productions: list[Production] = []
    blocks = prodSection.split(";")
    remaining = blocks[-1].strip()
    if remaining:
        raise YAParError("Error YAPar: producción sin ';'.")

    for block in blocks[:-1]:
        block = block.strip()
        if not block:
            continue
        if ":" not in block:
            raise YAParError("Error YAPar: producción sin ':'.")
        colonIdx = block.index(":")
        head = block[:colonIdx].strip()
        body = block[colonIdx + 1:].strip()
        alternatives = body.split("|")
        for alt in alternatives:
            symbols = alt.strip().split()
            if not symbols:
                raise YAParError("Error YAPar: producción vacía.")
            productions.append(Production(head, tuple(symbols)))

    return productions


def _validateNames(productions: list[Production]) -> None:
    for prod in productions:
        name = prod.left
        if not name[0].islower():
            if name[0].isupper():
                if name.isupper():
                    raise YAParError(
                        f"Error YAPar: nombre de producción inválido '{name}'. "
                        "Los no terminales deben escribirse como identificadores en minúscula."
                    )
                raise YAParError(
                    f"Error YAPar: nombre de producción inválido '{name}'. "
                    "Los no terminales deben iniciar en minúscula."
                )


def _validateSymbols(productions: list[Production], tokens: set[str]) -> None:
    definedNonterminals = {p.left for p in productions}
    for prod in productions:
        for symbol in prod.right:
            if symbol[0].isupper():
                if symbol not in tokens:
                    raise YAParError(
                        f"Error YAPar: token usado pero no declarado '{symbol}'."
                    )
            else:
                if symbol not in definedNonterminals:
                    raise YAParError(
                        f"Error YAPar: no terminal usado pero no definido '{symbol}'."
                    )


def parseYalp(path: str) -> Grammar:
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    text = _removeComments(text)
    tokenSection, prodSection = _splitSections(text)
    tokens = _parseTokens(tokenSection)
    ignoreTokens = _parseIgnore(tokenSection, tokens)
    productions = _parseProductions(prodSection)
    _validateNames(productions)
    _validateSymbols(productions, tokens)

    startSymbol = productions[0].left if productions else ""
    return Grammar(
        tokens=tokens,
        ignoreTokens=ignoreTokens,
        productions=productions,
        startSymbol=startSymbol,
    )

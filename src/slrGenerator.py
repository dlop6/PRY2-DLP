"""Generador de tabla SLR: FIRST, FOLLOW, autómata LR(0) y tablas ACTION/GOTO."""

from __future__ import annotations

from dataclasses import dataclass

from grammarModel import Grammar, Production

EPSILON = "ε"
END_MARKER = "$"


@dataclass(frozen=True)
class Item:
    left: str
    right: tuple[str, ...]
    dot: int


@dataclass
class State:
    id: int
    items: frozenset[Item]


@dataclass(frozen=True)
class Shift:
    state: int


@dataclass(frozen=True)
class Reduce:
    productionIndex: int


@dataclass(frozen=True)
class Accept:
    pass


@dataclass
class ParserTable:
    productions: list[Production]
    action: dict[tuple[int, str], object]
    goto: dict[tuple[int, str], int]


@dataclass(frozen=True)
class SLRConflict:
    state: int
    token: str
    existing: object
    new: object
    kind: str  # "shift/reduce" | "reduce/reduce"


class SLRConflictError(Exception):
    """La gramática no es SLR: hay conflictos en la tabla ACTION."""

    def __init__(
        self,
        conflicts: list[SLRConflict],
        productions: list[Production] | None = None,
    ) -> None:
        self.conflicts = conflicts
        prods = productions or []
        lines = [_formatConflict(c, prods) for c in conflicts]
        super().__init__("\n".join(lines))


def augmentGrammar(grammar: Grammar) -> Grammar:
    """Añade S' -> S como producción 0."""
    augStart = f"{grammar.startSymbol}'"
    augProd = Production(augStart, (grammar.startSymbol,))
    return Grammar(
        tokens=grammar.tokens,
        ignoreTokens=grammar.ignoreTokens,
        productions=[augProd] + list(grammar.productions),
        startSymbol=augStart,
    )


def computeFirst(grammar: Grammar) -> dict[str, set[str]]:
    """Calcula FIRST para terminales y no terminales (soporta ε)."""
    symbols = _allSymbols(grammar)
    first: dict[str, set[str]] = {s: set() for s in symbols}

    for token in grammar.tokens:
        first[token] = {token}

    changed = True
    while changed:
        changed = False
        for prod in grammar.productions:
            left = prod.left
            if not prod.right:
                if EPSILON not in first[left]:
                    first[left].add(EPSILON)
                    changed = True
                continue
            before = len(first[left])
            seqFirst = _firstOfSequence(prod.right, first)
            first[left].update(seqFirst)
            if len(first[left]) != before:
                changed = True

    return first


def computeFollow(grammar: Grammar, first: dict[str, set[str]]) -> dict[str, set[str]]:
    """Calcula FOLLOW para todos los no terminales."""
    nonTerminals = _nonTerminals(grammar)
    follow: dict[str, set[str]] = {nt: set() for nt in nonTerminals}
    follow[grammar.startSymbol].add(END_MARKER)

    changed = True
    while changed:
        changed = False
        for prod in grammar.productions:
            for i, symbol in enumerate(prod.right):
                if symbol not in nonTerminals:
                    continue
                beta = prod.right[i + 1:]
                before = len(follow[symbol])
                if beta:
                    follow[symbol].update(_firstOfSequence(beta, first) - {EPSILON})
                    if EPSILON in _firstOfSequence(beta, first):
                        follow[symbol].update(follow[prod.left])
                else:
                    follow[symbol].update(follow[prod.left])
                if len(follow[symbol]) != before:
                    changed = True
    return follow


def symbolAfterDot(item: Item) -> str | None:
    if item.dot < len(item.right):
        return item.right[item.dot]
    return None


def moveDot(item: Item) -> Item:
    return Item(item.left, item.right, item.dot + 1)


def closure(items: set[Item], grammar: Grammar) -> frozenset[Item]:
    result = set(items)
    nonTerminals = _nonTerminals(grammar)
    changed = True
    while changed:
        changed = False
        for item in list(result):
            symbol = symbolAfterDot(item)
            if symbol is None or symbol not in nonTerminals:
                continue
            for prod in grammar.productions:
                if prod.left != symbol:
                    continue
                newItem = Item(prod.left, prod.right, 0)
                if newItem not in result:
                    result.add(newItem)
                    changed = True
    return frozenset(result)


def goto(items: set[Item], symbol: str, grammar: Grammar) -> frozenset[Item]:
    moved: set[Item] = set()
    for item in items:
        if symbolAfterDot(item) == symbol:
            moved.add(moveDot(item))
    if not moved:
        return frozenset()
    return closure(moved, grammar)


def buildLr0States(grammar: Grammar) -> list[State]:
    """Construye estados LR(0) numerados I0, I1, …"""
    prod0 = grammar.productions[0]
    startItem = Item(prod0.left, prod0.right, 0)
    initialItems = closure({startItem}, grammar)

    stateMap: dict[frozenset[Item], int] = {initialItems: 0}
    states: list[State] = [State(0, initialItems)]
    queue: list[frozenset[Item]] = [initialItems]

    symbols = _lr0Symbols(grammar)

    while queue:
        currentItems = queue.pop(0)
        for symbol in symbols:
            targetItems = goto(set(currentItems), symbol, grammar)
            if not targetItems:
                continue
            if targetItems not in stateMap:
                newId = len(states)
                stateMap[targetItems] = newId
                states.append(State(newId, targetItems))
                queue.append(targetItems)

    return states


def _buildTransitions(
    grammar: Grammar, states: list[State]
) -> dict[tuple[int, str], int]:
    itemsToId = {state.items: state.id for state in states}
    transitions: dict[tuple[int, str], int] = {}
    for state in states:
        for symbol in _lr0Symbols(grammar):
            targetItems = goto(set(state.items), symbol, grammar)
            if targetItems and targetItems in itemsToId:
                transitions[(state.id, symbol)] = itemsToId[targetItems]
    return transitions


def buildActionTable(
    grammar: Grammar,
    states: list[State],
    follow: dict[str, set[str]],
) -> dict[tuple[int, str], object]:
    transitions = _buildTransitions(grammar, states)
    action: dict[tuple[int, str], object] = {}
    conflicts: list[SLRConflict] = []
    augStart = grammar.startSymbol

    for state in states:
        for item in state.items:
            symbol = symbolAfterDot(item)
            if symbol is not None and _isTerminal(symbol, grammar):
                key = (state.id, symbol)
                nextState = transitions.get((state.id, symbol))
                if nextState is None:
                    continue
                newAction: object = Shift(nextState)
                _setAction(action, key, newAction, grammar.productions, conflicts)
                continue

            if symbol is not None:
                continue

            if item.left == augStart:
                key = (state.id, END_MARKER)
                _setAction(action, key, Accept(), grammar.productions, conflicts)
                continue

            prodIdx = _productionIndex(item, grammar.productions)
            for token in follow.get(item.left, set()):
                key = (state.id, token)
                newAction = Reduce(prodIdx)
                _setAction(action, key, newAction, grammar.productions, conflicts)

    if conflicts:
        raise SLRConflictError(conflicts, grammar.productions)
    return action


def buildAllTransitions(grammar: Grammar, states: list[State]) -> dict[tuple[int, str], int]:
    """Todas las transiciones del autómata: terminales Y no-terminales."""
    return _buildTransitions(grammar, states)


def buildGotoTable(grammar: Grammar, states: list[State]) -> dict[tuple[int, str], int]:
    transitions = _buildTransitions(grammar, states)
    nonTerminals = _nonTerminals(grammar)
    gotoTable: dict[tuple[int, str], int] = {}
    for (stateId, symbol), targetId in transitions.items():
        if symbol in nonTerminals:
            gotoTable[(stateId, symbol)] = targetId
    return gotoTable


def buildSlrParserTable(grammar: Grammar) -> ParserTable:
    """Pipeline completo SLR. Lanza SLRConflictError si la gramática no es SLR."""
    aug = augmentGrammar(grammar)
    first = computeFirst(aug)
    follow = computeFollow(aug, first)
    states = buildLr0States(aug)
    action = buildActionTable(aug, states, follow)
    gotoTable = buildGotoTable(aug, states)
    return ParserTable(
        productions=list(aug.productions),
        action=action,
        goto=gotoTable,
    )


# --- Formato legible ---


def formatFirst(first: dict[str, set[str]], symbol: str) -> str:
    values = sorted(first.get(symbol, set()), key=_symbolSortKey)
    inner = ", ".join(values)
    return f"FIRST({symbol}) = {{ {inner} }}"


def formatFollow(follow: dict[str, set[str]], symbol: str) -> str:
    values = sorted(follow.get(symbol, set()), key=_symbolSortKey)
    inner = ", ".join(values)
    return f"FOLLOW({symbol}) = {{ {inner} }}"


def formatState(state: State) -> str:
    lines = [f"I{state.id}:"]
    for item in sorted(state.items, key=_itemSortKey):
        lines.append(f"  {_formatItem(item)}")
    return "\n".join(lines)


def formatActionEntry(state: int, token: str, action: object, productions: list[Production]) -> str:
    return f"ACTION[{state}, {token}] = {_formatAction(action, productions)}"


def formatGotoEntry(state: int, symbol: str, target: int) -> str:
    return f"GOTO[{state}, {symbol}] = {target}"


# --- Internos ---


def _isTerminal(symbol: str, grammar: Grammar) -> bool:
    return symbol in grammar.tokens


def _nonTerminals(grammar: Grammar) -> set[str]:
    return {p.left for p in grammar.productions}


def _allSymbols(grammar: Grammar) -> set[str]:
    symbols = set(grammar.tokens) | _nonTerminals(grammar)
    for prod in grammar.productions:
        symbols.update(prod.right)
    return symbols


def _lr0Symbols(grammar: Grammar) -> list[str]:
    symbols: set[str] = set()
    for prod in grammar.productions:
        symbols.update(prod.right)
    return sorted(symbols, key=_symbolSortKey)


def _firstOfSequence(symbols: tuple[str, ...], first: dict[str, set[str]]) -> set[str]:
    result: set[str] = set()
    for symbol in symbols:
        result.update(first.get(symbol, {symbol}) - {EPSILON})
        if EPSILON not in first.get(symbol, set()):
            return result
    result.add(EPSILON)
    return result


def _productionIndex(item: Item, productions: list[Production]) -> int:
    for i, prod in enumerate(productions):
        if prod.left == item.left and prod.right == item.right:
            return i
    raise ValueError(f"Producción no encontrada para item {item}")


def _setAction(
    table: dict[tuple[int, str], object],
    key: tuple[int, str],
    newAction: object,
    productions: list[Production],
    conflicts: list[SLRConflict],
) -> None:
    if key not in table:
        table[key] = newAction
        return
    existing = table[key]
    if existing == newAction:
        return
    kind = _conflictKind(existing, newAction)
    conflicts.append(
        SLRConflict(state=key[0], token=key[1], existing=existing, new=newAction, kind=kind)
    )


def _conflictKind(existing: object, new: object) -> str:
    if isinstance(existing, Shift) or isinstance(new, Shift):
        return "shift/reduce"
    return "reduce/reduce"


def _formatConflict(conflict: SLRConflict, productions: list[Production]) -> str:
    existingStr = _formatAction(conflict.existing, productions)
    newStr = _formatAction(conflict.new, productions)
    return (
        f"Conflicto {conflict.kind} en estado {conflict.state} con token {conflict.token}.\n"
        f"Acción existente: {existingStr}\n"
        f"Nueva acción: {newStr}"
    )


def _formatAction(action: object, productions: list[Production]) -> str:
    if isinstance(action, Shift):
        return f"shift {action.state}"
    if isinstance(action, Reduce):
        if productions and 0 <= action.productionIndex < len(productions):
            prod = productions[action.productionIndex]
            rhs = " ".join(prod.right) if prod.right else EPSILON
            return f"reduce {prod.left} -> {rhs}"
        return f"reduce production {action.productionIndex}"
    if isinstance(action, Accept):
        return "accept"
    return repr(action)


def _formatItem(item: Item) -> str:
    if not item.right:
        dotDisplay = f"· {EPSILON}"
    else:
        parts = list(item.right)
        dotPos = item.dot
        before = " ".join(parts[:dotPos])
        after = " ".join(parts[dotPos:])
        if before and after:
            dotDisplay = f"{before} · {after}"
        elif before:
            dotDisplay = f"{before} ·"
        elif after:
            dotDisplay = f"· {after}"
        else:
            dotDisplay = "·"
    return f"{item.left} -> {dotDisplay}"


def _itemSortKey(item: Item) -> tuple:
    return (item.left, item.right, item.dot)


def _symbolSortKey(symbol: str) -> tuple:
    order = {END_MARKER: 0, EPSILON: 1}
    return (order.get(symbol, 2), symbol)

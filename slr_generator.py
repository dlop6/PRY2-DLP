"""Generador de tabla SLR: FIRST, FOLLOW, autómata LR(0) y tablas ACTION/GOTO."""

from __future__ import annotations

from dataclasses import dataclass

from grammar import Grammar, Production

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
    production_index: int


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
        lines = [_format_conflict(c, prods) for c in conflicts]
        super().__init__("\n".join(lines))


def augment_grammar(grammar: Grammar) -> Grammar:
    """Añade S' -> S como producción 0."""
    aug_start = f"{grammar.start_symbol}'"
    aug_prod = Production(aug_start, (grammar.start_symbol,))
    return Grammar(
        tokens=grammar.tokens,
        ignore_tokens=grammar.ignore_tokens,
        productions=[aug_prod] + list(grammar.productions),
        start_symbol=aug_start,
    )


def compute_first(grammar: Grammar) -> dict[str, set[str]]:
    """Calcula FIRST para terminales y no terminales (soporta ε)."""
    symbols = _all_symbols(grammar)
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
            seq_first = _first_of_sequence(prod.right, first)
            first[left].update(seq_first)
            if len(first[left]) != before:
                changed = True

    return first


def compute_follow(grammar: Grammar, first: dict[str, set[str]]) -> dict[str, set[str]]:
    """Calcula FOLLOW para todos los no terminales."""
    non_terminals = _non_terminals(grammar)
    follow: dict[str, set[str]] = {nt: set() for nt in non_terminals}
    follow[grammar.start_symbol].add(END_MARKER)

    changed = True
    while changed:
        changed = False
        for prod in grammar.productions:
            for i, symbol in enumerate(prod.right):
                if symbol not in non_terminals:
                    continue
                beta = prod.right[i + 1 :]
                before = len(follow[symbol])
                if beta:
                    follow[symbol].update(_first_of_sequence(beta, first) - {EPSILON})
                    if EPSILON in _first_of_sequence(beta, first):
                        follow[symbol].update(follow[prod.left])
                else:
                    follow[symbol].update(follow[prod.left])
                if len(follow[symbol]) != before:
                    changed = True
    return follow


def symbol_after_dot(item: Item) -> str | None:
    if item.dot < len(item.right):
        return item.right[item.dot]
    return None


def move_dot(item: Item) -> Item:
    return Item(item.left, item.right, item.dot + 1)


def closure(items: set[Item], grammar: Grammar) -> frozenset[Item]:
    result = set(items)
    non_terminals = _non_terminals(grammar)
    changed = True
    while changed:
        changed = False
        for item in list(result):
            symbol = symbol_after_dot(item)
            if symbol is None or symbol not in non_terminals:
                continue
            for prod in grammar.productions:
                if prod.left != symbol:
                    continue
                new_item = Item(prod.left, prod.right, 0)
                if new_item not in result:
                    result.add(new_item)
                    changed = True
    return frozenset(result)


def goto(items: set[Item], symbol: str, grammar: Grammar) -> frozenset[Item]:
    moved: set[Item] = set()
    for item in items:
        if symbol_after_dot(item) == symbol:
            moved.add(move_dot(item))
    if not moved:
        return frozenset()
    return closure(moved, grammar)


def build_lr0_states(grammar: Grammar) -> list[State]:
    """Construye estados LR(0) numerados I0, I1, …"""
    prod0 = grammar.productions[0]
    start_item = Item(prod0.left, prod0.right, 0)
    initial_items = closure({start_item}, grammar)

    state_map: dict[frozenset[Item], int] = {initial_items: 0}
    states: list[State] = [State(0, initial_items)]
    queue: list[frozenset[Item]] = [initial_items]

    symbols = _lr0_symbols(grammar)

    while queue:
        current_items = queue.pop(0)
        for symbol in symbols:
            target_items = goto(set(current_items), symbol, grammar)
            if not target_items:
                continue
            if target_items not in state_map:
                new_id = len(states)
                state_map[target_items] = new_id
                states.append(State(new_id, target_items))
                queue.append(target_items)

    return states


def _build_transitions(
    grammar: Grammar, states: list[State]
) -> dict[tuple[int, str], int]:
    items_to_id = {state.items: state.id for state in states}
    transitions: dict[tuple[int, str], int] = {}
    for state in states:
        for symbol in _lr0_symbols(grammar):
            target_items = goto(set(state.items), symbol, grammar)
            if target_items and target_items in items_to_id:
                transitions[(state.id, symbol)] = items_to_id[target_items]
    return transitions


def build_action_table(
    grammar: Grammar,
    states: list[State],
    follow: dict[str, set[str]],
) -> dict[tuple[int, str], object]:
    transitions = _build_transitions(grammar, states)
    action: dict[tuple[int, str], object] = {}
    conflicts: list[SLRConflict] = []
    aug_start = grammar.start_symbol

    for state in states:
        for item in state.items:
            symbol = symbol_after_dot(item)
            if symbol is not None and _is_terminal(symbol, grammar):
                key = (state.id, symbol)
                next_state = transitions.get((state.id, symbol))
                if next_state is None:
                    continue
                new_action: object = Shift(next_state)
                _set_action(action, key, new_action, grammar.productions, conflicts)
                continue

            if symbol is not None:
                continue

            if item.left == aug_start:
                key = (state.id, END_MARKER)
                _set_action(action, key, Accept(), grammar.productions, conflicts)
                continue

            prod_index = _production_index(item, grammar.productions)
            for token in follow.get(item.left, set()):
                key = (state.id, token)
                new_action = Reduce(prod_index)
                _set_action(action, key, new_action, grammar.productions, conflicts)

    if conflicts:
        raise SLRConflictError(conflicts, grammar.productions)
    return action


def build_goto_table(grammar: Grammar, states: list[State]) -> dict[tuple[int, str], int]:
    transitions = _build_transitions(grammar, states)
    non_terminals = _non_terminals(grammar)
    goto_table: dict[tuple[int, str], int] = {}
    for (state_id, symbol), target_id in transitions.items():
        if symbol in non_terminals:
            goto_table[(state_id, symbol)] = target_id
    return goto_table


def build_slr_parser_table(grammar: Grammar) -> ParserTable:
    """Pipeline completo SLR. Lanza SLRConflictError si la gramática no es SLR."""
    aug = augment_grammar(grammar)
    first = compute_first(aug)
    follow = compute_follow(aug, first)
    states = build_lr0_states(aug)
    action = build_action_table(aug, states, follow)
    goto_table = build_goto_table(aug, states)
    return ParserTable(
        productions=list(aug.productions),
        action=action,
        goto=goto_table,
    )


# --- Formato legible ---


def format_first(first: dict[str, set[str]], symbol: str) -> str:
    values = sorted(first.get(symbol, set()), key=_symbol_sort_key)
    inner = ", ".join(values)
    return f"FIRST({symbol}) = {{ {inner} }}"


def format_follow(follow: dict[str, set[str]], symbol: str) -> str:
    values = sorted(follow.get(symbol, set()), key=_symbol_sort_key)
    inner = ", ".join(values)
    return f"FOLLOW({symbol}) = {{ {inner} }}"


def format_state(state: State) -> str:
    lines = [f"I{state.id}:"]
    for item in sorted(state.items, key=_item_sort_key):
        lines.append(f"  {_format_item(item)}")
    return "\n".join(lines)


def format_action_entry(state: int, token: str, action: object, productions: list[Production]) -> str:
    return f"ACTION[{state}, {token}] = {_format_action(action, productions)}"


def format_goto_entry(state: int, symbol: str, target: int) -> str:
    return f"GOTO[{state}, {symbol}] = {target}"


# --- Internos ---


def _is_terminal(symbol: str, grammar: Grammar) -> bool:
    return symbol in grammar.tokens


def _non_terminals(grammar: Grammar) -> set[str]:
    return {p.left for p in grammar.productions}


def _all_symbols(grammar: Grammar) -> set[str]:
    symbols = set(grammar.tokens) | _non_terminals(grammar)
    for prod in grammar.productions:
        symbols.update(prod.right)
    return symbols


def _lr0_symbols(grammar: Grammar) -> list[str]:
    symbols: set[str] = set()
    for prod in grammar.productions:
        symbols.update(prod.right)
    return sorted(symbols, key=_symbol_sort_key)


def _first_of_sequence(symbols: tuple[str, ...], first: dict[str, set[str]]) -> set[str]:
    result: set[str] = set()
    for symbol in symbols:
        result.update(first.get(symbol, {symbol}) - {EPSILON})
        if EPSILON not in first.get(symbol, set()):
            return result
    result.add(EPSILON)
    return result


def _production_index(item: Item, productions: list[Production]) -> int:
    for i, prod in enumerate(productions):
        if prod.left == item.left and prod.right == item.right:
            return i
    raise ValueError(f"Producción no encontrada para item {item}")


def _set_action(
    table: dict[tuple[int, str], object],
    key: tuple[int, str],
    new_action: object,
    productions: list[Production],
    conflicts: list[SLRConflict],
) -> None:
    if key not in table:
        table[key] = new_action
        return
    existing = table[key]
    if existing == new_action:
        return
    kind = _conflict_kind(existing, new_action)
    conflicts.append(
        SLRConflict(state=key[0], token=key[1], existing=existing, new=new_action, kind=kind)
    )


def _conflict_kind(existing: object, new: object) -> str:
    if isinstance(existing, Shift) or isinstance(new, Shift):
        return "shift/reduce"
    return "reduce/reduce"


def _format_conflict(conflict: SLRConflict, productions: list[Production]) -> str:
    existing_s = _format_action(conflict.existing, productions)
    new_s = _format_action(conflict.new, productions)
    return (
        f"Conflicto {conflict.kind} en estado {conflict.state} con token {conflict.token}.\n"
        f"Acción existente: {existing_s}\n"
        f"Nueva acción: {new_s}"
    )


def _format_action(action: object, productions: list[Production]) -> str:
    if isinstance(action, Shift):
        return f"shift {action.state}"
    if isinstance(action, Reduce):
        if productions and 0 <= action.production_index < len(productions):
            prod = productions[action.production_index]
            rhs = " ".join(prod.right) if prod.right else EPSILON
            return f"reduce {prod.left} -> {rhs}"
        return f"reduce production {action.production_index}"
    if isinstance(action, Accept):
        return "accept"
    return repr(action)


def _format_item(item: Item) -> str:
    if not item.right:
        before, after = "", ""
        dot_display = f"· {EPSILON}"
    else:
        parts = list(item.right)
        dot_pos = item.dot
        before = " ".join(parts[:dot_pos])
        after = " ".join(parts[dot_pos:])
        if before and after:
            dot_display = f"{before} · {after}"
        elif before:
            dot_display = f"{before} ·"
        elif after:
            dot_display = f"· {after}"
        else:
            dot_display = "·"
    return f"{item.left} -> {dot_display}"


def _item_sort_key(item: Item) -> tuple:
    return (item.left, item.right, item.dot)


def _symbol_sort_key(symbol: str) -> tuple:
    order = {END_MARKER: 0, EPSILON: 1}
    return (order.get(symbol, 2), symbol)

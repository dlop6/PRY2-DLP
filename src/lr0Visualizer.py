"""Visualización del autómata LR(0) con Graphviz o matplotlib (respaldo)."""

from __future__ import annotations

import shutil
from collections import deque
from dataclasses import dataclass
from pathlib import Path

from slrGenerator import State, _symbolSortKey

# Tipo alias para claridad
_Transitions = dict[tuple[int, str], int]


@dataclass(frozen=True)
class DiagramResult:
    path: Path
    engine: str  # "graphviz" | "matplotlib"


def isGraphvizAvailable() -> bool:
    """True si el ejecutable `dot` de Graphviz está en el PATH."""
    return shutil.which("dot") is not None


def generateLr0Diagram(
    states: list[State],
    gotoTable: _Transitions,
    outputPath: str,
    allTransitions: _Transitions | None = None,
    augStart: str | None = None,
) -> DiagramResult:
    """Genera PNG o PDF.

    allTransitions: transiciones completas (terminales + no-terminales).
    Si se proporciona, mejora el layout y muestra todas las aristas.
    Si no, usa gotoTable como antes (retrocompatible).
    """
    path = Path(outputPath)
    fmt = "pdf" if path.suffix.lower() == ".pdf" else "png"
    # Para el layout usamos allTransitions si está disponible
    layoutTrans = allTransitions if allTransitions is not None else gotoTable

    if fmt == "pdf" and not isGraphvizAvailable():
        raise RuntimeError(
            "La exportación PDF requiere Graphviz instalado en el sistema.\n"
            "Windows: winget install Graphviz.Graphviz\n"
            "Luego reinicie la terminal o Cursor."
        )

    if isGraphvizAvailable():
        try:
            out = _renderGraphviz(states, gotoTable, path, fmt, layoutTrans, augStart)
            return DiagramResult(path=out, engine="graphviz")
        except ImportError:
            pass  # binario presente pero paquete Python graphviz no instalado

    if fmt == "pdf":
        raise RuntimeError(
            "PDF no disponible sin Graphviz instalado.\n"
            "Windows: winget install Graphviz.Graphviz\n"
            "Luego: pip install graphviz"
        )
    out = _renderMatplotlib(states, gotoTable, path, layoutTrans, augStart)
    return DiagramResult(path=out, engine="matplotlib")


def buildLr0DotSource(
    states: list[State],
    gotoTable: _Transitions,
    augStart: str | None = None,
) -> str:
    """Devuelve el código DOT (útil sin binario Graphviz)."""
    return _buildDot(states, gotoTable, augStart).source


def _renderGraphviz(
    states: list[State],
    gotoTable: _Transitions,
    path: Path,
    fmt: str,
    layoutTrans: _Transitions,
    augStart: str | None = None,
) -> Path:
    dot = _buildDot(states, layoutTrans, augStart)
    base = str(path.with_suffix(""))
    dot.render(base, format=fmt, cleanup=True)
    return Path(f"{base}.{fmt}")


def _renderMatplotlib(
    states: list[State],
    gotoTable: _Transitions,
    path: Path,
    layoutTrans: _Transitions,
    augStart: str | None = None,
) -> Path:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import networkx as nx
    except ImportError as exc:
        raise ImportError(
            "Sin Graphviz en el PATH. Instálelo (winget install Graphviz.Graphviz) "
            "o instale el respaldo: pip install matplotlib networkx"
        ) from exc

    # Grafo con TODAS las transiciones para layout preciso
    graph = nx.DiGraph()
    for state in states:
        graph.add_node(state.id)
    # Aristas: usamos layoutTrans (que puede incluir terminales)
    for (src, symbol), dst in layoutTrans.items():
        graph.add_edge(src, dst, label=symbol)

    pos = _bfsLayout(states, layoutTrans)

    # Cálculo de tamaño basado en span real del grafo
    if pos:
        xs = [x for x, _ in pos.values()]
        ys = [y for _, y in pos.values()]
        spanX = max(xs) - min(xs) + 1
        spanY = max(ys) - min(ys) + 1
    else:
        spanX, spanY = 1, 1
    figW = min(36, max(10, spanX * 3.0))
    figH = min(40, max(8, spanY * 3.0))

    _, ax = plt.subplots(figsize=(figW, figH), facecolor="#1a1a1a")
    ax.set_facecolor("#1a1a1a")

    nodeSize = max(800, min(1800, int(10000 / max(len(states), 1))))
    acceptStates = _acceptStateIds(states, augStart)
    nodeColors = [
        "#2ecc71" if n in acceptStates else ("#3498db" if n == 0 else "#34495e")
        for n in graph.nodes()
    ]
    nx.draw_networkx_nodes(
        graph, pos, ax=ax, node_color=nodeColors,
        node_size=nodeSize, edgecolors="white", linewidths=2,
    )
    nx.draw_networkx_labels(
        graph, pos,
        labels={n: f"I{n}" for n in graph.nodes()},
        font_color="white", font_size=max(7, 11 - len(states) // 3),
        font_weight="bold", ax=ax,
    )
    nx.draw_networkx_edges(
        graph, pos, ax=ax, edge_color="#95a5a6",
        arrows=True, arrowsize=20, connectionstyle="arc3,rad=0.1",
        min_source_margin=nodeSize ** 0.5 * 0.6,
        min_target_margin=nodeSize ** 0.5 * 0.6,
    )
    # Mostrar etiquetas de aristas (símbolos de transición)
    edgeLabels = {(u, v): d.get("label", "") for u, v, d in graph.edges(data=True)}
    nx.draw_networkx_edge_labels(
        graph, pos, edge_labels=edgeLabels,
        font_color="#f1c40f", font_size=max(6, 9 - len(states) // 5), ax=ax,
        bbox={"boxstyle": "round,pad=0.2", "facecolor": "#2a2a2a", "edgecolor": "none"},
    )
    ax.axis("off")
    ax.margins(0.15)
    plt.tight_layout(pad=1.5)
    out = path if path.suffix.lower() == ".png" else path.with_suffix(".png")
    plt.savefig(out, dpi=130, facecolor="#1a1a1a", bbox_inches="tight")
    plt.close()
    return out


def _bfsLayout(
    states: list[State],
    transitions: _Transitions,
) -> dict[int, tuple[float, float]]:
    """BFS layout usando las transiciones dadas (pueden ser todas o solo GOTO)."""
    levels: dict[int, int] = {0: 0}
    queue: deque[int] = deque([0])
    while queue:
        current = queue.popleft()
        for (src, _symbol), dst in transitions.items():
            if src == current and dst not in levels:
                levels[dst] = levels[current] + 1
                queue.append(dst)

    # Distribuir estados no alcanzados según su vecino más cercano alcanzado
    maxLevel = max(levels.values(), default=0)
    unvisited = [s.id for s in states if s.id not in levels]

    # Para cada estado no visitado, intentar inferir su nivel
    # por el estado desde el que se alcanza (buscando en transitions)
    for sid in unvisited:
        parentLevel = None
        for (src, _sym), dst in transitions.items():
            if dst == sid and src in levels:
                candidateLevel = levels[src] + 1
                if parentLevel is None or candidateLevel < parentLevel:
                    parentLevel = candidateLevel
        levels[sid] = parentLevel if parentLevel is not None else maxLevel + 1

    byLevel: dict[int, list[int]] = {}
    for node, level in levels.items():
        byLevel.setdefault(level, []).append(node)

    pos: dict[int, tuple[float, float]] = {}
    for level, nodes in sorted(byLevel.items()):
        nodes.sort()
        width = len(nodes)
        for index, node in enumerate(nodes):
            pos[node] = (index - (width - 1) / 2.0, -level)
    return pos


def _buildDot(
    states: list[State],
    layoutTrans: _Transitions,
    augStart: str | None = None,
):
    from graphviz import Digraph

    dot = Digraph("LR0", format="png")
    dot.attr(rankdir="LR", nodesep="0.4", ranksep="0.8")
    dot.attr("node", shape="box", fontname="Consolas", fontsize="10")

    acceptStates = _acceptStateIds(states, augStart)

    for state in states:
        label = _stateLabel(state)
        attrs: dict[str, str] = {}
        if state.id == 0:
            attrs["penwidth"] = "3"
            attrs["color"] = "blue"
        if state.id in acceptStates:
            attrs["style"] = "bold"
            attrs["color"] = "darkgreen"
        dot.node(f"I{state.id}", label=label, **attrs)

    if states:
        dot.node("start", label="", shape="point", width="0.1")
        dot.edge("start", "I0", style="bold")

    seenEdges: set[tuple[int, str, int]] = set()
    for (src, symbol), dst in sorted(
        layoutTrans.items(), key=lambda e: (e[0][0], _symbolSortKey(e[0][1]))
    ):
        edge = (src, symbol, dst)
        if edge in seenEdges:
            continue
        seenEdges.add(edge)
        dot.edge(f"I{src}", f"I{dst}", label=symbol)

    return dot


def _stateLabel(state: State) -> str:
    lines = [f"I{state.id}:"]
    from slrGenerator import _formatItem, _itemSortKey
    for item in sorted(state.items, key=_itemSortKey):
        lines.append(_formatItem(item))
    return "\\n".join(lines)


def _acceptStateIds(states: list[State], augStart: str | None = None) -> set[int]:
    accept: set[int] = set()
    for state in states:
        for item in state.items:
            if item.dot != len(item.right):
                continue
            if augStart is not None:
                if item.left == augStart:
                    accept.add(state.id)
            else:
                if item.left.endswith("'"):  # fallback cuando no se conoce augStart
                    accept.add(state.id)
    return accept

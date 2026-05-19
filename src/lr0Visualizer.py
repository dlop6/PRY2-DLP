"""Visualización del autómata LR(0) con Graphviz o matplotlib (respaldo)."""

from __future__ import annotations

import shutil
from collections import deque
from dataclasses import dataclass
from pathlib import Path

from slrGenerator import State, _symbolSortKey


@dataclass(frozen=True)
class DiagramResult:
    path: Path
    engine: str  # "graphviz" | "matplotlib"


def isGraphvizAvailable() -> bool:
    """True si el ejecutable `dot` de Graphviz está en el PATH."""
    return shutil.which("dot") is not None


def generateLr0Diagram(
    states: list[State],
    gotoTable: dict[tuple[int, str], int],
    outputPath: str,
) -> DiagramResult:
    """Genera PNG o PDF. Usa Graphviz si está instalado; si no, matplotlib."""
    path = Path(outputPath)
    fmt = "pdf" if path.suffix.lower() == ".pdf" else "png"
    if fmt == "pdf" and not isGraphvizAvailable():
        raise RuntimeError(
            "La exportación PDF requiere Graphviz instalado en el sistema.\n"
            "Windows: winget install Graphviz.Graphviz\n"
            "Luego reinicie la terminal o Cursor."
        )

    if isGraphvizAvailable():
        out = _renderGraphviz(states, gotoTable, path, fmt)
        return DiagramResult(path=out, engine="graphviz")

    if fmt == "pdf":
        raise RuntimeError("PDF no disponible sin Graphviz.")
    out = _renderMatplotlib(states, gotoTable, path)
    return DiagramResult(path=out, engine="matplotlib")


def buildLr0DotSource(
    states: list[State],
    gotoTable: dict[tuple[int, str], int],
) -> str:
    """Devuelve el código DOT (útil sin binario Graphviz)."""
    return _buildDot(states, gotoTable).source


def _renderGraphviz(
    states: list[State],
    gotoTable: dict[tuple[int, str], int],
    path: Path,
    fmt: str,
) -> Path:
    dot = _buildDot(states, gotoTable)
    base = str(path.with_suffix(""))
    dot.render(base, format=fmt, cleanup=True)
    return Path(f"{base}.{fmt}")


def _renderMatplotlib(
    states: list[State],
    gotoTable: dict[tuple[int, str], int],
    path: Path,
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

    graph = nx.DiGraph()
    for state in states:
        graph.add_node(state.id)
    for (src, _symbol), dst in gotoTable.items():
        graph.add_edge(src, dst, label=_symbol)

    pos = _bfsLayout(states, gotoTable)
    figW = max(10, len(states) * 1.2)
    figH = max(6, len(states) * 0.5)
    _, ax = plt.subplots(figsize=(figW, figH), facecolor="#1a1a1a")
    ax.set_facecolor("#1a1a1a")

    acceptStates = _acceptStateIds(states)
    nodeColors = [
        "#2ecc71" if n in acceptStates else ("#3498db" if n == 0 else "#34495e")
        for n in graph.nodes()
    ]
    nx.draw_networkx_nodes(
        graph, pos, ax=ax, node_color=nodeColors,
        node_size=2200, edgecolors="white", linewidths=2,
    )
    nx.draw_networkx_labels(
        graph, pos,
        labels={n: f"I{n}" for n in graph.nodes()},
        font_color="white", font_size=9, font_weight="bold", ax=ax,
    )
    nx.draw_networkx_edges(
        graph, pos, ax=ax, edge_color="#95a5a6",
        arrows=True, arrowsize=16, connectionstyle="arc3,rad=0.08",
    )
    edgeLabels = {(u, v): d.get("label", "") for u, v, d in graph.edges(data=True)}
    nx.draw_networkx_edge_labels(
        graph, pos, edge_labels=edgeLabels,
        font_color="#f1c40f", font_size=8, ax=ax,
    )
    ax.axis("off")
    plt.tight_layout()
    out = path if path.suffix.lower() == ".png" else path.with_suffix(".png")
    plt.savefig(out, dpi=120, facecolor="#1a1a1a", bbox_inches="tight")
    plt.close()
    return out


def _bfsLayout(
    states: list[State],
    gotoTable: dict[tuple[int, str], int],
) -> dict[int, tuple[float, float]]:
    levels: dict[int, int] = {0: 0}
    queue: deque[int] = deque([0])
    while queue:
        current = queue.popleft()
        for (src, _symbol), dst in gotoTable.items():
            if src == current and dst not in levels:
                levels[dst] = levels[current] + 1
                queue.append(dst)

    maxLevel = max(levels.values(), default=0)
    for state in states:
        if state.id not in levels:
            levels[state.id] = maxLevel + 1

    byLevel: dict[int, list[int]] = {}
    for node, level in levels.items():
        byLevel.setdefault(level, []).append(node)

    pos: dict[int, tuple[float, float]] = {}
    for level, nodes in sorted(byLevel.items()):
        nodes.sort()
        width = len(nodes)
        for index, node in enumerate(nodes):
            pos[node] = (index - (width - 1) / 2, -level)
    return pos


def _buildDot(states: list[State], gotoTable: dict[tuple[int, str], int]):
    from graphviz import Digraph

    dot = Digraph("LR0", format="png")
    dot.attr(rankdir="LR", nodesep="0.4", ranksep="0.8")
    dot.attr("node", shape="box", fontname="Consolas", fontsize="10")

    acceptStates = _acceptStateIds(states)

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
        gotoTable.items(), key=lambda e: (e[0][0], _symbolSortKey(e[0][1]))
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


def _acceptStateIds(states: list[State]) -> set[int]:
    accept: set[int] = set()
    for state in states:
        for item in state.items:
            if item.dot == len(item.right) and item.left.endswith("'"):
                accept.add(state.id)
    return accept

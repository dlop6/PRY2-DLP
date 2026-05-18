"""Visualización del autómata LR(0) con Graphviz o matplotlib (respaldo)."""

from __future__ import annotations

import shutil
from collections import deque
from dataclasses import dataclass
from pathlib import Path

from slr_generator import State, _symbol_sort_key


@dataclass(frozen=True)
class DiagramResult:
    path: Path
    engine: str  # "graphviz" | "matplotlib"


def is_graphviz_available() -> bool:
    """True si el ejecutable `dot` de Graphviz está en el PATH."""
    return shutil.which("dot") is not None


def generate_lr0_diagram(
    states: list[State],
    goto_table: dict[tuple[int, str], int],
    output_path: str,
) -> DiagramResult:
    """Genera PNG o PDF. Usa Graphviz si está instalado; si no, matplotlib."""
    path = Path(output_path)
    fmt = "pdf" if path.suffix.lower() == ".pdf" else "png"
    if fmt == "pdf" and not is_graphviz_available():
        raise RuntimeError(
            "La exportación PDF requiere Graphviz instalado en el sistema.\n"
            "Windows: winget install Graphviz.Graphviz\n"
            "Luego reinicie la terminal o Cursor."
        )

    if is_graphviz_available():
        out = _render_graphviz(states, goto_table, path, fmt)
        return DiagramResult(path=out, engine="graphviz")

    if fmt == "pdf":
        raise RuntimeError("PDF no disponible sin Graphviz.")
    out = _render_matplotlib(states, goto_table, path)
    return DiagramResult(path=out, engine="matplotlib")


def build_lr0_dot_source(
    states: list[State],
    goto_table: dict[tuple[int, str], int],
) -> str:
    """Devuelve el código DOT (útil sin binario Graphviz)."""
    return _build_dot(states, goto_table).source


def _render_graphviz(
    states: list[State],
    goto_table: dict[tuple[int, str], int],
    path: Path,
    fmt: str,
) -> Path:
    dot = _build_dot(states, goto_table)
    base = str(path.with_suffix(""))
    dot.render(base, format=fmt, cleanup=True)
    return Path(f"{base}.{fmt}")


def _render_matplotlib(
    states: list[State],
    goto_table: dict[tuple[int, str], int],
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
    for (src, _symbol), dst in goto_table.items():
        graph.add_edge(src, dst, label=_symbol)

    pos = _bfs_layout(states, goto_table)
    fig_w = max(10, len(states) * 1.2)
    fig_h = max(6, len(states) * 0.5)
    _, ax = plt.subplots(figsize=(fig_w, fig_h), facecolor="#1a1a1a")
    ax.set_facecolor("#1a1a1a")

    accept_states = _accept_state_ids(states)
    node_colors = [
        "#2ecc71" if n in accept_states else ("#3498db" if n == 0 else "#34495e")
        for n in graph.nodes()
    ]
    nx.draw_networkx_nodes(
        graph,
        pos,
        ax=ax,
        node_color=node_colors,
        node_size=2200,
        edgecolors="white",
        linewidths=2,
    )
    nx.draw_networkx_labels(
        graph,
        pos,
        labels={n: f"I{n}" for n in graph.nodes()},
        font_color="white",
        font_size=9,
        font_weight="bold",
        ax=ax,
    )
    nx.draw_networkx_edges(
        graph,
        pos,
        ax=ax,
        edge_color="#95a5a6",
        arrows=True,
        arrowsize=16,
        connectionstyle="arc3,rad=0.08",
    )
    edge_labels = {
        (u, v): d.get("label", "") for u, v, d in graph.edges(data=True)
    }
    nx.draw_networkx_edge_labels(
        graph,
        pos,
        edge_labels=edge_labels,
        font_color="#f1c40f",
        font_size=8,
        ax=ax,
    )
    ax.axis("off")
    plt.tight_layout()
    out = path if path.suffix.lower() == ".png" else path.with_suffix(".png")
    plt.savefig(out, dpi=120, facecolor="#1a1a1a", bbox_inches="tight")
    plt.close()
    return out


def _bfs_layout(
    states: list[State],
    goto_table: dict[tuple[int, str], int],
) -> dict[int, tuple[float, float]]:
    levels: dict[int, int] = {0: 0}
    queue: deque[int] = deque([0])
    while queue:
        current = queue.popleft()
        for (src, _symbol), dst in goto_table.items():
            if src == current and dst not in levels:
                levels[dst] = levels[current] + 1
                queue.append(dst)

    max_level = max(levels.values(), default=0)
    for state in states:
        if state.id not in levels:
            levels[state.id] = max_level + 1

    by_level: dict[int, list[int]] = {}
    for node, level in levels.items():
        by_level.setdefault(level, []).append(node)

    pos: dict[int, tuple[float, float]] = {}
    for level, nodes in sorted(by_level.items()):
        nodes.sort()
        width = len(nodes)
        for index, node in enumerate(nodes):
            pos[node] = (index - (width - 1) / 2, -level)
    return pos


def _build_dot(states: list[State], goto_table: dict[tuple[int, str], int]):
    from graphviz import Digraph

    dot = Digraph("LR0", format="png")
    dot.attr(rankdir="LR", nodesep="0.4", ranksep="0.8")
    dot.attr("node", shape="box", fontname="Consolas", fontsize="10")

    accept_states = _accept_state_ids(states)

    for state in states:
        label = _state_label(state)
        attrs: dict[str, str] = {}
        if state.id == 0:
            attrs["penwidth"] = "3"
            attrs["color"] = "blue"
        if state.id in accept_states:
            attrs["style"] = "bold"
            attrs["color"] = "darkgreen"
        dot.node(f"I{state.id}", label=label, **attrs)

    if states:
        dot.node("start", label="", shape="point", width="0.1")
        dot.edge("start", "I0", style="bold")

    seen_edges: set[tuple[int, str, int]] = set()
    for (src, symbol), dst in sorted(
        goto_table.items(), key=lambda e: (e[0][0], _symbol_sort_key(e[0][1]))
    ):
        edge = (src, symbol, dst)
        if edge in seen_edges:
            continue
        seen_edges.add(edge)
        dot.edge(f"I{src}", f"I{dst}", label=symbol)

    return dot


def _state_label(state: State) -> str:
    lines = [f"I{state.id}:"]
    from slr_generator import _format_item, _item_sort_key

    for item in sorted(state.items, key=_item_sort_key):
        lines.append(_format_item(item))
    return "\\n".join(lines)


def _accept_state_ids(states: list[State]) -> set[int]:
    accept: set[int] = set()
    for state in states:
        for item in state.items:
            if item.dot == len(item.right) and item.left.endswith("'"):
                accept.add(state.id)
    return accept

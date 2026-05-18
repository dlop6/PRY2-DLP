"""Interfaz gráfica YAPar con CustomTkinter."""

from __future__ import annotations

import tempfile
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk
from PIL import Image

from grammar import Grammar
from lr0_visualizer import generate_lr0_diagram, is_graphviz_available
from slr_generator import (
    ParserTable,
    SLRConflictError,
    augment_grammar,
    build_goto_table,
    build_lr0_states,
    build_slr_parser_table,
    compute_first,
    compute_follow,
    format_action_entry,
    format_first,
    format_follow,
    format_goto_entry,
    format_state,
)
from yalp_reader import YAParError, parse_yalp

PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_YALP_DIR = PROJECT_ROOT / "tests" / "yalp" / "fixtures"


class YAParApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("YAPar — Generador SLR")
        self.geometry("1100x720")
        self.minsize(900, 600)

        self._yalp_path: Path | None = None
        self._grammar: Grammar | None = None
        self._table: ParserTable | None = None
        self._diagram_path: Path | None = None
        self._ctk_image: ctk.CTkImage | None = None

        self._build_layout()
        self._set_status("Abra un archivo .yalp para comenzar.")

    def _build_layout(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_rowconfigure(6, weight=1)

        ctk.CTkLabel(
            sidebar,
            text="YAPar",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).grid(row=0, column=0, padx=20, pady=(24, 4), sticky="w")

        ctk.CTkLabel(
            sidebar,
            text="Generador SLR",
            font=ctk.CTkFont(size=13),
            text_color="gray70",
        ).grid(row=1, column=0, padx=20, pady=(0, 20), sticky="w")

        ctk.CTkButton(
            sidebar, text="Abrir .yalp", command=self._open_yalp
        ).grid(row=2, column=0, padx=16, pady=6, sticky="ew")

        ctk.CTkButton(
            sidebar,
            text="Analizar gramática",
            command=self._analyze,
            fg_color="#1f6aa5",
        ).grid(row=3, column=0, padx=16, pady=6, sticky="ew")

        ctk.CTkButton(
            sidebar,
            text="Guardar diagrama",
            command=self._save_diagram,
        ).grid(row=4, column=0, padx=16, pady=6, sticky="ew")

        self._file_label = ctk.CTkLabel(
            sidebar,
            text="Sin archivo",
            font=ctk.CTkFont(size=11),
            text_color="gray60",
            wraplength=180,
            justify="left",
        )
        self._file_label.grid(row=5, column=0, padx=16, pady=(12, 8), sticky="nw")

        ctk.CTkLabel(
            sidebar,
            text="v1.0 · CustomTkinter",
            font=ctk.CTkFont(size=10),
            text_color="gray50",
        ).grid(row=7, column=0, padx=16, pady=16, sticky="sw")

        main = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        main.grid(row=0, column=1, sticky="nsew", padx=(0, 8), pady=8)
        main.grid_rowconfigure(1, weight=1)
        main.grid_columnconfigure(0, weight=1)

        self._status = ctk.CTkLabel(
            main,
            text="",
            anchor="w",
            font=ctk.CTkFont(size=12),
        )
        self._status.grid(row=0, column=0, sticky="ew", padx=4, pady=(0, 8))

        self._tabs = ctk.CTkTabview(main)
        self._tabs.grid(row=1, column=0, sticky="nsew")
        self._tabs.add("Gramática")
        self._tabs.add("FIRST / FOLLOW")
        self._tabs.add("Estados LR(0)")
        self._tabs.add("Tablas")
        self._tabs.add("Autómata")

        self._text_grammar = self._make_textbox(self._tabs.tab("Gramática"))
        self._text_sets = self._make_textbox(self._tabs.tab("FIRST / FOLLOW"))
        self._text_states = self._make_textbox(self._tabs.tab("Estados LR(0)"))
        self._text_tables = self._make_textbox(self._tabs.tab("Tablas"))

        automaton_tab = self._tabs.tab("Autómata")
        automaton_tab.grid_rowconfigure(0, weight=1)
        automaton_tab.grid_columnconfigure(0, weight=1)

        self._diagram_frame = ctk.CTkScrollableFrame(automaton_tab)
        self._diagram_frame.grid(row=0, column=0, sticky="nsew")
        self._diagram_label = ctk.CTkLabel(
            self._diagram_frame,
            text="El diagrama LR(0) aparecerá aquí tras analizar una gramática SLR válida.",
            font=ctk.CTkFont(size=13),
            text_color="gray65",
        )
        self._diagram_label.pack(expand=True, padx=20, pady=40)

    def _make_textbox(self, parent: ctk.CTkFrame) -> ctk.CTkTextbox:
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        box = ctk.CTkTextbox(parent, font=ctk.CTkFont(family="Consolas", size=13))
        box.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        box.configure(state="disabled")
        return box

    def _set_status(self, message: str, *, error: bool = False) -> None:
        color = "#e74c3c" if error else "gray80"
        self._status.configure(text=message, text_color=color)

    def _open_yalp(self) -> None:
        initial = str(DEFAULT_YALP_DIR) if DEFAULT_YALP_DIR.is_dir() else str(PROJECT_ROOT)
        path = filedialog.askopenfilename(
            title="Abrir archivo YAPar",
            initialdir=initial,
            filetypes=[("YAPar", "*.yalp"), ("Todos", "*.*")],
        )
        if not path:
            return
        self._yalp_path = Path(path)
        self._file_label.configure(text=self._yalp_path.name)
        self._set_status(f"Archivo cargado: {self._yalp_path.name}")
        self._grammar = None
        self._table = None
        self._clear_diagram()
        self._load_grammar_preview()

    def _load_grammar_preview(self) -> None:
        if not self._yalp_path:
            return
        try:
            grammar = parse_yalp(str(self._yalp_path))
        except YAParError as exc:
            self._set_text(self._text_grammar, str(exc))
            self._set_status(str(exc), error=True)
            return
        self._grammar = grammar
        self._set_text(self._text_grammar, _format_grammar_summary(grammar))
        self._set_status("Gramática válida. Pulse «Analizar gramática» para generar SLR.")

    def _analyze(self) -> None:
        if not self._yalp_path:
            messagebox.showwarning("YAPar", "Seleccione primero un archivo .yalp.")
            return
        try:
            grammar = parse_yalp(str(self._yalp_path))
        except YAParError as exc:
            self._set_status(str(exc), error=True)
            messagebox.showerror("Error YAPar", str(exc))
            return

        self._grammar = grammar
        self._set_text(self._text_grammar, _format_grammar_summary(grammar))

        aug = augment_grammar(grammar)
        first = compute_first(aug)
        follow = compute_follow(aug, first)
        states = build_lr0_states(aug)

        self._set_text(self._text_sets, _format_first_follow(aug, first, follow))
        self._set_text(self._text_states, _format_all_states(states))

        try:
            table = build_slr_parser_table(grammar)
        except SLRConflictError as exc:
            self._table = None
            self._set_text(self._text_tables, str(exc))
            self._clear_diagram()
            self._set_status("La gramática no es SLR (conflictos detectados).", error=True)
            messagebox.showerror("No es SLR", str(exc))
            return

        self._table = table
        self._set_text(self._text_tables, _format_tables(table))
        self._set_status("Tabla SLR generada correctamente.")
        self._show_diagram(states, build_goto_table(aug, states))

    def _show_diagram(
        self,
        states: list,
        goto_table: dict[tuple[int, str], int],
    ) -> None:
        self._clear_diagram()
        tmp = Path(tempfile.gettempdir()) / "yapar_lr0.png"
        try:
            result = generate_lr0_diagram(states, goto_table, str(tmp))
        except (ImportError, RuntimeError) as exc:
            self._diagram_label.configure(
                text=(
                    "No se pudo generar el diagrama.\n\n"
                    "Opción A — Graphviz (recomendado):\n"
                    "  winget install Graphviz.Graphviz\n"
                    "  Reinicie Cursor y vuelva a analizar.\n\n"
                    "Opción B — respaldo matplotlib:\n"
                    "  pip install matplotlib networkx\n\n"
                    f"Detalle: {exc}"
                ),
                image=None,
            )
            return

        self._diagram_path = result.path
        if result.engine == "matplotlib":
            self._set_status(
                "Diagrama generado con matplotlib (sin Graphviz en PATH). "
                "Para más detalle en nodos: winget install Graphviz.Graphviz"
            )
        elif not is_graphviz_available():
            self._set_status("Diagrama generado.")
        pil_image = Image.open(result.path)
        max_w = 900
        if pil_image.width > max_w:
            ratio = max_w / pil_image.width
            new_size = (max_w, int(pil_image.height * ratio))
            pil_image = pil_image.resize(new_size, Image.Resampling.LANCZOS)

        size = (pil_image.width, pil_image.height)
        self._ctk_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=size)
        self._diagram_label.configure(text="", image=self._ctk_image)

    def _clear_diagram(self) -> None:
        self._diagram_path = None
        self._ctk_image = None
        self._diagram_label.configure(
            image=None,
            text="El diagrama LR(0) aparecerá aquí tras analizar una gramática SLR válida.",
        )

    def _save_diagram(self) -> None:
        if not self._diagram_path or not self._diagram_path.exists():
            messagebox.showinfo(
                "YAPar",
                "No hay diagrama para guardar. Analice una gramática SLR válida primero.",
            )
            return
        dest = filedialog.asksaveasfilename(
            title="Guardar diagrama LR(0)",
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("PDF", "*.pdf")],
        )
        if not dest:
            return
        try:
            if dest.lower().endswith(".pdf"):
                aug = augment_grammar(self._grammar)  # type: ignore[arg-type]
                states = build_lr0_states(aug)
                goto_table = build_goto_table(aug, states)
                generate_lr0_diagram(states, goto_table, dest)
            else:
                data = self._diagram_path.read_bytes()
                Path(dest).write_bytes(data)
            messagebox.showinfo("YAPar", f"Diagrama guardado en:\n{dest}")
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    @staticmethod
    def _set_text(widget: ctk.CTkTextbox, content: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", content)
        widget.configure(state="disabled")


def _format_grammar_summary(grammar: Grammar) -> str:
    lines = [
        f"Símbolo inicial: {grammar.start_symbol}",
        f"Tokens ({len(grammar.tokens)}): {', '.join(sorted(grammar.tokens))}",
    ]
    if grammar.ignore_tokens:
        lines.append(
            f"IGNORE ({len(grammar.ignore_tokens)}): "
            f"{', '.join(sorted(grammar.ignore_tokens))}"
        )
    lines.append(f"\nProducciones ({len(grammar.productions)}):\n")
    for i, prod in enumerate(grammar.productions):
        rhs = " ".join(prod.right) if prod.right else "ε"
        lines.append(f"  {i}. {prod.left} -> {rhs}")
    return "\n".join(lines)


def _format_first_follow(
    grammar: Grammar,
    first: dict[str, set[str]],
    follow: dict[str, set[str]],
) -> str:
    non_terminals = sorted({p.left for p in grammar.productions})
    lines = ["=== FIRST ===\n"]
    for nt in non_terminals:
        if nt in first:
            lines.append(format_first(first, nt))
    lines.append("\n=== FOLLOW ===\n")
    for nt in non_terminals:
        if nt in follow:
            lines.append(format_follow(follow, nt))
    return "\n".join(lines)


def _format_all_states(states: list) -> str:
    return "\n\n".join(format_state(s) for s in states)


def _format_tables(table: ParserTable) -> str:
    lines = ["=== ACTION ===\n"]
    for (state, token), action in sorted(table.action.items()):
        lines.append(format_action_entry(state, token, action, table.productions))
    lines.append("\n=== GOTO ===\n")
    for (state, symbol), target in sorted(table.goto.items()):
        lines.append(format_goto_entry(state, symbol, target))
    lines.append("\n=== Producciones (aumentadas) ===\n")
    for i, prod in enumerate(table.productions):
        rhs = " ".join(prod.right) if prod.right else "ε"
        lines.append(f"  {i}. {prod.left} -> {rhs}")
    return "\n".join(lines)


def main() -> None:
    app = YAParApp()
    app.mainloop()


if __name__ == "__main__":
    main()

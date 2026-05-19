"""Interfaz gráfica YAPar con CustomTkinter."""

from __future__ import annotations

import tempfile
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk
from PIL import Image

from codeGenerator import generateParserFile
from grammarModel import Grammar
from lexerAdapter import tokenizeSimple
from lr0Visualizer import generateLr0Diagram, isGraphvizAvailable
from parserRuntime import parseTokens
from yalexReader import validateTokensInYalex
from slrGenerator import (
    ParserTable,
    SLRConflictError,
    augmentGrammar,
    buildGotoTable,
    buildLr0States,
    buildSlrParserTable,
    computeFirst,
    computeFollow,
    formatActionEntry,
    formatFirst,
    formatFollow,
    formatGotoEntry,
    formatState,
)
from yalpReader import YAParError, parseYalp

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_YALP_DIR = PROJECT_ROOT / "tests" / "yalp" / "fixtures"


class YAParApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("YAPar: Generador SLR")
        self.geometry("1200x760")
        self.minsize(960, 620)

        self._yalpPath: Path | None = None
        self._yalPath: Path | None = None
        self._grammar: Grammar | None = None
        self._table: ParserTable | None = None
        self._diagramPath: Path | None = None
        self._ctkImage: ctk.CTkImage | None = None
        self._generatedParserPath: Path | None = None

        self._buildLayout()
        self._setStatus("Abra un archivo .yalp para comenzar.")

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _buildLayout(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        sidebar = ctk.CTkFrame(self, width=230, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_rowconfigure(12, weight=1)

        ctk.CTkLabel(
            sidebar, text="YAPar",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).grid(row=0, column=0, padx=20, pady=(24, 2), sticky="w")
        ctk.CTkLabel(
            sidebar, text="Generador SLR",
            font=ctk.CTkFont(size=12), text_color="gray70",
        ).grid(row=1, column=0, padx=20, pady=(0, 8), sticky="w")

        ctk.CTkLabel(
            sidebar, text="ARCHIVOS",
            font=ctk.CTkFont(size=10, weight="bold"), text_color="gray55",
        ).grid(row=2, column=0, padx=20, pady=(0, 4), sticky="w")

        ctk.CTkButton(sidebar, text="Abrir .yalp", command=self._openYalp
                      ).grid(row=3, column=0, padx=16, pady=3, sticky="ew")

        self._yalpLabel = ctk.CTkLabel(
            sidebar, text="Sin archivo .yalp",
            font=ctk.CTkFont(size=10), text_color="gray55",
            wraplength=190, justify="left",
        )
        self._yalpLabel.grid(row=4, column=0, padx=20, pady=(0, 4), sticky="w")

        ctk.CTkButton(sidebar, text="Abrir .yal (lexer)", command=self._openYal
                      ).grid(row=5, column=0, padx=16, pady=3, sticky="ew")

        self._yalLabel = ctk.CTkLabel(
            sidebar, text="Sin archivo .yal",
            font=ctk.CTkFont(size=10), text_color="gray55",
            wraplength=190, justify="left",
        )
        self._yalLabel.grid(row=6, column=0, padx=20, pady=(0, 8), sticky="w")

        ctk.CTkLabel(
            sidebar, text="Archivo de salida:",
            font=ctk.CTkFont(size=11),
        ).grid(row=7, column=0, padx=20, pady=(0, 2), sticky="w")

        self._outputEntry = ctk.CTkEntry(sidebar, placeholder_text="theParser.py", width=190)
        self._outputEntry.grid(row=8, column=0, padx=16, pady=(0, 8), sticky="ew")
        self._outputEntry.insert(0, "theParser.py")

        ctk.CTkLabel(
            sidebar, text="ACCIONES",
            font=ctk.CTkFont(size=10, weight="bold"), text_color="gray55",
        ).grid(row=9, column=0, padx=20, pady=(4, 4), sticky="w")

        ctk.CTkButton(
            sidebar, text="Generar parser", command=self._generateParser,
            fg_color="#217a3c", hover_color="#1a5e2e",
        ).grid(row=10, column=0, padx=16, pady=3, sticky="ew")

        ctk.CTkButton(
            sidebar, text="Analizar gramática", command=self._analyze,
            fg_color="#1f6aa5",
        ).grid(row=11, column=0, padx=16, pady=3, sticky="ew")

        ctk.CTkButton(
            sidebar, text="Guardar diagrama", command=self._saveDiagram,
        ).grid(row=13, column=0, padx=16, pady=3, sticky="ew")

        ctk.CTkLabel(
            sidebar, text="v1.0 · CustomTkinter",
            font=ctk.CTkFont(size=10), text_color="gray50",
        ).grid(row=14, column=0, padx=16, pady=16, sticky="sw")

        main = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        main.grid(row=0, column=1, sticky="nsew", padx=(0, 8), pady=8)
        main.grid_rowconfigure(1, weight=1)
        main.grid_columnconfigure(0, weight=1)

        self._status = ctk.CTkLabel(main, text="", anchor="w", font=ctk.CTkFont(size=12))
        self._status.grid(row=0, column=0, sticky="ew", padx=4, pady=(0, 8))

        self._tabs = ctk.CTkTabview(main)
        self._tabs.grid(row=1, column=0, sticky="nsew")

        for tab in ("Gramática", "FIRST / FOLLOW", "Estados LR(0)", "Tablas",
                    "Autómata", "Generar Parser", "Probar Parser"):
            self._tabs.add(tab)

        self._textGrammar = self._makeTextbox(self._tabs.tab("Gramática"))
        self._textSets = self._makeTextbox(self._tabs.tab("FIRST / FOLLOW"))
        self._textStates = self._makeTextbox(self._tabs.tab("Estados LR(0)"))
        self._textTables = self._makeTextbox(self._tabs.tab("Tablas"))

        automatonTab = self._tabs.tab("Autómata")
        automatonTab.grid_rowconfigure(0, weight=1)
        automatonTab.grid_columnconfigure(0, weight=1)
        self._diagramFrame = ctk.CTkScrollableFrame(automatonTab)
        self._diagramFrame.grid(row=0, column=0, sticky="nsew")
        self._diagramLabel = ctk.CTkLabel(
            self._diagramFrame,
            text="El diagrama LR(0) aparecerá aquí tras analizar una gramática SLR válida.",
            font=ctk.CTkFont(size=13), text_color="gray65",
        )
        self._diagramLabel.pack(expand=True, padx=20, pady=40)

        self._buildGenerateTab()
        self._buildTestTab()

    def _buildGenerateTab(self) -> None:
        tab = self._tabs.tab("Generar Parser")
        tab.grid_rowconfigure(1, weight=1)
        tab.grid_columnconfigure(0, weight=1)

        top = ctk.CTkFrame(tab, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 0))
        top.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            top, text="Estado de generación:",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, padx=(0, 8), sticky="w")

        self._genStatus = ctk.CTkLabel(
            top,
            text="Usa el botón 'Generar parser' en la barra lateral.",
            font=ctk.CTkFont(size=12), text_color="gray70",
        )
        self._genStatus.grid(row=0, column=1, sticky="w")

        frame = ctk.CTkScrollableFrame(tab, label_text="Diagrama LR(0)")
        frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=8)

        self._genDiagramLabel = ctk.CTkLabel(
            frame,
            text="El diagrama aparecerá aquí al generar el parser.",
            font=ctk.CTkFont(size=13), text_color="gray65",
        )
        self._genDiagramLabel.pack(expand=True, padx=20, pady=40)
        self._genCtkImage: ctk.CTkImage | None = None

    def _buildTestTab(self) -> None:
        tab = self._tabs.tab("Probar Parser")
        tab.grid_rowconfigure(2, weight=1)
        tab.grid_columnconfigure(0, weight=1)

        top = ctk.CTkFrame(tab, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 4))
        top.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            top, text="Seleccionar input", command=self._openInput, width=140,
        ).grid(row=0, column=0, padx=(0, 8))

        self._inputLabel = ctk.CTkLabel(
            top, text="Sin archivo de entrada",
            font=ctk.CTkFont(size=11), text_color="gray60",
        )
        self._inputLabel.grid(row=0, column=1, sticky="w")

        ctk.CTkButton(
            top, text="Ejecutar parser", command=self._runParser,
            fg_color="#217a3c", hover_color="#1a5e2e", width=140,
        ).grid(row=0, column=2, padx=(8, 0))

        ctk.CTkLabel(
            tab, text="Resultado:",
            font=ctk.CTkFont(size=12, weight="bold"), anchor="w",
        ).grid(row=1, column=0, sticky="w", padx=12, pady=(4, 0))

        self._textResult = self._makeTextbox(tab)
        self._textResult.grid(row=2, column=0, sticky="nsew", padx=8, pady=(4, 8))

        self._inputPath: Path | None = None

    # ------------------------------------------------------------------
    # Widgets helpers
    # ------------------------------------------------------------------

    def _makeTextbox(self, parent: ctk.CTkFrame) -> ctk.CTkTextbox:
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        box = ctk.CTkTextbox(parent, font=ctk.CTkFont(family="Consolas", size=13))
        box.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        box.configure(state="disabled")
        return box

    def _setStatus(self, message: str, *, error: bool = False) -> None:
        color = "#e74c3c" if error else "gray80"
        self._status.configure(text=message, text_color=color)

    # ------------------------------------------------------------------
    # Abrir archivos
    # ------------------------------------------------------------------

    def _openYalp(self) -> None:
        initial = str(DEFAULT_YALP_DIR) if DEFAULT_YALP_DIR.is_dir() else str(PROJECT_ROOT)
        path = filedialog.askopenfilename(
            title="Abrir archivo YAPar",
            initialdir=initial,
            filetypes=[("YAPar", "*.yalp"), ("Todos", "*.*")],
        )
        if not path:
            return
        self._yalpPath = Path(path)
        self._yalpLabel.configure(text=self._yalpPath.name)
        self._setStatus(f"Archivo .yalp cargado: {self._yalpPath.name}")
        self._grammar = None
        self._table = None
        self._clearDiagram()
        self._loadGrammarPreview()

    def _openYal(self) -> None:
        examplesDir = PROJECT_ROOT / "examples"
        path = filedialog.askopenfilename(
            title="Abrir lexer YALex",
            initialdir=str(examplesDir) if examplesDir.is_dir() else str(PROJECT_ROOT),
            filetypes=[("YALex", "*.yal"), ("Todos", "*.*")],
        )
        if not path:
            return
        self._yalPath = Path(path)
        self._yalLabel.configure(text=self._yalPath.name)
        self._setStatus(f"Archivo .yal cargado: {self._yalPath.name}")

    def _openInput(self) -> None:
        examplesDir = PROJECT_ROOT / "examples"
        path = filedialog.askopenfilename(
            title="Seleccionar archivo de entrada",
            initialdir=str(examplesDir) if examplesDir.is_dir() else str(PROJECT_ROOT),
            filetypes=[("Texto", "*.txt"), ("Todos", "*.*")],
        )
        if not path:
            return
        self._inputPath = Path(path)
        self._inputLabel.configure(text=self._inputPath.name)

    # ------------------------------------------------------------------
    # Cargar y analizar gramática
    # ------------------------------------------------------------------

    def _loadGrammarPreview(self) -> None:
        if not self._yalpPath:
            return
        try:
            grammar = parseYalp(str(self._yalpPath))
        except YAParError as exc:
            self._setText(self._textGrammar, str(exc))
            self._setStatus(str(exc), error=True)
            return
        self._grammar = grammar
        self._setText(self._textGrammar, _formatGrammarSummary(grammar))
        self._setStatus("Gramática válida. Pulse «Analizar gramática» para generar SLR.")

    def _analyze(self) -> None:
        if not self._yalpPath:
            messagebox.showwarning("YAPar", "Seleccione primero un archivo .yalp.")
            return
        try:
            grammar = parseYalp(str(self._yalpPath))
        except YAParError as exc:
            self._setStatus(str(exc), error=True)
            messagebox.showerror("Error YAPar", str(exc))
            return

        self._grammar = grammar
        self._setText(self._textGrammar, _formatGrammarSummary(grammar))

        aug = augmentGrammar(grammar)
        first = computeFirst(aug)
        follow = computeFollow(aug, first)
        states = buildLr0States(aug)

        self._setText(self._textSets, _formatFirstFollow(aug, first, follow))
        self._setText(self._textStates, _formatAllStates(states))

        try:
            table = buildSlrParserTable(grammar)
        except SLRConflictError as exc:
            self._table = None
            self._setText(self._textTables, str(exc))
            self._clearDiagram()
            self._setStatus("La gramática no es SLR (conflictos detectados).", error=True)
            messagebox.showerror("No es SLR", str(exc))
            return

        self._table = table
        self._setText(self._textTables, _formatTables(table))
        self._setStatus("Tabla SLR generada correctamente.")
        gotoTable = buildGotoTable(aug, states)
        self._showDiagram(states, gotoTable)

    # ------------------------------------------------------------------
    # Generar parser
    # ------------------------------------------------------------------

    def _generateParser(self) -> None:
        if not self._yalpPath:
            messagebox.showwarning("YAPar", "Seleccione primero un archivo .yalp.")
            return
        if not self._yalPath:
            messagebox.showwarning("YAPar", "Seleccione primero un archivo .yal (lexer).")
            return

        outputName = self._outputEntry.get().strip() or "theparser.py"
        outputPath = PROJECT_ROOT / outputName

        try:
            grammar = parseYalp(str(self._yalpPath))
        except YAParError as exc:
            self._setGenStatus(str(exc), error=True)
            self._setStatus(str(exc), error=True)
            return

        self._grammar = grammar
        self._setText(self._textGrammar, _formatGrammarSummary(grammar))

        # Validar tokens YAPar vs YALex
        tokenErrors = validateTokensInYalex(grammar.tokens, str(self._yalPath))
        if tokenErrors:
            msg = "\n".join(tokenErrors)
            self._setGenStatus(msg, error=True)
            self._setStatus("Error: tokens no coinciden entre .yalp y .yal.", error=True)
            return

        try:
            table = buildSlrParserTable(grammar)
        except SLRConflictError as exc:
            msg = str(exc) + "\nLa gramática no es SLR. No se generó parser."
            self._setGenStatus(msg, error=True)
            self._setStatus("La gramática no es SLR (conflictos detectados).", error=True)
            self._setText(self._textTables, str(exc))
            return

        self._table = table
        self._setText(self._textTables, _formatTables(table))

        aug = augmentGrammar(grammar)
        states = buildLr0States(aug)
        gotoTable = buildGotoTable(aug, states)
        tmpDiagram = Path(tempfile.gettempdir()) / "yaparGenLr0.png"
        try:
            result = generateLr0Diagram(states, gotoTable, str(tmpDiagram))
            self._diagramPath = result.path
            self._showGenDiagram(result.path)
            self._showDiagram(states, gotoTable)
        except Exception as exc:  # noqa: BLE001
            self._showGenDiagram(None, error=str(exc))

        generateParserFile(grammar, table, str(outputPath))
        self._generatedParserPath = outputPath
        self._setGenStatus(f"Parser generado exitosamente: {outputPath.name}", error=False)
        self._setStatus(f"Parser generado exitosamente: {outputPath.name}")
        self._tabs.set("Generar Parser")

    def _setGenStatus(self, message: str, *, error: bool = False) -> None:
        color = "#e74c3c" if error else "#2ecc71"
        self._genStatus.configure(text=message, text_color=color)

    def _showGenDiagram(self, path: Path | None, *, error: str | None = None) -> None:
        if error or path is None:
            self._genCtkImage = None
            msg = f"No se pudo generar el diagrama.\nDetalle: {error}" if error else "Sin diagrama."
            self._genDiagramLabel.configure(text=msg, image=None)
            return
        try:
            pilImage = Image.open(path)
            maxW = 880
            if pilImage.width > maxW:
                ratio = maxW / pilImage.width
                newSize = (maxW, int(pilImage.height * ratio))
                pilImage = pilImage.resize(newSize, Image.Resampling.LANCZOS)
            size = (pilImage.width, pilImage.height)
            self._genCtkImage = ctk.CTkImage(
                light_image=pilImage, dark_image=pilImage, size=size
            )
            self._genDiagramLabel.configure(text="", image=self._genCtkImage)
        except Exception:  # noqa: BLE001
            self._genDiagramLabel.configure(
                text="Error al cargar la imagen del diagrama.", image=None
            )

    # ------------------------------------------------------------------
    # Probar parser
    # ------------------------------------------------------------------

    def _runParser(self) -> None:
        if not self._inputPath:
            messagebox.showwarning("YAPar", "Seleccione un archivo de entrada.")
            return
        if self._table is None or self._grammar is None:
            messagebox.showwarning(
                "YAPar", "Genere o analice primero una gramática SLR válida.",
            )
            return

        try:
            tokens = tokenizeSimple(str(self._inputPath), self._grammar.tokens)
        except Exception as exc:  # noqa: BLE001
            self._setText(self._textResult, f"Error al leer el archivo de entrada:\n{exc}")
            return

        import io
        import sys as _sys

        captured = io.StringIO()
        oldStdout = _sys.stdout
        _sys.stdout = captured
        try:
            ok = parseTokens(tokens, self._table, self._grammar.ignoreTokens)
        finally:
            _sys.stdout = oldStdout

        output = captured.getvalue()
        self._setText(self._textResult, output)
        if ok:
            self._setStatus("Parsing exitoso.")
        else:
            self._setStatus("Parsing con error.", error=True)
        self._tabs.set("Probar Parser")

    # ------------------------------------------------------------------
    # Diagrama (tab Autómata)
    # ------------------------------------------------------------------

    def _showDiagram(
        self,
        states: list,
        gotoTable: dict[tuple[int, str], int],
    ) -> None:
        self._clearDiagram()
        tmp = Path(tempfile.gettempdir()) / "yaparLr0.png"
        try:
            result = generateLr0Diagram(states, gotoTable, str(tmp))
        except (ImportError, RuntimeError) as exc:
            self._diagramLabel.configure(
                text=(
                    "No se pudo generar el diagrama.\n\n"
                    "Opción A — Graphviz (recomendado):\n"
                    "  winget install Graphviz.Graphviz\n\n"
                    "Opción B — respaldo matplotlib:\n"
                    "  pip install matplotlib networkx\n\n"
                    f"Detalle: {exc}"
                ),
                image=None,
            )
            return

        self._diagramPath = result.path
        pilImage = Image.open(result.path)
        maxW = 900
        if pilImage.width > maxW:
            ratio = maxW / pilImage.width
            newSize = (maxW, int(pilImage.height * ratio))
            pilImage = pilImage.resize(newSize, Image.Resampling.LANCZOS)

        size = (pilImage.width, pilImage.height)
        self._ctkImage = ctk.CTkImage(light_image=pilImage, dark_image=pilImage, size=size)
        self._diagramLabel.configure(text="", image=self._ctkImage)

    def _clearDiagram(self) -> None:
        self._diagramPath = None
        self._ctkImage = None
        self._diagramLabel.configure(
            image=None,
            text="El diagrama LR(0) aparecerá aquí tras analizar una gramática SLR válida.",
        )

    def _saveDiagram(self) -> None:
        if not self._diagramPath or not self._diagramPath.exists():
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
                aug = augmentGrammar(self._grammar)  # type: ignore[arg-type]
                states = buildLr0States(aug)
                gotoTable = buildGotoTable(aug, states)
                generateLr0Diagram(states, gotoTable, dest)
            else:
                data = self._diagramPath.read_bytes()
                Path(dest).write_bytes(data)
            messagebox.showinfo("YAPar", f"Diagrama guardado en:\n{dest}")
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Error", str(exc))

    # ------------------------------------------------------------------
    # Utilidad
    # ------------------------------------------------------------------

    @staticmethod
    def _setText(widget: ctk.CTkTextbox, content: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", content)
        widget.configure(state="disabled")


# ---------------------------------------------------------------------------
# Helpers de formato
# ---------------------------------------------------------------------------


def _formatGrammarSummary(grammar: Grammar) -> str:
    lines = [
        f"Símbolo inicial: {grammar.startSymbol}",
        f"Tokens ({len(grammar.tokens)}): {', '.join(sorted(grammar.tokens))}",
    ]
    if grammar.ignoreTokens:
        lines.append(
            f"IGNORE ({len(grammar.ignoreTokens)}): "
            f"{', '.join(sorted(grammar.ignoreTokens))}"
        )
    lines.append(f"\nProducciones ({len(grammar.productions)}):\n")
    for i, prod in enumerate(grammar.productions):
        rhs = " ".join(prod.right) if prod.right else "ε"
        lines.append(f"  {i}. {prod.left} -> {rhs}")
    return "\n".join(lines)


def _formatFirstFollow(
    grammar: Grammar,
    first: dict[str, set[str]],
    follow: dict[str, set[str]],
) -> str:
    nonTerminals = sorted({p.left for p in grammar.productions})
    lines = ["=== FIRST ===\n"]
    for nt in nonTerminals:
        if nt in first:
            lines.append(formatFirst(first, nt))
    lines.append("\n=== FOLLOW ===\n")
    for nt in nonTerminals:
        if nt in follow:
            lines.append(formatFollow(follow, nt))
    return "\n".join(lines)


def _formatAllStates(states: list) -> str:
    return "\n\n".join(formatState(s) for s in states)


def _formatTables(table: ParserTable) -> str:
    lines = ["=== ACTION ===\n"]
    for (state, token), action in sorted(table.action.items()):
        lines.append(formatActionEntry(state, token, action, table.productions))
    lines.append("\n=== GOTO ===\n")
    for (state, symbol), target in sorted(table.goto.items()):
        lines.append(formatGotoEntry(state, symbol, target))
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

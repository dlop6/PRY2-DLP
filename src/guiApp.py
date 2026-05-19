"""Interfaz gráfica YAPar con CustomTkinter."""

from __future__ import annotations

import io
import sys as _sys
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
from slrGenerator import (
    ParserTable,
    SLRConflictError,
    buildSLRData,
    computeFirst,
    computeFollow,
    formatActionEntry,
    formatFirst,
    formatFollow,
    formatGotoEntry,
    formatState,
)
from yalexReader import validateTokensInYalex
from yalpReader import YAParError, parseYalp

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_YALP_DIR = PROJECT_ROOT / "tests" / "yalp" / "fixtures"

_PLACEHOLDER_DIAGRAM = "El diagrama LR(0) aparecerá aquí tras analizar una gramática SLR válida."
_PLACEHOLDER_GEN     = "El diagrama aparecerá aquí al generar el parser."


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
        # Las imágenes se mantienen como atributos para evitar GC prematuro
        self._ctkImage: ctk.CTkImage | None = None
        self._genCtkImage: ctk.CTkImage | None = None
        self._generatedParserPath: Path | None = None
        self._inputPath: Path | None = None

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

        ctk.CTkLabel(sidebar, text="YAPar",
                     font=ctk.CTkFont(size=22, weight="bold"),
                     ).grid(row=0, column=0, padx=20, pady=(24, 2), sticky="w")
        ctk.CTkLabel(sidebar, text="Generador SLR",
                     font=ctk.CTkFont(size=12), text_color="gray70",
                     ).grid(row=1, column=0, padx=20, pady=(0, 8), sticky="w")

        ctk.CTkLabel(sidebar, text="ARCHIVOS",
                     font=ctk.CTkFont(size=10, weight="bold"), text_color="gray55",
                     ).grid(row=2, column=0, padx=20, pady=(0, 4), sticky="w")

        ctk.CTkButton(sidebar, text="Abrir .yalp", command=self._openYalp,
                      ).grid(row=3, column=0, padx=16, pady=3, sticky="ew")
        self._yalpLabel = ctk.CTkLabel(sidebar, text="Sin archivo .yalp",
                                       font=ctk.CTkFont(size=10), text_color="gray55",
                                       wraplength=190, justify="left")
        self._yalpLabel.grid(row=4, column=0, padx=20, pady=(0, 4), sticky="w")

        ctk.CTkButton(sidebar, text="Abrir .yal (lexer)", command=self._openYal,
                      ).grid(row=5, column=0, padx=16, pady=3, sticky="ew")
        self._yalLabel = ctk.CTkLabel(sidebar, text="Sin archivo .yal",
                                      font=ctk.CTkFont(size=10), text_color="gray55",
                                      wraplength=190, justify="left")
        self._yalLabel.grid(row=6, column=0, padx=20, pady=(0, 8), sticky="w")

        ctk.CTkLabel(sidebar, text="Archivo de salida:",
                     font=ctk.CTkFont(size=11),
                     ).grid(row=7, column=0, padx=20, pady=(0, 2), sticky="w")
        self._outputEntry = ctk.CTkEntry(sidebar, placeholder_text="theParser.py", width=190)
        self._outputEntry.grid(row=8, column=0, padx=16, pady=(0, 8), sticky="ew")
        self._outputEntry.insert(0, "theParser.py")

        ctk.CTkLabel(sidebar, text="ACCIONES",
                     font=ctk.CTkFont(size=10, weight="bold"), text_color="gray55",
                     ).grid(row=9, column=0, padx=20, pady=(4, 4), sticky="w")

        self._btnGenerate = ctk.CTkButton(
            sidebar, text="Generar parser", command=self._generateParser,
            fg_color="#217a3c", hover_color="#1a5e2e")
        self._btnGenerate.grid(row=10, column=0, padx=16, pady=3, sticky="ew")

        self._btnAnalyze = ctk.CTkButton(
            sidebar, text="Analizar gramática", command=self._analyze,
            fg_color="#1f6aa5")
        self._btnAnalyze.grid(row=11, column=0, padx=16, pady=3, sticky="ew")

        self._btnSave = ctk.CTkButton(
            sidebar, text="Guardar diagrama", command=self._saveDiagram)
        self._btnSave.grid(row=13, column=0, padx=16, pady=3, sticky="ew")

        ctk.CTkLabel(sidebar, text="v1.0 · CustomTkinter",
                     font=ctk.CTkFont(size=10), text_color="gray50",
                     ).grid(row=14, column=0, padx=16, pady=16, sticky="sw")

        # Área principal
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
        self._textSets    = self._makeTextbox(self._tabs.tab("FIRST / FOLLOW"))
        self._textStates  = self._makeTextbox(self._tabs.tab("Estados LR(0)"))
        self._textTables  = self._makeTextbox(self._tabs.tab("Tablas"))

        # Tab Autómata: frame scrollable donde se insertan/destruyen labels
        automatonTab = self._tabs.tab("Autómata")
        automatonTab.grid_rowconfigure(0, weight=1)
        automatonTab.grid_columnconfigure(0, weight=1)
        self._diagramFrame = ctk.CTkScrollableFrame(automatonTab)
        self._diagramFrame.grid(row=0, column=0, sticky="nsew")
        self._diagramLabel = ctk.CTkLabel(
            self._diagramFrame, text=_PLACEHOLDER_DIAGRAM,
            font=ctk.CTkFont(size=13), text_color="gray65", wraplength=700)
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

        ctk.CTkLabel(top, text="Estado de generación:",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     ).grid(row=0, column=0, padx=(0, 8), sticky="w")

        self._genStatus = ctk.CTkLabel(
            top, text="Usa el botón 'Generar parser' en la barra lateral.",
            font=ctk.CTkFont(size=12), text_color="gray70")
        self._genStatus.grid(row=0, column=1, sticky="w")

        # Frame scrollable para el diagrama de generación
        self._genDiagramFrame = ctk.CTkScrollableFrame(tab, label_text="Diagrama LR(0)")
        self._genDiagramFrame.grid(row=1, column=0, sticky="nsew", padx=8, pady=8)
        self._genDiagramLabel = ctk.CTkLabel(
            self._genDiagramFrame, text=_PLACEHOLDER_GEN,
            font=ctk.CTkFont(size=13), text_color="gray65", wraplength=700)
        self._genDiagramLabel.pack(expand=True, padx=20, pady=40)

    def _buildTestTab(self) -> None:
        tab = self._tabs.tab("Probar Parser")
        tab.grid_rowconfigure(2, weight=1)
        tab.grid_columnconfigure(0, weight=1)

        top = ctk.CTkFrame(tab, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 4))
        top.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(top, text="Seleccionar input", command=self._openInput,
                      width=140).grid(row=0, column=0, padx=(0, 8))
        self._inputLabel = ctk.CTkLabel(
            top, text="Sin archivo de entrada",
            font=ctk.CTkFont(size=11), text_color="gray60")
        self._inputLabel.grid(row=0, column=1, sticky="w")

        self._btnRun = ctk.CTkButton(
            top, text="Ejecutar parser", command=self._runParser,
            fg_color="#217a3c", hover_color="#1a5e2e", width=140)
        self._btnRun.grid(row=0, column=2, padx=(8, 0))

        ctk.CTkLabel(tab, text="Resultado:", font=ctk.CTkFont(size=12, weight="bold"),
                     anchor="w").grid(row=1, column=0, sticky="w", padx=12, pady=(4, 0))

        self._textResult = self._makeTextbox(tab)
        self._textResult.grid(row=2, column=0, sticky="nsew", padx=8, pady=(4, 8))

    # ------------------------------------------------------------------
    # Helpers de widgets
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

    def _setBusy(self, label: str) -> None:
        """Deshabilita botones de acción y muestra estado de procesamiento."""
        self._btnGenerate.configure(state="disabled", text=label, fg_color="#555555")
        self._btnAnalyze.configure(state="disabled")
        self._setStatus(f"⟳  {label}...")
        self.update()

    def _setIdle(self) -> None:
        """Rehabilita botones de acción."""
        self._btnGenerate.configure(state="normal", text="Generar parser",
                                    fg_color="#217a3c")
        self._btnAnalyze.configure(state="normal")
        self.update()

    @staticmethod
    def _setText(widget: ctk.CTkTextbox, content: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", content)
        widget.configure(state="disabled")

    # ------------------------------------------------------------------
    # Abrir archivos
    # ------------------------------------------------------------------

    def _openYalp(self) -> None:
        initial = str(DEFAULT_YALP_DIR) if DEFAULT_YALP_DIR.is_dir() else str(PROJECT_ROOT)
        path = filedialog.askopenfilename(
            title="Abrir archivo YAPar",
            initialdir=initial,
            filetypes=[("YAPar", "*.yalp"), ("Todos", "*.*")])
        if not path:
            return
        self._yalpPath = Path(path)
        self._yalpLabel.configure(text=self._yalpPath.name)
        self._setStatus(f"✓  Archivo .yalp cargado: {self._yalpPath.name}")
        self._grammar = None
        self._table = None
        self._clearDiagram()
        self._loadGrammarPreview()

    def _openYal(self) -> None:
        exDir = PROJECT_ROOT / "examples"
        path = filedialog.askopenfilename(
            title="Abrir lexer YALex",
            initialdir=str(exDir) if exDir.is_dir() else str(PROJECT_ROOT),
            filetypes=[("YALex", "*.yal"), ("Todos", "*.*")])
        if not path:
            return
        self._yalPath = Path(path)
        self._yalLabel.configure(text=self._yalPath.name)
        self._setStatus(f"✓  Archivo .yal cargado: {self._yalPath.name}")

    def _openInput(self) -> None:
        # Usar el directorio del .yalp cargado como directorio inicial
        # para que sea fácil encontrar el input_valid.txt del mismo grupo
        if self._yalpPath and self._yalpPath.parent.is_dir():
            initialDir = str(self._yalpPath.parent)
        else:
            initialDir = str(PROJECT_ROOT / "examples")
        path = filedialog.askopenfilename(
            title="Seleccionar archivo de entrada",
            initialdir=initialDir,
            filetypes=[("Texto", "*.txt"), ("Todos", "*.*")])
        if not path:
            return
        self._inputPath = Path(path)
        self._inputLabel.configure(text=self._inputPath.name)
        self._setStatus(f"✓  Archivo de entrada cargado: {self._inputPath.name}")

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
            self._setStatus(f"✗  {exc}", error=True)
            return
        self._grammar = grammar
        self._setText(self._textGrammar, _formatGrammarSummary(grammar))
        self._setStatus("✓  Gramática válida. Pulse «Analizar gramática» para generar la tabla SLR.")

    def _analyze(self) -> None:
        if not self._yalpPath:
            messagebox.showwarning("YAPar", "Seleccione primero un archivo .yalp.")
            return
        self._setBusy("Analizando gramática")
        try:
            grammar = parseYalp(str(self._yalpPath))
        except YAParError as exc:
            self._setIdle()
            self._setStatus(f"✗  {exc}", error=True)
            messagebox.showerror("Error YAPar", str(exc))
            return

        self._grammar = grammar
        self._setText(self._textGrammar, _formatGrammarSummary(grammar))

        try:
            aug, states, gotoTable, allTrans, table = buildSLRData(grammar)
        except SLRConflictError as exc:
            self._table = None
            self._setText(self._textTables, str(exc))
            self._clearDiagram()
            self._setIdle()
            self._setStatus("✗  La gramática no es SLR (conflictos detectados).", error=True)
            messagebox.showerror("No es SLR", str(exc))
            return

        # first/follow solo para mostrar en la pestaña de conjuntos
        first = computeFirst(aug)
        follow = computeFollow(aug, first)
        self._setText(self._textSets, _formatFirstFollow(aug, first, follow))
        self._setText(self._textStates, _formatAllStates(states))
        self._table = table
        self._setText(self._textTables, _formatTables(table))
        self._setStatus("✓  Tabla SLR generada. Generando diagrama...")
        self.update()
        self._showDiagram(states, gotoTable, allTrans, aug.startSymbol)
        self._setIdle()
        self._setStatus("✓  Tabla SLR y autómata LR(0) generados correctamente.")
        self._tabs.set("Autómata")

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

        outputName = self._outputEntry.get().strip() or "theParser.py"
        outputPath = PROJECT_ROOT / outputName
        self._setBusy("Generando parser")

        # 1. Parsear gramática
        try:
            grammar = parseYalp(str(self._yalpPath))
        except YAParError as exc:
            self._setIdle()
            self._setGenStatus(f"✗  {exc}", error=True)
            self._setStatus(f"✗  {exc}", error=True)
            return

        self._grammar = grammar
        self._setText(self._textGrammar, _formatGrammarSummary(grammar))

        # 2. Validar tokens YAPar vs YALex
        self._setStatus("⟳  Validando tokens YAPar vs YALex...")
        self.update()
        tokenErrors = validateTokensInYalex(grammar.tokens, str(self._yalPath))
        if tokenErrors:
            msg = "\n".join(tokenErrors)
            self._setIdle()
            self._setGenStatus(f"✗  {tokenErrors[0]}", error=True)
            self._setStatus("✗  Error: tokens no coinciden entre .yalp y .yal.", error=True)
            messagebox.showerror("Validación YALex", msg)
            return

        # 3. construir tabla SLR (una sola pasada, sin recalcular)
        self._setStatus("⟳  Construyendo tabla SLR...")
        self.update()
        try:
            aug, states, gotoTable, allTrans, table = buildSLRData(grammar)
        except SLRConflictError as exc:
            self._setIdle()
            msg = str(exc) + "\nLa gramática no es SLR. No se generó parser."
            self._setGenStatus("✗  La gramática no es SLR.", error=True)
            self._setStatus("✗  La gramática no es SLR (conflictos detectados).", error=True)
            self._setText(self._textTables, str(exc))
            messagebox.showerror("No es SLR", msg)
            return

        self._table = table
        self._setText(self._textTables, _formatTables(table))

        # 4. generar diagrama con los datos ya calculados
        self._setStatus("⟳  Generando diagrama LR(0)...")
        self.update()
        tmpDiagram = Path(tempfile.gettempdir()) / "yaparGenLr0.png"
        try:
            result = generateLr0Diagram(
                states, gotoTable, str(tmpDiagram), allTrans, aug.startSymbol)
            self._diagramPath = result.path
            self._showGenDiagram(result.path)
            self._showDiagram(states, gotoTable, allTrans, aug.startSymbol)
        except Exception as exc:  # noqa: BLE001
            self._showGenDiagram(None, error=str(exc))

        # 5. Generar theParser.py
        self._setStatus("⟳  Escribiendo theParser.py...")
        self.update()
        generateParserFile(grammar, table, str(outputPath))
        self._generatedParserPath = outputPath
        self._setIdle()
        self._setGenStatus(f"✓  Parser generado exitosamente: {outputPath.name}")
        self._setStatus(f"✓  Parser generado exitosamente: {outputPath.name}")
        self._tabs.set("Generar Parser")

    def _setGenStatus(self, message: str, *, error: bool = False) -> None:
        color = "#e74c3c" if error else "#2ecc71"
        self._genStatus.configure(text=message, text_color=color)

    # ------------------------------------------------------------------
    # Probar parser
    # ------------------------------------------------------------------

    def _runParser(self) -> None:
        if not self._inputPath:
            messagebox.showwarning("YAPar", "Seleccione un archivo de entrada.")
            return
        if self._table is None or self._grammar is None:
            messagebox.showwarning(
                "YAPar", "Genere o analice primero una gramática SLR válida.")
            return

        self._btnRun.configure(state="disabled", text="Ejecutando...")
        self._setStatus("⟳  Ejecutando parser...")
        self.update()

        try:
            tokens = tokenizeSimple(str(self._inputPath), self._grammar.tokens)
        except Exception as exc:  # noqa: BLE001
            self._setText(self._textResult, f"Error al leer el archivo de entrada:\n{exc}")
            self._btnRun.configure(state="normal", text="Ejecutar parser")
            return

        captured = io.StringIO()
        oldStdout = _sys.stdout
        ok = False
        try:
            _sys.stdout = captured
            ok = parseTokens(tokens, self._table, self._grammar.ignoreTokens)
        except Exception as exc:  # noqa: BLE001
            captured.write(f"\nError inesperado durante el parsing:\n{exc}")
        finally:
            _sys.stdout = oldStdout
            self._btnRun.configure(state="normal", text="Ejecutar parser")

        output = captured.getvalue()
        self._setText(self._textResult, output)

        if ok:
            self._setStatus("✓  Parsing exitoso: entrada aceptada.")
        else:
            self._setStatus("✗  Parsing con error. Ver resultado.", error=True)
        self._tabs.set("Probar Parser")

    # ------------------------------------------------------------------
    # Diagrama: patrón destroy-recreate para evitar "pyimage doesn't exist"
    # ------------------------------------------------------------------

    def _showDiagram(
        self,
        states: list,
        gotoTable: dict[tuple[int, str], int],
        allTrans: dict[tuple[int, str], int] | None = None,
        augStart: str | None = None,
    ) -> None:
        """Genera y muestra el diagrama LR(0) en la pestaña Autómata."""
        tmp = Path(tempfile.gettempdir()) / "yaparLr0.png"
        try:
            result = generateLr0Diagram(states, gotoTable, str(tmp), allTrans, augStart)
        except (ImportError, RuntimeError) as exc:
            self._setDiagramText(
                "No se pudo generar el diagrama.\n\n"
                "Opción A: winget install Graphviz.Graphviz\n"
                "Opción B: pip install matplotlib networkx\n\n"
                f"Detalle: {exc}"
            )
            return

        self._diagramPath = result.path
        try:
            pilImage = Image.open(result.path)
            # Escalar solo si es extremadamente ancho; altura libre para el scroll
            maxW = 1100
            if pilImage.width > maxW:
                ratio = maxW / pilImage.width
                pilImage = pilImage.resize(
                    (maxW, int(pilImage.height * ratio)), Image.Resampling.LANCZOS)
            self._ctkImage = ctk.CTkImage(
                light_image=pilImage, dark_image=pilImage,
                size=(pilImage.width, pilImage.height))
            for w in self._diagramFrame.winfo_children():
                w.destroy()
            # Sin expand=True para que el CTkScrollableFrame pueda desplazarse
            self._diagramLabel = ctk.CTkLabel(
                self._diagramFrame, text="", image=self._ctkImage)
            self._diagramLabel.pack(padx=8, pady=8)
        except Exception as exc:  # noqa: BLE001
            self._setDiagramText(f"Error al cargar la imagen del diagrama:\n{exc}")

    def _clearDiagram(self) -> None:
        """Resetea el panel de diagrama a texto de marcador de posición."""
        # Liberar imagen ANTES de destruir el widget que la contiene
        self._ctkImage = None
        self._diagramPath = None
        for w in self._diagramFrame.winfo_children():
            w.destroy()
        self._diagramLabel = ctk.CTkLabel(
            self._diagramFrame, text=_PLACEHOLDER_DIAGRAM,
            font=ctk.CTkFont(size=13), text_color="gray65", wraplength=700)
        self._diagramLabel.pack(expand=True, padx=20, pady=40)

    def _setDiagramText(self, text: str) -> None:
        """Muestra un mensaje de texto en el panel de diagrama (sin imagen)."""
        self._ctkImage = None
        for w in self._diagramFrame.winfo_children():
            w.destroy()
        self._diagramLabel = ctk.CTkLabel(
            self._diagramFrame, text=text,
            font=ctk.CTkFont(size=12), text_color="gray65", wraplength=700)
        self._diagramLabel.pack(expand=True, padx=20, pady=40)

    # Mismo patrón para el panel de generación
    def _showGenDiagram(self, path: Path | None, *, error: str | None = None) -> None:
        if error or path is None:
            self._genCtkImage = None
            msg = (f"No se pudo generar el diagrama.\nDetalle: {error}"
                   if error else "Sin diagrama.")
            self._setGenDiagramText(msg)
            return
        try:
            pilImage = Image.open(path)
            maxW = 880
            if pilImage.width > maxW:
                ratio = maxW / pilImage.width
                pilImage = pilImage.resize(
                    (maxW, int(pilImage.height * ratio)), Image.Resampling.LANCZOS)
            self._genCtkImage = ctk.CTkImage(
                light_image=pilImage, dark_image=pilImage,
                size=(pilImage.width, pilImage.height))
            for w in self._genDiagramFrame.winfo_children():
                w.destroy()
            self._genDiagramLabel = ctk.CTkLabel(
                self._genDiagramFrame, text="", image=self._genCtkImage)
            self._genDiagramLabel.pack(padx=8, pady=8)
        except Exception as exc:  # noqa: BLE001
            self._setGenDiagramText(f"Error al cargar la imagen:\n{exc}")

    def _setGenDiagramText(self, text: str) -> None:
        self._genCtkImage = None
        for w in self._genDiagramFrame.winfo_children():
            w.destroy()
        self._genDiagramLabel = ctk.CTkLabel(
            self._genDiagramFrame, text=text,
            font=ctk.CTkFont(size=12), text_color="gray65", wraplength=700)
        self._genDiagramLabel.pack(expand=True, padx=20, pady=40)

    # ------------------------------------------------------------------
    # Guardar diagrama
    # ------------------------------------------------------------------

    def _saveDiagram(self) -> None:
        if not self._diagramPath or not self._diagramPath.exists():
            messagebox.showinfo(
                "YAPar",
                "No hay diagrama para guardar.\nAnalice una gramática SLR válida primero.")
            return
        dest = filedialog.asksaveasfilename(
            title="Guardar diagrama LR(0)",
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("PDF", "*.pdf")])
        if not dest:
            return
        self._btnSave.configure(state="disabled", text="Guardando...")
        self.update()
        try:
            if dest.lower().endswith(".pdf"):
                if self._grammar is None:
                    raise RuntimeError("Gramática no disponible para regenerar PDF.")
                aug, states, gotoTable, allTrans, _ = buildSLRData(self._grammar)
                generateLr0Diagram(states, gotoTable, dest, allTrans, aug.startSymbol)
            else:
                Path(dest).write_bytes(self._diagramPath.read_bytes())
            messagebox.showinfo("YAPar", f"Diagrama guardado en:\n{dest}")
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Error", str(exc))
        finally:
            self._btnSave.configure(state="normal", text="Guardar diagrama")


# ---------------------------------------------------------------------------
# Helpers de formato (módulo-level)
# ---------------------------------------------------------------------------

def _formatGrammarSummary(grammar: Grammar) -> str:
    lines = [
        f"Símbolo inicial: {grammar.startSymbol}",
        f"Tokens ({len(grammar.tokens)}): {', '.join(sorted(grammar.tokens))}",
    ]
    if grammar.ignoreTokens:
        lines.append(
            f"IGNORE ({len(grammar.ignoreTokens)}): "
            f"{', '.join(sorted(grammar.ignoreTokens))}")
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

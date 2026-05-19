# YAPar — Generador de Analizadores Sintácticos SLR

**CC3071 · Diseño de Lenguajes de Programación · UVG 2026-I**

**Integrantes:** Diego Lopez #23747 · Jennifer Toxcon #21276 · Roberto Barreda #23354

Genera un parser SLR en Python a partir de una gramática `.yalp`. Produce la tabla ACTION/GOTO, el autómata LR(0) y un archivo `theparser.py` completamente independiente.

---

## Requisitos

- Python 3.10+
- `pip install -r requirements.txt`
- Graphviz (opcional, mejor calidad en el diagrama): `winget install Graphviz.Graphviz`

---

## Cómo correrlo

### 1. Generar el parser (CLI)

```bash
python yapar.py examples/medium/parser.yalp -l examples/medium/lexer.yal -o theparser.py
```

Produce `theparser.py` y `theparser_lr0.png`.

### 2. Ejecutar el parser generado

```bash
python theparser.py examples/medium/input_valid.txt    # Parsing exitoso
python theparser.py examples/medium/input_error.txt    # Error sintáctico
```

### 3. Interfaz gráfica

```bash
python src/guiApp.py
```
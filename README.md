# YAPar — Generador de analizadores sintácticos SLR

Generador de parsers SLR escrito en Python. Toma un archivo `.yalp` con la especificación de una gramática libre de contexto, construye la tabla SLR (FIRST, FOLLOW, autómata LR(0), ACTION/GOTO) y muestra los resultados en una interfaz gráfica. A futuro generará un analizador sintáctico que interactúe con el lexer producido por YALex.

## Requisitos

- Python 3.10+
- pip

Opcional (mejor calidad del diagrama LR(0)):

- [Graphviz](https://graphviz.org/download/) en el PATH (`dot`). En Windows: `winget install Graphviz.Graphviz` y reiniciar el IDE.

## Instalación

Se recomienda un entorno virtual para que el IDE y la terminal usen el mismo intérprete:

```bash
python -m venv .venv

# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
```

En Cursor/VS Code: **Python: Select Interpreter** → `.venv\Scripts\python.exe`.

## Uso

### Interfaz gráfica (recomendado)

```bash
python gui.py
```

1. **Abrir .yalp** — seleccione un archivo de gramática.
2. **Analizar gramática** — calcula FIRST/FOLLOW, estados LR(0) y tablas ACTION/GOTO.
3. Revise las pestañas: **Gramática**, **FIRST / FOLLOW**, **Estados LR(0)**, **Tablas**, **Autómata**.
4. **Guardar diagrama** — exporta el PNG del autómata (si se generó correctamente).

**Ejemplo incluido:** `examples/expr.yalp` (expresiones aritméticas, gramática SLR válida).

> **Nota:** `tests/yalp/fixtures/valid_basic.yalp` parsea bien como YAPar pero **no es SLR** (muestra conflictos al analizar). Úselo para probar la detección de errores.

### Línea de comandos (API Python)

```python
from yalp_reader import parse_yalp
from slr_generator import build_slr_parser_table, SLRConflictError

grammar = parse_yalp("examples/expr.yalp")
try:
    table = build_slr_parser_table(grammar)
    print("SLR OK — ACTION:", len(table.action), "GOTO:", len(table.goto))
except SLRConflictError as e:
    print("No es SLR:\n", e)
```

### Generar un parser (pendiente)

```bash
python yapar.py examples/parser.yalp -l examples/lexer.yal -o theparser.py
python theparser.py examples/input_valid.txt
```

Estos comandos estarán disponibles cuando se implementen `yapar.py`, `code_generator.py` y `parser_runtime.py`.

## Formato del archivo `.yalp`

```
/* comentarios con /* ... */ */

%token TOKEN_A TOKEN_B
%token TOKEN_C
IGNORE TOKEN_C

%%

produccion1:
    produccion1 TOKEN_A produccion2
  | produccion2
;

produccion2:
    TOKEN_B
;
```

**Reglas:**

- Sección de tokens antes de `%%`, producciones después.
- `%token` declara terminales — deben estar en MAYÚSCULA (`[A-Z][A-Z0-9_]*`).
- `IGNORE` filtra tokens del flujo antes de parsear.
- No-terminales deben iniciar en minúscula.
- Cada producción termina con `;`, alternativas separadas por `|`.

## Formato de tokens (interfaz con YALex)

```json
{ "type": "TOKEN_A", "lexeme": "x", "line": 1, "column": 1 }
```

Errores léxicos:

```json
{ "type": "LEXICAL_ERROR", "lexeme": "@", "line": 2, "column": 4, "message": "símbolo no reconocido" }
```

## Gramáticas y ε (epsilon)

El generador SLR **soporta producciones vacías**. Una producción sin símbolos en la parte derecha representa ε (`EPSILON = "ε"` en `slr_generator.py`). El marcador de fin de entrada es `$` (`END_MARKER`).

## Visualización del autómata LR(0)

| Modo | Requisito | Resultado |
|------|-----------|-----------|
| **Graphviz** | `dot` en el PATH + `pip install graphviz` | Nodos con todos los items LR(0) |
| **matplotlib** (automático) | `pip install matplotlib networkx` | Nodos `I0`, `I1`, … y aristas etiquetadas |

```python
from slr_generator import augment_grammar, build_lr0_states, build_goto_table
from lr0_visualizer import generate_lr0_diagram

aug = augment_grammar(grammar)
states = build_lr0_states(aug)
goto_table = build_goto_table(aug, states)
result = generate_lr0_diagram(states, goto_table, "lr0_automaton.png")
print(result.engine)  # "graphviz" o "matplotlib"
```

## Pruebas

### Tests automáticos

```bash
pytest tests/ -v
pytest tests/slr/ -v    # solo generador SLR
pytest tests/yalp/ -v   # solo lector .yalp
```

### Prueba manual rápida

| Paso | Acción | Resultado esperado |
|------|--------|-------------------|
| 1 | `python gui.py` + `examples/expr.yalp` + Analizar | Tablas y diagrama sin error |
| 2 | Mismo flujo con `valid_basic.yalp` | Mensaje de conflictos SLR |
| 3 | Abrir un `.yalp` con error de sintaxis | Error YAPar en pantalla |

## Estado actual

| Componente | Estado |
|---|---|
| Modelos `Production` y `Grammar` | Completo |
| Lectura y validación de `.yalp` (`parse_yalp`) | Completo |
| Generador de tabla SLR (`slr_generator.py`) | Completo |
| Visualización del autómata LR(0) | Completo (Graphviz + respaldo matplotlib) |
| Interfaz gráfica (`gui.py`, CustomTkinter) | Completo |
| Runtime del parser (shift/reduce/accept) | Pendiente |
| Generación de `theparser.py` | Pendiente |
| Adaptador para lexer YALex | Pendiente |
| CLI (`yapar.py`) | Pendiente |

## Restricciones del proyecto

- **Prohibido usar librerías de expresiones regulares** (`import re` o similares). Toda lógica de reconocimiento de patrones se implementa con autómatas finitos o parsing manual. Penalización: 0 puntos.
- El parser generado (`theparser.py`) debe funcionar de forma **independiente** del generador.
- La interfaz gráfica es **obligatoria**. Penalización por ausencia: -3 puntos.

## Estructura del proyecto

```
grammar.py            # modelos Production y Grammar
yalp_reader.py        # lector y validador de .yalp
slr_generator.py      # FIRST, FOLLOW, LR(0), ACTION/GOTO, detección de conflictos
lr0_visualizer.py     # diagrama LR(0) (Graphviz / matplotlib)
gui.py                # interfaz gráfica CustomTkinter
requirements.txt
examples/
  expr.yalp           # gramática SLR de ejemplo
tests/
  yalp/               # tests del lector .yalp
  slr/                # tests del generador SLR
yapar.py              # CLI (pendiente)
parser_runtime.py     # runtime shift/reduce/accept (pendiente)
code_generator.py     # generación de theparser.py (pendiente)
lexer_adapter.py      # adaptador tokens YALex (pendiente)
docs/
  instrucciones.md    # enunciado del proyecto
```

## Dependencias (`requirements.txt`)

| Paquete | Uso |
|---------|-----|
| `pytest` | Tests |
| `graphviz` | Wrapper Python para diagramas (requiere `dot` en el sistema) |
| `customtkinter`, `Pillow` | Interfaz gráfica |
| `matplotlib`, `networkx` | Diagrama LR(0) sin Graphviz instalado |

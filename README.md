# YAPar — Generador de analizadores sintácticos SLR

Generador de parsers SLR escrito en Python. Toma un archivo `.yalp` con la especificación de una gramática libre de contexto y genera un analizador sintáctico funcional que interactúa con el lexer producido por YALex.

## Requisitos

- Python 3.10+
- pip

## Instalación

```bash
pip install -r requirements.txt
```

## Uso

### Generar un parser

```bash
python yapar.py examples/parser.yalp -l examples/lexer.yal -o theparser.py
```

### Ejecutar el parser generado

```bash
python theparser.py examples/input_valid.txt
```

### Lanzar la interfaz gráfica

Requiere `customtkinter` y `Pillow` (incluidos en `requirements.txt`):

```bash
python gui.py
```

La GUI permite abrir un `.yalp`, ver FIRST/FOLLOW, estados LR(0), tablas ACTION/GOTO y el diagrama del autómata.

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
- Sección de tokens antes de `%%`, producciones después
- `%token` declara terminales — deben estar en MAYÚSCULA (`[A-Z][A-Z0-9_]*`)
- `IGNORE` filtra tokens del flujo antes de parsear
- No-terminales deben iniciar en minúscula
- Cada producción termina con `;`, alternativas separadas por `|`

## Formato de tokens (interfaz con YALex)

```json
{ "type": "TOKEN_A", "lexeme": "x", "line": 1, "column": 1 }
```

Errores léxicos se representan como:

```json
{ "type": "LEXICAL_ERROR", "lexeme": "@", "line": 2, "column": 4, "message": "símbolo no reconocido" }
```

## Gramáticas y ε (epsilon)

El generador SLR **soporta producciones vacías** (ε). Una producción sin símbolos en la parte derecha representa ε y se denota con la constante `EPSILON = "ε"` en `slr_generator.py`. El marcador de fin de entrada es `$` (`END_MARKER`).

## Visualización LR(0)

- **Con Graphviz** (mejor calidad, nodos con items): instale [Graphviz](https://graphviz.org/download/) en el sistema y añada `dot` al PATH.
  - Windows: `winget install Graphviz.Graphviz` y reinicie Cursor.
- **Sin Graphviz**: se usa automáticamente **matplotlib + networkx** (nodos `I0`, `I1`, … con aristas etiquetadas).

```python
from slr_generator import augment_grammar, build_lr0_states, build_goto_table
from lr0_visualizer import generate_lr0_diagram

aug = augment_grammar(grammar)
states = build_lr0_states(aug)
goto_table = build_goto_table(aug, states)
result = generate_lr0_diagram(states, goto_table, "lr0_automaton.png")
print(result.engine)  # "graphviz" o "matplotlib"
```

## Ejecutar tests

```bash
pytest tests/ -v
```

## Estado actual

| Componente | Estado |
|---|---|
| Modelos `Production` y `Grammar` | Completo |
| Lectura y validación de `.yalp` (`parse_yalp`) | Completo |
| Generador de tabla SLR | Completo |
| Visualización del autómata LR(0) | Completo |
| Runtime del parser (shift/reduce/accept) | Pendiente |
| Generación de `theparser.py` | Pendiente |
| Adaptador para lexer YALex | Pendiente |
| CLI (`yapar.py`) | Pendiente |
| Interfaz gráfica (CustomTkinter) | Completo |

## Restricciones del proyecto

- **Prohibido usar librerías de expresiones regulares** (`import re` o similares). Toda lógica de reconocimiento de patrones se implementa con autómatas finitos o parsing manual. Penalización: 0 puntos.
- El parser generado (`theparser.py`) debe funcionar de forma **independiente** del generador.
- La interfaz gráfica es **obligatoria**. Penalización por ausencia: -3 puntos.

## Estructura del proyecto

```
yapar.py              # CLI principal
grammar.py            # modelos Production y Grammar
yalp_reader.py        # lector y validador de .yalp
slr_generator.py      # algoritmo SLR (FIRST, FOLLOW, LR(0), ACTION/GOTO)
lr0_visualizer.py     # visualización del autómata LR(0)
parser_runtime.py     # runtime shift/reduce/accept/error
code_generator.py     # generación de theparser.py
lexer_adapter.py      # adaptador para tokens de YALex
gui.py                # interfaz gráfica
requirements.txt
examples/             # archivos de ejemplo (.yalp, .yal, entradas)
tests/
  yalp/               # tests del lector .yalp
  slr/                # tests del generador SLR
  runtime/            # tests del runtime
  integration/        # tests end-to-end
```

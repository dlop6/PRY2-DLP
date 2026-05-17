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

```bash
python gui.py
```

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

## Ejecutar tests

```bash
pytest tests/ -v
```

## Estado actual

| Componente | Estado |
|---|---|
| Modelos `Production` y `Grammar` | Completo |
| Lectura y validación de `.yalp` (`parse_yalp`) | Completo |
| Generador de tabla SLR | Pendiente |
| Visualización del autómata LR(0) | Pendiente |
| Runtime del parser (shift/reduce/accept) | Pendiente |
| Generación de `theparser.py` | Pendiente |
| Adaptador para lexer YALex | Pendiente |
| CLI (`yapar.py`) | Pendiente |
| Interfaz gráfica | Pendiente |

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

# Guía E2E — GUI YAPar

## Prerequisito

```
python src/guiApp.py
```

La ventana abre con título **"YAPar: Generador SLR"** y la barra de estado dice:
> `Abra un archivo .yalp para comenzar.`

---

## Caso 1 — Gramática baja válida (generar + probar)

**Paso 1.** Clic en **"Abrir .yalp"** → `examples/low/parser.yalp`

Resultado esperado:
- Label cambia a `parser.yalp`
- Pestaña **Gramática** muestra símbolo inicial `expr`, tokens `NUM PLUS WS`, 2 producciones

**Paso 2.** Clic en **"Abrir .yal (lexer)"** → `examples/low/lexer.yal`

**Paso 3.** Campo de salida dice `theParser.py`. Clic en **"Generar parser"** (botón verde)

Resultado esperado:
- Barra de estado termina en `✓ Parser generado exitosamente: theParser.py`
- GUI salta a pestaña **Generar Parser** con el diagrama LR(0)
- Se crea `theParser.py` en la raíz del proyecto

**Paso 4.** Pestaña **"Probar Parser"** → **"Seleccionar input"** → `examples/low/input_valid.txt`

Contenido del archivo: `NUM PLUS NUM PLUS NUM`

**Paso 5.** Clic en **"Ejecutar parser"**

Resultado esperado: `✓ Parsing exitoso: entrada aceptada.`

**Paso 6.** **"Seleccionar input"** → `examples/low/input_error.txt`

Contenido del archivo: `NUM PLUS PLUS NUM`

**Paso 7.** Clic en **"Ejecutar parser"**

Resultado esperado: error sintáctico en rojo — recibió `PLUS`, esperaba `NUM`

---

## Caso 2 — Explorar tabla SLR sin generar parser (gramática media)

**Paso 8.** Clic en **"Abrir .yalp"** → `examples/medium/parser.yalp`

**Paso 9.** Clic en **"Analizar gramática"** (botón azul)

Resultado esperado:
- GUI salta a pestaña **Autómata** con el diagrama LR(0)
- Pestaña **FIRST / FOLLOW** muestra conjuntos de `expr`, `term`, `factor`
- Pestaña **Estados LR(0)** lista todos los ítems por estado
- Pestaña **Tablas** muestra secciones `ACTION` y `GOTO`

---

## Caso 3 — Gramática con conflicto SLR

**Paso 10.** Clic en **"Abrir .yalp"** → `tests/yalp/fixtures/error_slr_conflict.yalp`

Contenido: `expr: expr PLUS expr | ID ;` (gramática ambigua)

**Paso 11.** Clic en **"Analizar gramática"**

Resultado esperado:
- Popup **"No es SLR"** con detalle del conflicto shift/reduce
- Barra de estado en rojo: `✗ La gramática no es SLR (conflictos detectados).`

---

## Caso 4 — Guardar diagrama

**Paso 12.** Con una gramática SLR válida ya analizada, clic en **"Guardar diagrama"** (sidebar)

Resultado esperado: diálogo para escoger destino → guarda la imagen `.png` del autómata

---

## Resumen de checks

| # | Qué verifica |
|---|-------------|
| 1–2 | Carga de archivos `.yalp` y `.yal` |
| 3 | Generación del parser + diagrama LR(0) |
| 4–5 | Input válido → aceptado |
| 6–7 | Input inválido → error sintáctico |
| 8–9 | Análisis sin generación + todas las pestañas internas |
| 10–11 | Detección de conflicto SLR |
| 12 | Exportar diagrama a PNG |

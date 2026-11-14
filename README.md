# RustiQ

Compilador de **RustiQ** (un subconjunto de Rust) a **WebAssembly**, escrito en Python con ANTLR4, y un editor web para escribir, compilar y ejecutar programas.

```
programa .rq ──► ANTLR4 (léxico + sintaxis) ──► semántico ──► generador WAT ──► .wasm ──► navegador / wasmtime
```

## Requisitos

- Python 3.9 o superior
- Java (solo si se quiere regenerar el parser desde `RustiQ.g4`)
- Node.js 18 o superior (solo si se quiere modificar el editor web; el editor ya compilado viene en `web/frontend/dist`)

## Instalación

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Usar el editor web

```bash
python web/server.py
```

Abrir http://localhost:5001. Se puede escribir o cargar un programa (o elegir uno en **Ejemplos**), pulsar **Compilar** y luego **Ejecutar**. `⌘/Ctrl + Enter` compila y ejecuta.

- La compilación ocurre en Python, en el servidor (`POST /api/compilar`).
- El navegador recibe el `.wasm` y lo ejecuta con la API `WebAssembly`, en un Web Worker (si el programa no termina en 5 s, se detiene).
- Los errores muestran fase, línea y columna, y se subrayan en el editor.

## Usar el compilador desde la terminal

```bash
cd compilador
python correr.py ejemplos/wasm/paso11_ejemplo_profe.rq          # compila, valida y ejecuta
python correr.py ejemplos/wasm/paso11_ejemplo_profe.rq --wat    # además muestra el WAT
```

El `.wat` y el `.wasm` generados quedan en `compilador/salida/`.

## Pruebas

```bash
python -m unittest discover -s compilador/tests -v
```

Los programas de `compilador/ejemplos/wasm/` traen su salida esperada en un comentario; las pruebas los compilan, validan, ejecutan y comparan.

## Funciones predefinidas

RustiQ no tiene `println!`. Para mostrar resultados existen:

| Función | Imprime |
|---|---|
| `print_i32(x: i32)` | un entero |
| `print_f64(x: f64)` | un decimal |
| `print_bool(x: bool)` | `true` / `false` |
| `print_char(c: char)` | un carácter |
| `print_str(s: String)` o `print_str(&s)` | un texto |

## Estructura

```
compilador/
  RustiQ.g4            gramática ANTLR4
  generado/            lexer y parser generados para Python
  errores.py           errores con fase, línea y columna
  tipos.py             tipos y reglas de operadores
  tabla_simbolos.py    ámbitos, variables, funciones, structs y enums
  memoria.py           representación de los valores en la memoria de Wasm
  generador_wat.py     árbol de ANTLR -> WAT
  ejecutor_wasm.py     WAT -> .wasm, validación y ejecución con wasmtime
  correr.py            compilar y ejecutar un archivo desde la terminal
  ejemplos/            programas de ejemplo
  tests/               pruebas
web/
  server.py            servidor Flask (sirve el editor y la API)
  frontend/            editor en React (Vite + CodeMirror)
```

## Modificar el editor web

```bash
cd web/frontend
npm install
npm run dev        # en otra terminal: python web/server.py
npm run build      # genera web/frontend/dist, que es lo que sirve Flask
```

## Regenerar el parser

```bash
cd compilador
java -jar antlr-4.13.2-complete.jar -Dlanguage=Python3 -visitor -o generado RustiQ.g4
```

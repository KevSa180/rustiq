# RustiQ

Compilador de **RustiQ** (un subconjunto de Rust) a **WebAssembly**, escrito en Python con ANTLR4, y un editor web para escribir, compilar y ejecutar programas.

```
programa .rq ──► léxico + sintaxis (ANTLR4) ──► recolector ──► tipos ──► ownership ──► generador WAT ──► .wasm ──► navegador / wasmtime
```

Cada fase corre solo si la anterior no dejó errores. Un programa con errores **nunca** produce un `.wasm`. Todos los errores llevan fase, línea y columna (desde 1) y mensaje en español.

Proyecto del curso Compiladores e Intérpretes (TEC San Carlos).

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
python probar.py tests/invalidos/ownership/dos_ref_mut.rq       # solo análisis: muestra los errores
```

El `.wat` y el `.wasm` generados quedan en `compilador/salida/`.

## Pruebas

```bash
cd compilador
python -m unittest discover -s tests          # añadir -v para ver cada prueba
```

| Carpeta | Qué prueba |
|---|---|
| `ejemplos/wasm/*.rq` | Programas válidos: se compilan, validan, ejecutan y se compara la salida con el comentario `// Salida esperada:`. |
| `tests/validos/*.rq` | Casos límite que deben compilar (inicialización diferida, préstamos que terminan en su último uso, match sobre referencias, etc.). |
| `tests/invalidos/semantico/*.rq` | Un programa por cada error semántico. La cabecera `// Error esperado: semántico <línea>:<columna> <mensaje>` dice qué debe reportarse. |
| `tests/invalidos/ownership/*.rq` | Lo mismo para los errores de ownership y préstamos. |
| `tests/test_tabla_simbolos.py` | Ámbitos, sombreado, duplicados y resolución de nombres. |
| `tests/test_generador_wat.py` | Backend: copia de arrays, `&mut` a través de funciones, errores en ejecución (división por cero, índice fuera de rango). |

Para agregar una prueba inválida basta con crear el `.rq` con su cabecera; `tests/test_analisis.py` recorre las carpetas.

## Fases del compilador

| Fase | Archivo | Qué hace |
|---|---|---|
| léxico / sintáctico | `generado/`, `errores.py` | ANTLR4 reconoce el programa; `ColectorErrores` traduce los mensajes al español. |
| semántico (1) | `recolector.py` | Registra structs, enums, constantes y firmas de funciones en la tabla de símbolos, convierte los tipos escritos a objetos de `tipos.py` y revisa duplicados, tipos inexistentes y `main`. |
| semántico (2) | `verificador_tipos.py` | Revisa los cuerpos: variables, operadores, condiciones, llamadas, structs, enums, arrays, tuplas, `match` (patrones y exhaustividad), `break`/`continue`, constantes. Deja anotado en cada nodo del árbol de ANTLR su `tipo` y su `simbolo`. |
| ownership | `analizador_ownership.py` | Movimientos, inicialización, `mut`, préstamos `&`/`&mut` y referencias que no viven lo suficiente. |
| generación | `generador_wat.py`, `memoria.py` | Árbol de ANTLR → texto WAT. `memoria.py` documenta cómo se guardan structs, arrays, tuplas, enums y String. |
| ejecución | `ejecutor_wasm.py` | WAT → `.wasm`, validación y ejecución con wasmtime (en la terminal) o con la API `WebAssembly` (en el navegador). |

No se construye un AST propio: todas las fases son `Visitor` sobre el árbol que genera ANTLR.

## El lenguaje

### Características soportadas

- **Tipos**: `i32`, `f64`, `bool`, `char`, `String`, arrays `[T; N]`, tuplas `(T1, T2, ...)`, referencias `&T` y `&mut T`, `struct` y `enum` (con variantes con datos).
- **Declaraciones**: `fn` con parámetros (opcionalmente `mut`) y tipo de retorno, `struct`, `enum`, `const` (global y local), `let` / `let mut` con tipo explícito o inferido, `let x: T;` con asignación posterior.
- **Expresiones**: aritmética (`+ - * / %`), comparaciones, `&&` / `||` (con cortocircuito), `-` y `!` unarios, `&` / `&mut` / `*`, llamadas, campos `p.x`, índices `a[i]`, literales de struct, enum, array y tupla, bloques `{ ... }` con valor, `match` como expresión.
- **Sentencias**: asignación (`=`, `+=`, `-=`, `*=`, `/=`) a variables, campos e índices; `if` / `else if` / `else` (también como valor al final de un bloque o función); `while`; `loop`; `break`; `continue`; `return`.
- **Match**: patrones comodín `_`, literales, variables, variantes `Enum::Variante(...)` y tuplas, anidados. Se exige exhaustividad.
- **Structs y enums pueden declararse en cualquier orden** (un struct puede usar otro declarado más abajo; una función puede llamar a otra declarada más abajo).
- **Sombreado**: solo en un ámbito interior (`let x` dos veces en el mismo bloque es error).
- **Referencias**: `p.x` funciona con `p: &Punto` o `&mut Punto`; los operadores ven a través de las referencias (`a + 1` con `a: &i32`); un `&mut T` se acepta donde se espera `&T`; en `match r` con `r: &Enum` los patrones comparan el valor referido.

### Funciones predefinidas

RustiQ no tiene `println!`. Para mostrar resultados existen:

| Función | Imprime |
|---|---|
| `print_i32(x: i32)` | un entero |
| `print_f64(x: f64)` | un decimal (`4.0` se muestra como `4.0`) |
| `print_bool(x: bool)` | `true` / `false` |
| `print_char(c: char)` | un carácter |
| `print_str(s: &String)` | un texto; acepta `&s` o directamente un literal `"hola"` |

No se pueden volver a declarar.

### Errores que se detectan

**Semánticos**: variable, función, tipo, campo o variante inexistentes; `let x;` sin tipo ni valor; tipo declarado distinto del valor; operadores con tipos inválidos (no se mezcla `i32` con `f64`); condición de `if`/`while` que no es `bool`; número y tipos de argumentos; tipo de retorno (y función con tipo que no devuelve valor por todos los caminos); campos faltantes, repetidos o de tipo equivocado; variantes con datos incorrectos; índice que no es `i32`, índice constante fuera de rango, elementos de array de tipos distintos, longitud de array; brazos de `match` de tipos distintos, patrón incompatible, `match` no exhaustivo; `break`/`continue` fuera de un bucle; asignar a una `const`; división entre el literal `0`; duplicados (funciones, tipos, campos, variantes, parámetros, variables en el mismo ámbito); falta `main`.

**Ownership**: uso después de mover (también al mover un campo no copiable o dentro de un `if`); mover una variable de fuera de un bucle dentro del bucle; variable sin inicializar (o inicializada solo en una rama); asignar sin `mut`; `&mut` de una variable sin `mut`; modificar a través de `&T`; mover desde una referencia; `&mut` con un `&` activo, dos `&mut`, `&` con `&mut` activo; modificar, mover o leer una variable mientras está prestada; devolver una referencia a una variable local; referencia que sobrevive al bloque de la variable prestada.

Reglas de copia: son copiables `i32`, `f64`, `bool`, `char`, `&T` y los arrays y tuplas de copiables. Se mueven `String`, structs, enums y `&mut T`. Pasar un `&mut T` a una función lo re-presta (no lo mueve), igual que en Rust. Un préstamo guardado en una variable dura hasta el **último uso** de esa variable (como el "non-lexical lifetimes" de Rust); un préstamo temporal (`f(&mut x)`) dura hasta el final de la sentencia.

### Limitaciones y construcciones no soportadas

- **No hay** `impl`, métodos, traits, genéricos, closures, `Vec`, `Option`/`Result`, `for`, `println!`, módulos ni `use`.
- **La gramática exige `;` después de un `match` usado como sentencia** (`match x { ... };`). Un `match` al final de un bloque sin `;` es su valor.
- **No se puede asignar a través de un deref** (`*r = 5` no está en la gramática). Para modificar a través de `&mut` se usa un struct: `p.x = 5` con `p: &mut Punto`.
- **No se puede leer un elemento de tupla con `t.0`** (la gramática no lo permite): se usa `match t { (a, b) => ... }`.
- **No hay patrones de texto** (`"hola" =>`) en `match`; sobre `String` solo sirven `_` y variables.
- `String` solo se crea desde literales; no hay concatenación ni comparación de `String`.
- Los literales enteros siempre son `i32` y los decimales `f64`; no hay conversiones entre tipos.
- `const` solo acepta expresiones con tipo explícito; su valor se calcula al iniciar `main`.
- Los arrays tienen longitud fija y los índices se revisan en ejecución (índice fuera de rango detiene el programa).
- Movimientos parciales: mover un campo (`let n = u.nombre;`) se trata como mover toda la variable.
- El analizador de ownership trabaja por función y no sigue referencias guardadas dentro de structs.
- La memoria del programa nunca se libera (asignador que solo avanza); suficiente para programas de prueba.
- wasmtime se usa con el intérprete Pulley: el Python de Apple (Xcode Command Line Tools) no permite código JIT y macOS mataba el proceso al ejecutar Wasm compilado nativamente.

## Estructura

```
compilador/
  RustiQ.g4                 gramática ANTLR4
  generado/                 lexer, parser y visitor generados para Python
  errores.py                errores con fase, línea y columna
  tipos.py                  tipos y reglas de operadores
  tabla_simbolos.py         ámbitos, variables, funciones, structs y enums
  recolector.py             fase semántica 1: declaraciones de nivel superior
  verificador_tipos.py      fase semántica 2: tipos, llamadas, match, exhaustividad
  analizador_ownership.py   fase 3: movimientos, mutabilidad y préstamos
  memoria.py                representación de los valores en la memoria de Wasm
  generador_wat.py          árbol de ANTLR -> WAT
  ejecutor_wasm.py          WAT -> .wasm, validación y ejecución con wasmtime
  correr.py                 cadena completa desde la terminal
  probar.py                 solo análisis (muestra errores)
  ejemplos/                 programas de ejemplo (ejemplos/wasm/ con salida esperada)
  tests/                    pruebas (validos/, invalidos/semantico/, invalidos/ownership/)
web/
  server.py                 servidor Flask (sirve el editor y la API)
  frontend/                 editor en React (Vite + CodeMirror)
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

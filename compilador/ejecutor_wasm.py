"""
EJECUTOR: texto WAT -> binario .wasm -> validación -> ejecución (con wasmtime).

[DEFENSA] Los tres pasos que pide el enunciado:
    1. wat_a_wasm  convierte el texto WAT al binario .wasm real
    2. validar     revisa que el módulo sea correcto (tipos y pila); si el
                   generador escribiera algo mal, se detecta aquí
    3. ejecutar    corre main() en wasmtime, un runtime de Wasm fuera del navegador

El navegador hace lo mismo en web/frontend/src/ejecutor.worker.js.
"""
import wasmtime


class ErrorWasm(Exception):
    """Error al convertir, validar o ejecutar un módulo Wasm."""


# [DEFENSA] Un "trap" es un error que ocurre MIENTRAS el programa corre
# (el módulo es válido, pero hace algo imposible). Se traduce al español.
TRAPS = {
    "integer divide by zero": "División entera por cero",
    "out of bounds memory access": "Acceso fuera de la memoria",
    # El generador emite 'unreachable' cuando un índice de array se sale del rango.
    "wasm `unreachable` instruction executed": "Índice de array fuera de rango",
}


def leer_string(caller, puntero):
    """Un String en memoria es [ largo (4 bytes) ][ bytes UTF-8 ] (ver memoria.py)."""
    memoria = caller["memory"]
    largo = int.from_bytes(memoria.read(caller, puntero, puntero + 4), "little")
    return memoria.read(caller, puntero + 4, puntero + 4 + largo).decode("utf-8")


def wat_a_wasm(texto_wat):
    """Paso 1: texto WAT -> bytes .wasm (empiezan con \\0asm). Solo traduce, no revisa tipos."""
    try:
        return wasmtime.wat2wasm(texto_wat)
    except wasmtime.WasmtimeError as e:
        raise ErrorWasm(f"El WAT generado no se pudo convertir: {e}")


def validar(bytes_wasm):
    """Paso 2: valida el módulo (que cada instrucción tenga en la pila los valores que necesita)."""
    try:
        wasmtime.Module.validate(wasmtime.Engine(), bytes_wasm)
    except wasmtime.WasmtimeError as e:
        raise ErrorWasm(f"El módulo .wasm no es válido: {e}")


def formatear_f64(valor):
    """4.0 se muestra como 4.0 (no 4); el navegador usa la misma regla."""
    if valor == int(valor):
        return f"{valor:.1f}"
    return repr(valor)


def ejecutar(bytes_wasm):
    """
    Paso 3: instancia el módulo y llama a main. Devuelve la lista de líneas impresas.
    [DEFENSA] linker.define_func es el "préstamo": cuando el módulo llama a
    env.print_i32, wasmtime ejecuta la función de Python que se registra aquí.
    """
    engine = wasmtime.Engine()
    store = wasmtime.Store(engine)
    modulo = wasmtime.Module(engine, bytes_wasm)
    linker = wasmtime.Linker(engine)
    salida = []

    i32 = wasmtime.ValType.i32()
    f64 = wasmtime.ValType.f64()

    linker.define_func("env", "print_i32", wasmtime.FuncType([i32], []),
                       lambda v: salida.append(str(v)))
    linker.define_func("env", "print_f64", wasmtime.FuncType([f64], []),
                       lambda v: salida.append(formatear_f64(v)))
    linker.define_func("env", "print_bool", wasmtime.FuncType([i32], []),
                       lambda v: salida.append("true" if v else "false"))
    linker.define_func("env", "print_char", wasmtime.FuncType([i32], []),
                       lambda v: salida.append(chr(v)))
    linker.define_func("env", "print_str", wasmtime.FuncType([i32], []),
                       lambda caller, p: salida.append(leer_string(caller, p)),
                       access_caller=True)

    instancia = linker.instantiate(store, modulo)
    main = instancia.exports(store)["main"]
    try:
        main(store)
    except wasmtime.Trap as e:
        motivo = e.message.strip().splitlines()[-1].replace("wasm trap: ", "").strip()
        raise ErrorWasm(f"Error en ejecución: {TRAPS.get(motivo, motivo)}") from None
    return salida
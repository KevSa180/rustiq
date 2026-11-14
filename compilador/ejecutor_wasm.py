import wasmtime


class ErrorWasm(Exception):
    """Error al convertir, validar o ejecutar un módulo Wasm."""


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


def motor():
    """
    Motor de wasmtime. Se usa el intérprete Pulley en vez del compilador JIT
    nativo: el Python de Apple (Xcode CLT) no tiene permiso de ejecutar código
    generado en tiempo de ejecución y macOS mata el proceso (SIGKILL) al correr
    Wasm compilado con Cranelift. Pulley funciona en cualquier plataforma y la
    velocidad sobra para programas de prueba. Si la versión de wasmtime no lo
    trae, se usa el motor por defecto.
    """
    config = wasmtime.Config()
    try:
        config.target = "pulley64"
    except wasmtime.WasmtimeError:
        config = wasmtime.Config()
    return wasmtime.Engine(config)


def wat_a_wasm(texto_wat):
    try:
        return wasmtime.wat2wasm(texto_wat)
    except wasmtime.WasmtimeError as e:
        raise ErrorWasm(f"El WAT generado no se pudo convertir: {e}")


def validar(bytes_wasm):
    try:
        wasmtime.Module.validate(motor(), bytes_wasm)
    except wasmtime.WasmtimeError as e:
        raise ErrorWasm(f"El módulo .wasm no es válido: {e}")


def formatear_f64(valor):
    if valor == int(valor):
        return f"{valor:.1f}"
    return repr(valor)


def ejecutar(bytes_wasm):
    engine = motor()
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
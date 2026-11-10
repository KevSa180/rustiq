import wasmtime


class ErrorWasm(Exception):
    """Error al convertir, validar o ejecutar un módulo Wasm."""


TRAPS = {
    "integer divide by zero": "División entera por cero",
    "out of bounds memory access": "Acceso fuera de la memoria",
    "unreachable": "Se llegó a código inalcanzable",
}


def wat_a_wasm(texto_wat):
    try:
        return wasmtime.wat2wasm(texto_wat)
    except wasmtime.WasmtimeError as e:
        raise ErrorWasm(f"El WAT generado no se pudo convertir: {e}")


def validar(bytes_wasm):
    try:
        wasmtime.Module.validate(wasmtime.Engine(), bytes_wasm)
    except wasmtime.WasmtimeError as e:
        raise ErrorWasm(f"El módulo .wasm no es válido: {e}")


def formatear_f64(valor):
    if valor == int(valor):
        return f"{valor:.1f}"
    return repr(valor)


def ejecutar(bytes_wasm):
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

    instancia = linker.instantiate(store, modulo)
    main = instancia.exports(store)["main"]
    try:
        main(store)
    except wasmtime.Trap as e:
        motivo = e.message.strip().splitlines()[-1].replace("wasm trap: ", "").strip()
        raise ErrorWasm(f"Error en ejecución: {TRAPS.get(motivo, motivo)}") from None
    return salida
"""
Compila un programa RustiQ a Wasm y lo ejecuta.

    python correr.py ejemplos/wasm/suma.rq          -> muestra la salida
    python correr.py ejemplos/wasm/suma.rq --wat    -> además muestra el WAT

Guarda el .wat y el .wasm en la carpeta salida/ (evidencia para la defensa).
"""
import os
import sys
from antlr4 import InputStream, CommonTokenStream
from generado.RustiQLexer import RustiQLexer
from generado.RustiQParser import RustiQParser
from errores import ListaErrores, ColectorErrores
from generador_wat import GeneradorWat, ErrorNoSoportado
from ejecutor_wasm import wat_a_wasm, validar, ejecutar, ErrorWasm


def compilar_a_wat(codigo, errores):
    lexer = RustiQLexer(InputStream(codigo))
    lexer.removeErrorListeners()
    lexer.addErrorListener(ColectorErrores("léxico", errores))
    parser = RustiQParser(CommonTokenStream(lexer))
    parser.removeErrorListeners()
    parser.addErrorListener(ColectorErrores("sintáctico", errores))
    arbol = parser.programa()
    if errores.hay_errores():
        return None
    # Aquí irán el recolector, el verificador de tipos y el de ownership.
    try:
        return GeneradorWat().visit(arbol)
    except ErrorNoSoportado as e:
        errores.agregar("generación", e.linea, e.columna, e.mensaje)
        return None


def main():
    ruta = sys.argv[1]
    with open(ruta, encoding="utf-8") as f:
        codigo = f.read()

    errores = ListaErrores()
    wat = compilar_a_wat(codigo, errores)
    if wat is None:
        for e in errores.ordenados():
            print(e)
        sys.exit(1)

    if "--wat" in sys.argv:
        print(wat)
        print("-" * 40)

    try:
        bytes_wasm = wat_a_wasm(wat)
        validar(bytes_wasm)
    except ErrorWasm as e:
        print(f"[wasm] {e}")
        sys.exit(1)

    os.makedirs("salida", exist_ok=True)
    base = os.path.join("salida", os.path.splitext(os.path.basename(ruta))[0])
    with open(base + ".wat", "w", encoding="utf-8") as f:
        f.write(wat)
    with open(base + ".wasm", "wb") as f:
        f.write(bytes_wasm)

    try:
        for linea in ejecutar(bytes_wasm):
            print(linea)
    except ErrorWasm as e:
        print(f"[ejecución] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

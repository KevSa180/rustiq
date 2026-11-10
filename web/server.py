"""
Servidor del editor web de RustiQ.

    python web/server.py      ->  abre http://localhost:5001

- GET  /                 el editor (React ya compilado en frontend/dist)
- GET  /api/ejemplos     los programas de compilador/ejemplos/wasm
- POST /api/compilar     {"codigo": "..."}  ->  errores o el .wasm en base64

Toda la compilación ocurre aquí, en Python. El navegador solo recibe el .wasm
ya generado y lo ejecuta con la API WebAssembly.
"""
import base64
import glob
import os
import sys

from flask import Flask, jsonify, request, send_from_directory

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARPETA_COMPILADOR = os.path.join(RAIZ, "compilador")
CARPETA_EJEMPLOS = os.path.join(CARPETA_COMPILADOR, "ejemplos", "wasm")
CARPETA_FRONTEND = os.path.join(RAIZ, "web", "frontend", "dist")
sys.path.insert(0, CARPETA_COMPILADOR)

from errores import ListaErrores                       # noqa: E402
from correr import compilar_a_wat                      # noqa: E402
from ejecutor_wasm import wat_a_wasm, validar, ErrorWasm  # noqa: E402

app = Flask(__name__, static_folder=CARPETA_FRONTEND, static_url_path="")


def compilar(codigo):
    """Devuelve el diccionario que se envía al navegador."""
    errores = ListaErrores()
    try:
        wat = compilar_a_wat(codigo, errores)
    except Exception as e:  # un fallo del compilador nunca debe verse como éxito
        errores.agregar("interno", 1, 1, f"Error interno del compilador: {type(e).__name__}: {e}")
        wat = None

    if wat is None:
        return {"ok": False, "errores": [e.a_diccionario() for e in errores.ordenados()]}

    try:
        bytes_wasm = wat_a_wasm(wat)
        validar(bytes_wasm)
    except ErrorWasm as e:
        return {"ok": False, "wat": wat,
                "errores": [{"fase": "wasm", "linea": 1, "columna": 1, "mensaje": str(e)}]}

    return {
        "ok": True,
        "wasm": base64.b64encode(bytes_wasm).decode("ascii"),
        "wat": wat,
        "bytes": len(bytes_wasm),
    }


@app.post("/api/compilar")
def api_compilar():
    datos = request.get_json(silent=True) or {}
    codigo = datos.get("codigo")
    if not isinstance(codigo, str):
        return jsonify({"ok": False, "errores": [
            {"fase": "servidor", "linea": 1, "columna": 1, "mensaje": "Falta el código a compilar"}]}), 400
    return jsonify(compilar(codigo))


@app.get("/api/ejemplos")
def api_ejemplos():
    ejemplos = []
    for ruta in sorted(glob.glob(os.path.join(CARPETA_EJEMPLOS, "*.rq")), key=orden_ejemplo):
        with open(ruta, encoding="utf-8") as f:
            ejemplos.append({"nombre": os.path.basename(ruta), "codigo": f.read()})
    return jsonify(ejemplos)


def orden_ejemplo(ruta):
    """paso3, paso4, ..., paso12 en orden numérico; los de error al final."""
    nombre = os.path.basename(ruta)
    if nombre.startswith("paso"):
        numero = "".join(c for c in nombre[4:] if c.isdigit())
        return (0, int(numero or 0), nombre)
    return (1, 0, nombre)


@app.get("/")
def inicio():
    if not os.path.exists(os.path.join(CARPETA_FRONTEND, "index.html")):
        return ("Falta compilar el frontend: cd web/frontend && npm install && npm run build", 500)
    return send_from_directory(CARPETA_FRONTEND, "index.html")


if __name__ == "__main__":
    app.run(port=5001, debug=True)

"""
Corre solo las fases de análisis (sin generar código) y muestra los errores.

    python probar.py ejemplos/error1.rq
"""
import sys
from errores import ListaErrores
from correr import analizar

with open(sys.argv[1], encoding="utf-8") as f:
    codigo = f.read()

errores = ListaErrores()
arbol, tabla = analizar(codigo, errores)

if errores.hay_errores():
    for e in errores.ordenados():
        print(e)
    sys.exit(1)
print("Sin errores")

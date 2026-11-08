import re
from antlr4.error.ErrorListener import ErrorListener

class ErrorCompilador:
    def __init__(self, fase, linea, columna, mensaje):
        self.fase = fase
        self.linea = linea
        self.columna = columna
        self.mensaje = mensaje

    def a_diccionario(self):
        return {
            "fase": self.fase,
            "linea": self.linea,
            "columna": self.columna,
            "mensaje": self.mensaje,
        }

    def __str__(self):
        return f"[{self.fase}] línea {self.linea}, columna {self.columna}: {self.mensaje}"


class ListaErrores:
    def __init__(self):
        self.errores = []

    def agregar(self, fase, linea, columna, mensaje):
        self.errores.append(ErrorCompilador(fase, linea, columna, mensaje))

    def hay_errores(self):
        return len(self.errores) > 0

    def ordenados(self):
        return sorted(self.errores, key=lambda e: (e.linea, e.columna))


def traducir_mensaje(msg):
    m = re.match(r"token recognition error at: (.*)", msg, re.DOTALL)
    if m:
        return f"Símbolo no reconocido: {m.group(1)}"

    m = re.match(r"missing (.+?) at (.+)", msg, re.DOTALL)
    if m:
        return f"Falta {m.group(1)}"

    m = re.match(r"extraneous input (.+?) expecting", msg, re.DOTALL)
    if m:
        if m.group(1) == "'<EOF>'":
            return "El programa termina antes de tiempo (falta cerrar algo)"
        return f"Símbolo sobrante: {m.group(1)}"

    m = re.match(r"mismatched input (.+?) expecting (.+)", msg, re.DOTALL)
    if m:
        encontrado, esperado = m.group(1), m.group(2)
        if encontrado == "'<EOF>'":
            return "El programa termina antes de tiempo (falta cerrar algo)"
        if not esperado.startswith("{"):
            return f"Se encontró {encontrado} pero se esperaba {esperado}"
        return f"Símbolo inesperado: {encontrado}"

    m = re.match(r"no viable alternative at input (.+)", msg, re.DOTALL)
    if m:
        return f"Estructura no válida cerca de: {m.group(1)}"

    return msg


class ColectorErrores(ErrorListener):
    def __init__(self, fase, lista):
        super().__init__()
        self.fase = fase
        self.lista = lista

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        self.lista.agregar(self.fase, line, column + 1, traducir_mensaje(msg))
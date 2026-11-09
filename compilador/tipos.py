class Tipo:
    """Base de todos los tipos de RustiQ."""

    def es_copiable(self):
        return False

    def __eq__(self, otro):
        return isinstance(otro, Tipo) and str(self) == str(otro)

    def __hash__(self):
        return hash(str(self))


class TipoSimple(Tipo):
    """Tipos sin parámetros: i32, f64, bool, char, String, (), <error>."""

    def __init__(self, nombre, copiable):
        self.nombre = nombre
        self._copiable = copiable

    def es_copiable(self):
        return self._copiable

    def __str__(self):
        return self.nombre


I32 = TipoSimple("i32", True)
F64 = TipoSimple("f64", True)
BOOL = TipoSimple("bool", True)
CHAR = TipoSimple("char", True)
STRING = TipoSimple("String", False)
UNIT = TipoSimple("()", True)
ERROR = TipoSimple("<error>", True)

class TipoArray(Tipo):
    def __init__(self, elemento, longitud):
        self.elemento = elemento
        self.longitud = longitud

    def es_copiable(self):
        return self.elemento.es_copiable()

    def __str__(self):
        return f"[{self.elemento}; {self.longitud}]"


class TipoTupla(Tipo):
    def __init__(self, elementos):
        self.elementos = list(elementos)

    def es_copiable(self):
        return all(t.es_copiable() for t in self.elementos)

    def __str__(self):
        return "(" + ", ".join(str(t) for t in self.elementos) + ")"


class TipoReferencia(Tipo):
    def __init__(self, interno, mutable):
        self.interno = interno
        self.mutable = mutable

    def es_copiable(self):
        return not self.mutable

    def __str__(self):
        return f"&mut {self.interno}" if self.mutable else f"&{self.interno}"


class TipoStruct(Tipo):
    def __init__(self, nombre):
        self.nombre = nombre

    def __str__(self):
        return self.nombre


class TipoEnum(Tipo):
    def __init__(self, nombre):
        self.nombre = nombre

    def __str__(self):
        return self.nombre

NUMERICOS = (I32, F64)
COMPARABLES = (I32, F64, BOOL, CHAR)
ORDENABLES = (I32, F64, CHAR)


def resultado_binario(op, t1, t2):
    if t1 == ERROR or t2 == ERROR:
        return ERROR

    if op in ("+", "-", "*", "/", "%"):
        if t1 == t2 and t1 in NUMERICOS:
            return t1
        return ERROR

    if op in ("==", "!="):
        if t1 == t2 and t1 in COMPARABLES:
            return BOOL
        return ERROR

    if op in ("<", "<=", ">", ">="):
        if t1 == t2 and t1 in ORDENABLES:
            return BOOL
        return ERROR

    if op in ("&&", "||"):
        if t1 == BOOL and t2 == BOOL:
            return BOOL
        return ERROR

    return ERROR

def resultado_unario(op, t):
    if t == ERROR:
        return ERROR
    if op == "-" and t in NUMERICOS:
        return t
    if op == "!" and t == BOOL:
        return BOOL
    return ERROR


def compatibles(esperado, real):
    return esperado == ERROR or real == ERROR or esperado == real
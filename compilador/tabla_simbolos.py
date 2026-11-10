class SimboloVariable:
    def __init__(self, nombre, tipo, mutable, linea, columna, es_constante=False):
        self.nombre = nombre
        self.tipo = tipo
        self.mutable = mutable
        self.linea = linea
        self.columna = columna
        self.es_constante = es_constante


class SimboloFuncion:
    def __init__(self, nombre, parametros, retorno, linea, columna):
        self.nombre = nombre
        self.parametros = parametros
        self.retorno = retorno
        self.linea = linea
        self.columna = columna

    def tipos_parametros(self):
        return [p.tipo for p in self.parametros]
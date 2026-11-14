from tipos import TipoStruct, TipoEnum

FASE = "semántico"


# =====================================================
#  SÍMBOLOS: lo que se guarda en la tabla
# =====================================================

class SimboloVariable:
    """Una variable, parámetro o constante."""

    def __init__(self, nombre, tipo, mutable, linea, columna, es_constante=False):
        self.nombre = nombre
        self.tipo = tipo
        self.mutable = mutable
        self.linea = linea
        self.columna = columna
        self.es_constante = es_constante


class SimboloFuncion:
    """Una función: sus parámetros (SimboloVariable) y su tipo de retorno."""

    def __init__(self, nombre, parametros, retorno, linea, columna, predefinida=False):
        self.nombre = nombre
        self.parametros = parametros
        self.retorno = retorno
        self.linea = linea
        self.columna = columna
        self.predefinida = predefinida   # print_i32, print_str... (las presta el entorno)

    def tipos_parametros(self):
        return [p.tipo for p in self.parametros]


class SimboloStruct:
    """Un struct: sus campos en orden (nombre -> tipo)."""

    def __init__(self, nombre, linea, columna):
        self.nombre = nombre
        self.linea = linea
        self.columna = columna
        self.campos = {}
        self.tipo = TipoStruct(nombre)

    def tipo_campo(self, nombre):
        return self.campos.get(nombre)


class SimboloEnum:
    """Un enum: sus variantes en orden (nombre -> lista de tipos de sus datos)."""

    def __init__(self, nombre, linea, columna):
        self.nombre = nombre
        self.linea = linea
        self.columna = columna
        self.variantes = {}
        self.tipo = TipoEnum(nombre)

    def tipos_variante(self, nombre):
        return self.variantes.get(nombre)

    def nombres_variantes(self):
        return list(self.variantes.keys())


# =====================================================
#  TABLA DE SÍMBOLOS
# =====================================================

class TablaSimbolos:
    """
    Guarda variables (por ámbitos), funciones, structs y enums.

    - Las variables viven en una pila de ámbitos: cada bloque { } abre uno.
      El ámbito 0 es el global (ahí van las const globales).
    - Funciones, structs y enums son globales.

    Regla de sombreado de RustiQ: no se puede declarar dos veces el mismo
    nombre en el MISMO ámbito, pero sí en un ámbito interior (la declaración
    interior tapa a la de afuera hasta que se cierra el bloque).
    """

    def __init__(self, errores):
        self.errores = errores
        self.ambitos = [{}]
        self.funciones = {}
        self.structs = {}
        self.enums = {}

    def _error(self, linea, columna, mensaje):
        self.errores.agregar(FASE, linea, columna, mensaje)

    # ----- Ámbitos -----

    def abrir_ambito(self):
        self.ambitos.append({})

    def cerrar_ambito(self):
        if len(self.ambitos) == 1:
            raise RuntimeError("No se puede cerrar el ámbito global")
        self.ambitos.pop()

    def nivel(self):
        return len(self.ambitos) - 1

    # ----- Variables -----

    def insertar_variable(self, simbolo):
        """Devuelve True si se insertó; False (y reporta error) si ya existía en este ámbito."""
        actual = self.ambitos[-1]
        previo = actual.get(simbolo.nombre)
        if previo is not None:
            que = "La constante" if previo.es_constante else "La variable"
            self._error(simbolo.linea, simbolo.columna,
                        f"{que} '{simbolo.nombre}' ya fue declarada en este ámbito "
                        f"(línea {previo.linea})")
            return False
        actual[simbolo.nombre] = simbolo
        return True

    def buscar_en_ambito_actual(self, nombre):
        return self.ambitos[-1].get(nombre)

    def buscar(self, nombre):
        """Busca una variable desde el ámbito más interno hacia el global. None si no existe."""
        for ambito in reversed(self.ambitos):
            if nombre in ambito:
                return ambito[nombre]
        return None

    def resolver_variable(self, nombre, linea, columna):
        """Como buscar(), pero reporta 'no declarada' si no existe."""
        simbolo = self.buscar(nombre)
        if simbolo is None:
            self._error(linea, columna, f"La variable '{nombre}' no está declarada")
        return simbolo

    # ----- Funciones -----

    def insertar_funcion(self, simbolo):
        """Reporta función duplicada y parámetros repetidos."""
        nombres = set()
        for p in simbolo.parametros:
            if p.nombre in nombres:
                self._error(p.linea, p.columna,
                            f"El parámetro '{p.nombre}' está repetido en la función "
                            f"'{simbolo.nombre}'")
            nombres.add(p.nombre)

        previa = self.funciones.get(simbolo.nombre)
        if previa is not None:
            if previa.predefinida:
                self._error(simbolo.linea, simbolo.columna,
                            f"'{simbolo.nombre}' es una función predefinida y no se puede "
                            f"volver a declarar")
            else:
                self._error(simbolo.linea, simbolo.columna,
                            f"La función '{simbolo.nombre}' ya fue declarada "
                            f"(línea {previa.linea})")
            return False
        self.funciones[simbolo.nombre] = simbolo
        return True

    def buscar_funcion(self, nombre):
        return self.funciones.get(nombre)

    def resolver_funcion(self, nombre, linea, columna):
        """Como buscar_funcion(), pero reporta 'no existe' si no está."""
        simbolo = self.buscar_funcion(nombre)
        if simbolo is None:
            self._error(linea, columna, f"La función '{nombre}' no existe")
        return simbolo

    # ----- Structs y enums -----

    def _tipo_ya_existe(self, nombre, linea, columna):
        previo = self.structs.get(nombre) or self.enums.get(nombre)
        if previo is not None:
            self._error(linea, columna,
                        f"El tipo '{nombre}' ya fue declarado (línea {previo.linea})")
            return True
        return False

    def declarar_struct(self, nombre, campos, linea, columna):
        """
        campos: lista de (nombre, tipo, linea, columna) en el orden del código.
        Reporta struct duplicado y campos repetidos. Devuelve el SimboloStruct
        (o None si el nombre ya estaba usado).
        """
        if self._tipo_ya_existe(nombre, linea, columna):
            return None
        simbolo = SimboloStruct(nombre, linea, columna)
        self.structs[nombre] = simbolo
        self.completar_struct(simbolo, campos)
        return simbolo

    def completar_struct(self, simbolo, campos):
        """
        Agrega los campos a un struct ya declarado. El recolector declara primero
        todos los nombres (con campos vacíos) y los completa después, para que un
        struct pueda usar otro declarado más abajo en el archivo.
        """
        for c_nombre, c_tipo, c_linea, c_columna in campos:
            if c_nombre in simbolo.campos:
                self._error(c_linea, c_columna,
                            f"El campo '{c_nombre}' está repetido en el struct '{simbolo.nombre}'")
                continue
            simbolo.campos[c_nombre] = c_tipo

    def declarar_enum(self, nombre, variantes, linea, columna):
        """
        variantes: lista de (nombre, [tipos], linea, columna) en el orden del código.
        Una variante sin datos lleva lista vacía. Reporta enum duplicado y
        variantes repetidas. Devuelve el SimboloEnum (o None).
        """
        if self._tipo_ya_existe(nombre, linea, columna):
            return None
        simbolo = SimboloEnum(nombre, linea, columna)
        self.enums[nombre] = simbolo
        self.completar_enum(simbolo, variantes)
        return simbolo

    def completar_enum(self, simbolo, variantes):
        """Agrega las variantes a un enum ya declarado (ver completar_struct)."""
        for v_nombre, v_tipos, v_linea, v_columna in variantes:
            if v_nombre in simbolo.variantes:
                self._error(v_linea, v_columna,
                            f"La variante '{v_nombre}' está repetida en el enum '{simbolo.nombre}'")
                continue
            simbolo.variantes[v_nombre] = list(v_tipos)

    def buscar_struct(self, nombre):
        return self.structs.get(nombre)

    def buscar_enum(self, nombre):
        return self.enums.get(nombre)

    def tipo_por_nombre(self, nombre, linea, columna):
        """
        Convierte un nombre usado como tipo (ej. 'Punto' en 'p: Punto') en su
        TipoStruct o TipoEnum. Si no existe, reporta el error y devuelve None.
        """
        if nombre in self.structs:
            return self.structs[nombre].tipo
        if nombre in self.enums:
            return self.enums[nombre].tipo
        self._error(linea, columna, f"El tipo '{nombre}' no existe")
        return None

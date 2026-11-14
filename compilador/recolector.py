"""
Primera pasada semántica: el RECOLECTOR.

Recorre solo el nivel superior del programa (structs, enums, constantes y
firmas de funciones) y los registra en la tabla de símbolos. Así, cuando el
verificador de tipos revise el cuerpo de una función, ya conoce todas las
funciones y tipos del programa aunque estén declarados más abajo.

También convierte los nodos de tipo del árbol (`tipo` en la gramática) a los
objetos de tipos.py; esa conversión la usan las demás fases.

Reporta (fase "semántico"):
  - struct, enum, función o constante duplicados (lo hace la tabla);
  - campos, variantes o parámetros repetidos (lo hace la tabla);
  - tipos inexistentes en campos, variantes, parámetros, retornos y constantes;
  - que falte la función main, o que main tenga parámetros o devuelva valor.
"""
from generado.RustiQVisitor import RustiQVisitor
from generado.RustiQParser import RustiQParser as P
from tabla_simbolos import SimboloVariable, SimboloFuncion
import tipos as T

FASE = "semántico"

PRIMITIVOS = {"i32": T.I32, "f64": T.F64, "bool": T.BOOL, "char": T.CHAR}

# Funciones que el entorno (Python o el navegador) le presta a todo programa.
# print_str recibe una referencia para no consumir el String al imprimirlo.
PREDEFINIDAS = [
    ("print_i32", T.I32),
    ("print_f64", T.F64),
    ("print_bool", T.BOOL),
    ("print_char", T.CHAR),
    ("print_str", T.TipoReferencia(T.STRING, False)),
]


def posicion(ctx):
    """(línea, columna) del primer token de un nodo; la columna empieza en 1."""
    return ctx.start.line, ctx.start.column + 1


def posicion_token(token):
    return token.symbol.line, token.symbol.column + 1


def convertir_tipo(ctx, tabla):
    """
    Nodo `tipo` del árbol -> objeto de tipos.py.
    Si un nombre no existe, la tabla reporta el error y aquí se devuelve
    T.ERROR (un tipo comodín que no genera más errores en cadena).
    """
    if isinstance(ctx, P.TipoPrimContext):
        return PRIMITIVOS[ctx.getText()]
    if isinstance(ctx, P.TipoStringContext):
        return T.STRING
    if isinstance(ctx, P.TipoArrContext):
        arr = ctx.tipoArray()
        return T.TipoArray(convertir_tipo(arr.tipo(), tabla), int(arr.INT_LIT().getText()))
    if isinstance(ctx, P.TipoTupContext):
        return T.TipoTupla([convertir_tipo(t, tabla) for t in ctx.tipoTupla().tipo()])
    if isinstance(ctx, P.TipoRefContext):
        ref = ctx.tipoReferencia()
        return T.TipoReferencia(convertir_tipo(ref.tipo(), tabla), ref.MUT() is not None)
    # TipoNombre: un struct o un enum
    linea, columna = posicion(ctx)
    tipo = tabla.tipo_por_nombre(ctx.getText(), linea, columna)
    return tipo if tipo is not None else T.ERROR


class Recolector(RustiQVisitor):
    def __init__(self, tabla, errores):
        self.tabla = tabla
        self.errores = errores

    def error(self, ctx, mensaje):
        linea, columna = posicion(ctx)
        self.errores.agregar(FASE, linea, columna, mensaje)

    def visitPrograma(self, ctx):
        declaraciones = [item.getChild(0) for item in ctx.item()]
        structs = [d for d in declaraciones if isinstance(d, P.DeclStructContext)]
        enums = [d for d in declaraciones if isinstance(d, P.DeclEnumContext)]
        funciones = [d for d in declaraciones if isinstance(d, P.DeclFuncionContext)]
        constantes = [d for d in declaraciones if isinstance(d, P.DeclConstContext)]

        # 1) Primero solo los NOMBRES de structs y enums (con campos vacíos),
        #    para que un campo pueda referirse a un tipo declarado más abajo.
        simbolos = {}
        for s in structs:
            linea, columna = posicion_token(s.ID())
            simbolos[s] = self.tabla.declarar_struct(s.ID().getText(), [], linea, columna)
        for e in enums:
            linea, columna = posicion_token(e.ID())
            simbolos[e] = self.tabla.declarar_enum(e.ID().getText(), [], linea, columna)

        # 2) Ahora sí los campos y las variantes, con sus tipos ya convertidos.
        for s in structs:
            if simbolos[s] is not None:
                self.tabla.completar_struct(simbolos[s], self.campos_de(s))
        for e in enums:
            if simbolos[e] is not None:
                self.tabla.completar_enum(simbolos[e], self.variantes_de(e))

        # 3) Funciones predefinidas, luego las firmas del programa.
        for nombre, tipo_param in PREDEFINIDAS:
            parametro = SimboloVariable("valor", tipo_param, False, 0, 0)
            self.tabla.insertar_funcion(SimboloFuncion(nombre, [parametro], T.UNIT, 0, 0,
                                                       predefinida=True))
        for f in funciones:
            self.visit(f)

        # 4) Constantes globales (su valor lo revisa el verificador de tipos).
        for c in constantes:
            self.visit(c)

        self.revisar_main()
        return None

    # ----- Structs y enums -----

    def campos_de(self, ctx):
        campos = []
        for c in ctx.declCampo():
            linea, columna = posicion_token(c.ID())
            campos.append((c.ID().getText(), convertir_tipo(c.tipo(), self.tabla), linea, columna))
        return campos

    def variantes_de(self, ctx):
        variantes = []
        for v in ctx.variante():
            linea, columna = posicion_token(v.ID())
            tipos = []
            if v.listaTipos():
                tipos = [convertir_tipo(t, self.tabla) for t in v.listaTipos().tipo()]
            variantes.append((v.ID().getText(), tipos, linea, columna))
        return variantes

    # ----- Funciones y constantes -----

    def visitDeclFuncion(self, ctx):
        parametros = []
        if ctx.listaParametros():
            for p in ctx.listaParametros().parametro():
                linea, columna = posicion_token(p.ID())
                simbolo = SimboloVariable(p.ID().getText(), convertir_tipo(p.tipo(), self.tabla),
                                          p.MUT() is not None, linea, columna)
                p.simbolo = simbolo          # el verificador lo inserta en el ámbito de la función
                parametros.append(simbolo)
        retorno = convertir_tipo(ctx.tipo(), self.tabla) if ctx.tipo() else T.UNIT
        linea, columna = posicion_token(ctx.ID())
        simbolo = SimboloFuncion(ctx.ID().getText(), parametros, retorno, linea, columna)
        ctx.simbolo = simbolo
        self.tabla.insertar_funcion(simbolo)
        return None

    def visitDeclConst(self, ctx):
        linea, columna = posicion_token(ctx.ID())
        tipo = convertir_tipo(ctx.tipo(), self.tabla)
        simbolo = SimboloVariable(ctx.ID().getText(), tipo, False, linea, columna, es_constante=True)
        ctx.simbolo = simbolo
        self.tabla.insertar_variable(simbolo)
        return None

    def revisar_main(self):
        main = self.tabla.buscar_funcion("main")
        if main is None:
            self.errores.agregar(FASE, 1, 1, "El programa no tiene función 'main'")
            return
        if main.parametros:
            self.errores.agregar(FASE, main.linea, main.columna,
                                 "La función 'main' no puede recibir parámetros")
        if main.retorno != T.UNIT:
            self.errores.agregar(FASE, main.linea, main.columna,
                                 "La función 'main' no puede devolver un valor")

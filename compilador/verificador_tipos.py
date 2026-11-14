"""
Segunda pasada semántica: el VERIFICADOR DE TIPOS.

Recorre los cuerpos de las funciones con la tabla que llenó el recolector.
Cada visit de una expresión DEVUELVE su tipo (objeto de tipos.py) y además lo
deja anotado en el propio nodo del árbol de ANTLR (`nodo.tipo`), junto con el
símbolo resuelto en los identificadores (`nodo.simbolo`). Esas anotaciones
las usan el analizador de ownership y el generador; así no hace falta un AST
propio.

Cuando algo falla se reporta el error (fase "semántico") y la expresión queda
con el tipo comodín T.ERROR, que es compatible con todo: así un solo error no
produce una cascada de mensajes.

Reglas de conveniencia (como en Rust):
  - Los accesos a campos/índices y los operadores "ven a través" de las
    referencias: si p: &Punto, p.x es f64; si a: &i32, a + 1 es i32.
  - Un `&mut T` se acepta donde se espera `&T`.
  - En un match sobre una referencia, los patrones se comparan con el valor
    referido y las variables del patrón toman el tipo interno.
"""
from generado.RustiQVisitor import RustiQVisitor
from generado.RustiQParser import RustiQParser as P
from tabla_simbolos import SimboloVariable
from recolector import convertir_tipo, posicion, posicion_token
import tipos as T

FASE = "semántico"
REF_STRING = T.TipoReferencia(T.STRING, False)


def sin_referencia(tipo):
    while isinstance(tipo, T.TipoReferencia):
        tipo = tipo.interno
    return tipo


def asignable(esperado, real):
    """¿Se puede usar un valor de tipo `real` donde se espera `esperado`?"""
    if T.compatibles(esperado, real):
        return True
    # &mut T se puede usar como &T
    return (isinstance(esperado, T.TipoReferencia) and isinstance(real, T.TipoReferencia)
            and not esperado.mutable and real.mutable
            and T.compatibles(esperado.interno, real.interno))


# =====================================================
#  ¿Un bloque termina siempre con return/break/continue?
#  (Entonces no necesita producir un valor.)
# =====================================================

def termina_bloque(ctx):
    return any(termina_sentencia(s) for s in ctx.sentencia())


def termina_sentencia(ctx):
    hijo = ctx.getChild(0)
    if isinstance(hijo, (P.SentenciaReturnContext, P.SentenciaBreakContext,
                         P.SentenciaContinueContext)):
        return True
    if isinstance(hijo, P.BloqueContext):
        return termina_bloque(hijo)
    if isinstance(hijo, P.SentenciaIfContext):
        return termina_if(hijo)
    if isinstance(hijo, P.SentenciaLoopContext):
        return not contiene_break(hijo.bloque())
    return False


def termina_if(ctx):
    if not ctx.ELSE() or not termina_bloque(ctx.bloque(0)):
        return False
    if ctx.sentenciaIf():
        return termina_if(ctx.sentenciaIf())
    return termina_bloque(ctx.bloque(1))


def contiene_break(nodo):
    """¿Hay un break que salga de ESTE bucle? (no cuenta los de bucles internos)"""
    if isinstance(nodo, P.SentenciaBreakContext):
        return True
    if isinstance(nodo, (P.SentenciaWhileContext, P.SentenciaLoopContext)):
        return False
    if nodo.getChildCount() == 0:
        return False
    return any(contiene_break(h) for h in nodo.getChildren())


def if_completo(ctx):
    """¿Este if tiene else en todas sus ramas? Solo así puede producir un valor."""
    if not ctx.ELSE():
        return False
    if ctx.sentenciaIf():
        return if_completo(ctx.sentenciaIf())
    return True


def primario_directo(expresion):
    """Si la expresión es solo un primario (sin operadores ni sufijos), lo devuelve."""
    nodo = expresion
    while nodo.getChildCount() == 1 and not isinstance(nodo, P.PostfijoContext):
        nodo = nodo.getChild(0)
    if isinstance(nodo, P.PostfijoContext) and nodo.getChildCount() == 1:
        return nodo.primario()
    return None


def es_bloque(expresion):
    """¿La expresión es directamente un bloque { ... }? Devuelve el bloque o None."""
    primario = primario_directo(expresion)
    return primario.bloque() if isinstance(primario, P.PrimBloqueContext) else None


def es_literal_texto(expresion):
    primario = primario_directo(expresion)
    return isinstance(primario, P.PrimLiteralContext) \
        and isinstance(primario.literal(), P.LitTextoContext)


def termina_expresion(expresion):
    bloque = es_bloque(expresion)
    return bloque is not None and termina_bloque(bloque)


# =====================================================
#  El verificador
# =====================================================

class VerificadorTipos(RustiQVisitor):
    def __init__(self, tabla, errores):
        self.tabla = tabla
        self.errores = errores
        self.funcion = None          # SimboloFuncion que se está revisando
        self.bucles = 0              # profundidad de while/loop (para break/continue)

    # ----- Utilidades -----

    def visit(self, nodo):
        resultado = nodo.accept(self)
        if isinstance(resultado, T.Tipo):
            nodo.tipo = resultado
        return resultado

    def error(self, ctx, mensaje):
        linea, columna = posicion(ctx)
        self.errores.agregar(FASE, linea, columna, mensaje)
        return T.ERROR

    def error_token(self, token, mensaje):
        linea, columna = posicion_token(token)
        self.errores.agregar(FASE, linea, columna, mensaje)
        return T.ERROR

    def declarar(self, ctx, nombre, tipo, mutable, token, es_constante=False):
        linea, columna = posicion_token(token)
        simbolo = SimboloVariable(nombre, tipo, mutable, linea, columna, es_constante)
        ctx.simbolo = simbolo
        self.tabla.insertar_variable(simbolo)
        return simbolo

    # ----- Programa y funciones -----

    def visitPrograma(self, ctx):
        for item in ctx.item():
            self.visit(item.getChild(0))
        return None

    def visitDeclStruct(self, ctx):
        return None

    def visitDeclEnum(self, ctx):
        return None

    def visitDeclConst(self, ctx):
        self.revisar_constante(ctx, ctx.simbolo)
        return None

    def revisar_constante(self, ctx, simbolo):
        tipo = self.visit(ctx.expresion())
        if not asignable(simbolo.tipo, tipo):
            self.error(ctx.expresion(),
                       f"La constante '{simbolo.nombre}' se declaró como {simbolo.tipo} "
                       f"pero se le asigna {tipo}")

    def visitDeclFuncion(self, ctx):
        self.funcion = ctx.simbolo
        self.bucles = 0
        self.tabla.abrir_ambito()
        if ctx.listaParametros():
            for p in ctx.listaParametros().parametro():
                self.tabla.insertar_variable(p.simbolo)

        retorno = self.funcion.retorno
        tipo_cuerpo = self.tipo_bloque(ctx.bloque(), retorno != T.UNIT)
        if retorno == T.UNIT:
            if tipo_cuerpo not in (T.UNIT, T.ERROR):
                self.error(ctx.bloque().expresion(),
                           f"La función '{self.funcion.nombre}' no declara tipo de retorno "
                           f"pero su cuerpo produce un valor de tipo {tipo_cuerpo}")
        elif not asignable(retorno, tipo_cuerpo) and not termina_bloque(ctx.bloque()):
            if tipo_cuerpo == T.UNIT:
                self.error_token(ctx.ID(),
                                 f"La función '{self.funcion.nombre}' debe devolver {retorno} "
                                 f"pero no todos los caminos devuelven un valor")
            else:
                self.error(ctx.bloque().expresion() or ctx.bloque(),
                           f"La función '{self.funcion.nombre}' devuelve {retorno} "
                           f"pero su cuerpo produce {tipo_cuerpo}")
        self.tabla.cerrar_ambito()
        self.funcion = None
        return None

    # ----- Bloques y sentencias -----

    def tipo_bloque(self, ctx, quiere_valor):
        """
        Revisa { sentencias; expresion_final } en un ámbito nuevo y devuelve el
        tipo del valor que produce: el de la expresión final; si no hay, el de
        un if-else final (solo cuando quiere_valor); si no, ().
        """
        self.tabla.abrir_ambito()
        sentencias = ctx.sentencia()
        tipo = T.UNIT
        if ctx.expresion():
            for s in sentencias:
                self.visit(s)
            tipo = self.visit(ctx.expresion())
        elif quiere_valor and sentencias and sentencias[-1].sentenciaIf() \
                and if_completo(sentencias[-1].sentenciaIf()):
            for s in sentencias[:-1]:
                self.visit(s)
            tipo = self.tipo_if(sentencias[-1].sentenciaIf(), True)
        else:
            for s in sentencias:
                self.visit(s)
        self.tabla.cerrar_ambito()
        ctx.tipo = tipo
        return tipo

    def visitBloque(self, ctx):
        return self.tipo_bloque(ctx, False)

    def visitSentencia(self, ctx):
        self.visit(ctx.getChild(0))
        return None

    def visitDeclLet(self, ctx):
        nombre = ctx.ID().getText()
        tipo_declarado = convertir_tipo(ctx.tipo(), self.tabla) if ctx.tipo() else None
        if ctx.expresion():
            tipo_valor = self.visit(ctx.expresion())    # antes de declararla: let x = x + 1;
            if tipo_declarado is not None:
                if not asignable(tipo_declarado, tipo_valor):
                    self.error(ctx.expresion(),
                               f"La variable '{nombre}' se declaró como {tipo_declarado} "
                               f"pero se le asigna {tipo_valor}")
                tipo = tipo_declarado
            else:
                tipo = tipo_valor
                if tipo == T.UNIT:
                    tipo = self.error(ctx.expresion(),
                                      f"La expresión no produce ningún valor para guardar en '{nombre}'")
        elif tipo_declarado is None:
            tipo = self.error_token(ctx.ID(),
                                    f"La variable '{nombre}' necesita un tipo o un valor inicial")
        else:
            tipo = tipo_declarado
        self.declarar(ctx, nombre, tipo, ctx.MUT() is not None, ctx.ID())
        return None

    def visitDeclConstLocal(self, ctx):
        tipo = convertir_tipo(ctx.tipo(), self.tabla)
        simbolo = SimboloVariable(ctx.ID().getText(), tipo, False, 0, 0, es_constante=True)
        simbolo.linea, simbolo.columna = posicion_token(ctx.ID())
        self.revisar_constante(ctx, simbolo)
        ctx.simbolo = simbolo
        self.tabla.insertar_variable(simbolo)
        return None

    def visitAsignacion(self, ctx):
        tipo_lugar = self.visit(ctx.lugar())
        tipo_valor = self.visit(ctx.expresion())
        op = ctx.opAsignacion().getText()
        texto = ctx.lugar().getText()
        if op == "=":
            if not asignable(tipo_lugar, tipo_valor):
                self.error(ctx.expresion(),
                           f"No se puede asignar {tipo_valor} a '{texto}', que es de tipo {tipo_lugar}")
        else:
            a, b = sin_referencia(tipo_lugar), sin_referencia(tipo_valor)
            if T.resultado_binario(op[0], a, b) == T.ERROR and T.ERROR not in (a, b):
                self.error(ctx.opAsignacion(), f"No se puede aplicar '{op}' a {a} y {b}")
        return None

    def visitLugar(self, ctx):
        """x, p.campo, a[i], p.lista[2]...  Devuelve el tipo del lugar."""
        token = ctx.ID(0)
        linea, columna = posicion_token(token)
        simbolo = self.tabla.resolver_variable(token.getText(), linea, columna)
        ctx.simbolo = simbolo
        if simbolo is None:
            tipo = T.ERROR
        else:
            tipo = simbolo.tipo
            if simbolo.es_constante:
                tipo = self.error_token(token, f"No se puede asignar a la constante '{simbolo.nombre}'")
        hijos = list(ctx.getChildren())[1:]
        i = 0
        while i < len(hijos):
            if hijos[i].getText() == ".":
                tipo = self.tipo_campo(tipo, hijos[i + 1])
                i += 2
            else:
                tipo = self.tipo_indice(tipo, hijos[i + 1], hijos[i])
                i += 3
        return tipo

    def visitSentenciaReturn(self, ctx):
        nombre, retorno = self.funcion.nombre, self.funcion.retorno
        if ctx.expresion():
            tipo = self.visit(ctx.expresion())
            if retorno == T.UNIT:
                self.error(ctx.expresion(),
                           f"La función '{nombre}' no devuelve valor pero este 'return' lleva uno")
            elif not asignable(retorno, tipo):
                self.error(ctx.expresion(),
                           f"La función '{nombre}' devuelve {retorno} pero este 'return' lleva {tipo}")
        elif retorno != T.UNIT:
            self.error(ctx, f"La función '{nombre}' debe devolver {retorno} pero este 'return' "
                            f"no lleva valor")
        return None

    def visitSentenciaBreak(self, ctx):
        if self.bucles == 0:
            self.error(ctx, "'break' fuera de un bucle")
        return None

    def visitSentenciaContinue(self, ctx):
        if self.bucles == 0:
            self.error(ctx, "'continue' fuera de un bucle")
        return None

    def revisar_condicion(self, ctx, palabra):
        tipo = self.visit(ctx)
        if sin_referencia(tipo) not in (T.BOOL, T.ERROR):
            self.error(ctx, f"La condición del {palabra} debe ser bool, no {tipo}")

    def visitSentenciaWhile(self, ctx):
        self.revisar_condicion(ctx.expresion(), "while")
        self.bucles += 1
        self.tipo_bloque(ctx.bloque(), False)
        self.bucles -= 1
        return None

    def visitSentenciaLoop(self, ctx):
        self.bucles += 1
        self.tipo_bloque(ctx.bloque(), False)
        self.bucles -= 1
        return None

    def visitSentenciaIf(self, ctx):
        self.tipo_if(ctx, False)
        return None

    def tipo_if(self, ctx, quiere_valor):
        """
        if c { a } else { b }. Cuando quiere_valor, las ramas deben producir el
        mismo tipo (una rama que siempre hace return/break no cuenta).
        """
        self.revisar_condicion(ctx.expresion(), "if")
        ramas = [(ctx.bloque(0), self.tipo_bloque(ctx.bloque(0), quiere_valor))]
        tipo = T.UNIT
        if ctx.ELSE():
            if ctx.sentenciaIf():
                otro = ctx.sentenciaIf()
                ramas.append((otro, self.tipo_if(otro, quiere_valor)))
            else:
                ramas.append((ctx.bloque(1), self.tipo_bloque(ctx.bloque(1), quiere_valor)))
        if quiere_valor:
            tipo = self.unificar(ramas, "Las ramas del if")
        ctx.tipo = tipo
        return tipo

    def unificar(self, ramas, que):
        """ramas: lista de (nodo, tipo). Todas deben coincidir salvo las que terminan."""
        tipo = None
        for nodo, t in ramas:
            if t == T.ERROR:
                return T.ERROR
            diverge = termina_bloque(nodo) if isinstance(nodo, P.BloqueContext) else \
                termina_if(nodo) if isinstance(nodo, P.SentenciaIfContext) else \
                termina_expresion(nodo)
            if diverge:
                continue
            if tipo is None:
                tipo = t
            elif t != tipo:
                return self.error(nodo, f"{que} tienen tipos distintos: {tipo} y {t}")
        return tipo if tipo is not None else T.UNIT

    # ----- Expresiones -----

    def visitExpresion(self, ctx):
        return self.visit(ctx.disyuncion())

    def binaria_logica(self, operandos, operadores, op):
        tipo = self.visit(operandos[0])
        for i, siguiente in enumerate(operandos[1:]):
            otro = self.visit(siguiente)
            a, b = sin_referencia(tipo), sin_referencia(otro)
            tipo = T.resultado_binario(op, a, b)
            if tipo == T.ERROR and T.ERROR not in (a, b):
                self.error_token(operadores[i], f"'{op}' necesita dos bool, no {a} y {b}")
        return tipo

    def visitDisyuncion(self, ctx):
        return self.binaria_logica(ctx.conjuncion(), ctx.OROR(), "||")

    def visitConjuncion(self, ctx):
        return self.binaria_logica(ctx.comparacion(), ctx.ANDAND(), "&&")

    def visitComparacion(self, ctx):
        tipo = self.visit(ctx.suma(0))
        if not ctx.opRelacional():
            return tipo
        otro = self.visit(ctx.suma(1))
        a, b = sin_referencia(tipo), sin_referencia(otro)
        op = ctx.opRelacional().getText()
        resultado = T.resultado_binario(op, a, b)
        if resultado == T.ERROR and T.ERROR not in (a, b):
            if a == b:
                self.error(ctx.opRelacional(), f"No se puede aplicar '{op}' a valores de tipo {a}")
            else:
                self.error(ctx.opRelacional(), f"No se puede comparar {a} con {b}")
        return resultado

    def binaria_aritmetica(self, ctx):
        hijos = list(ctx.getChildren())
        tipo = self.visit(hijos[0])
        for i in range(1, len(hijos), 2):
            op = hijos[i].getText()
            otro = self.visit(hijos[i + 1])
            a, b = sin_referencia(tipo), sin_referencia(otro)
            resultado = T.resultado_binario(op, a, b)
            if resultado == T.ERROR and T.ERROR not in (a, b):
                self.error_token(hijos[i], f"No se puede aplicar '{op}' a {a} y {b}")
            elif op in ("/", "%") and a == T.I32 and hijos[i + 1].getText().strip("()") == "0":
                self.error(hijos[i + 1], "División entera por cero")
            tipo = resultado
        return tipo

    def visitSuma(self, ctx):
        return self.binaria_aritmetica(ctx)

    def visitProducto(self, ctx):
        return self.binaria_aritmetica(ctx)

    def visitUnarioNegativo(self, ctx):
        tipo = sin_referencia(self.visit(ctx.unario()))
        resultado = T.resultado_unario("-", tipo)
        if resultado == T.ERROR and tipo != T.ERROR:
            self.error(ctx, f"No se puede aplicar '-' a un valor de tipo {tipo}")
        return resultado

    def visitUnarioNegacion(self, ctx):
        tipo = sin_referencia(self.visit(ctx.unario()))
        resultado = T.resultado_unario("!", tipo)
        if resultado == T.ERROR and tipo != T.ERROR:
            self.error(ctx, f"No se puede aplicar '!' a un valor de tipo {tipo}")
        return resultado

    def visitUnarioRef(self, ctx):
        tipo = self.visit(ctx.unario())
        return T.ERROR if tipo == T.ERROR else T.TipoReferencia(tipo, False)

    def visitUnarioRefMut(self, ctx):
        tipo = self.visit(ctx.unario())
        return T.ERROR if tipo == T.ERROR else T.TipoReferencia(tipo, True)

    def visitUnarioDeref(self, ctx):
        tipo = self.visit(ctx.unario())
        if isinstance(tipo, T.TipoReferencia):
            return tipo.interno
        if tipo == T.ERROR:
            return T.ERROR
        return self.error(ctx, f"No se puede desreferenciar un valor de tipo {tipo} "
                               f"(no es una referencia)")

    def visitUnarioPostfijo(self, ctx):
        return self.visit(ctx.postfijo())

    def visitPostfijo(self, ctx):
        """primario seguido de llamadas f(...), campos .x e índices [i]."""
        primario, *sufijos = list(ctx.getChildren())

        if sufijos and isinstance(sufijos[0], P.SufijoLlamadaContext):
            if isinstance(primario, P.PrimIdentContext):
                tipo = self.revisar_llamada(primario, sufijos[0])
            else:
                self.visitar_argumentos(sufijos[0])
                tipo = self.error(ctx, "Solo se puede llamar a una función por su nombre")
            sufijos = sufijos[1:]
        else:
            tipo = self.visit(primario)

        for sufijo in sufijos:
            if isinstance(sufijo, P.SufijoLlamadaContext):
                self.visitar_argumentos(sufijo)
                tipo = self.error(sufijo, "RustiQ no tiene métodos: solo se puede llamar a una "
                                          "función por su nombre")
            elif isinstance(sufijo, P.SufijoCampoContext):
                tipo = self.tipo_campo(tipo, sufijo.ID())
            else:
                tipo = self.tipo_indice(tipo, sufijo.expresion(), sufijo)
            sufijo.tipo = tipo
        return tipo

    def tipo_campo(self, tipo, token_campo):
        campo = token_campo.getText()
        base = sin_referencia(tipo)
        if base == T.ERROR:
            return T.ERROR
        if isinstance(base, T.TipoStruct):
            struct = self.tabla.buscar_struct(base.nombre)
            tipo_campo = struct.tipo_campo(campo)
            if tipo_campo is None:
                return self.error_token(token_campo,
                                        f"El struct '{base.nombre}' no tiene el campo '{campo}'")
            return tipo_campo
        if isinstance(base, T.TipoTupla):
            return self.error_token(token_campo,
                                    "RustiQ no permite leer los elementos de una tupla con '.'; "
                                    "use un match con patrón de tupla")
        return self.error_token(token_campo,
                                f"Un valor de tipo {base} no tiene campos (se pidió '{campo}')")

    def tipo_indice(self, tipo, expresion_indice, nodo):
        tipo_i = self.visit(expresion_indice)
        if sin_referencia(tipo_i) not in (T.I32, T.ERROR):
            self.error(expresion_indice, f"El índice de un array debe ser i32, no {tipo_i}")
        base = sin_referencia(tipo)
        if base == T.ERROR:
            return T.ERROR
        if not isinstance(base, T.TipoArray):
            return self.error(nodo, f"No se puede indexar un valor de tipo {base} (no es un array)")
        texto = expresion_indice.getText()
        if texto.isdigit() and int(texto) >= base.longitud:
            self.error(expresion_indice,
                       f"El índice {texto} está fuera del rango del array {base} "
                       f"(índices válidos: 0 a {base.longitud - 1})")
        return base.elemento

    def visitar_argumentos(self, sufijo):
        argumentos = sufijo.listaArgumentos().expresion() if sufijo.listaArgumentos() else []
        return [(a, self.visit(a)) for a in argumentos]

    def revisar_llamada(self, primario, sufijo):
        token = primario.ID()
        nombre = token.getText()
        linea, columna = posicion_token(token)
        funcion = self.tabla.resolver_funcion(nombre, linea, columna)
        primario.funcion = funcion
        argumentos = self.visitar_argumentos(sufijo)
        if funcion is None:
            return T.ERROR
        esperados = funcion.parametros
        if len(argumentos) != len(esperados):
            return self.error_token(token,
                                    f"La función '{nombre}' espera {len(esperados)} argumento(s) "
                                    f"pero recibe {len(argumentos)}")
        for i, ((nodo, tipo), parametro) in enumerate(zip(argumentos, esperados), start=1):
            # Un literal de texto se acepta donde se espera &String (como el &str de Rust):
            # print_str("hola") no necesita escribir print_str(&"hola").
            if tipo == T.STRING and parametro.tipo == REF_STRING and es_literal_texto(nodo):
                continue
            if not asignable(parametro.tipo, tipo):
                self.error(nodo, f"El argumento {i} de '{nombre}' debe ser {parametro.tipo}, "
                                 f"no {tipo}")
        return funcion.retorno

    # ----- Primarios -----

    def visitPrimLiteral(self, ctx):
        return self.visit(ctx.literal())

    def visitPrimParen(self, ctx):
        return self.visit(ctx.expresion())

    def visitPrimBloque(self, ctx):
        return self.tipo_bloque(ctx.bloque(), True)

    def visitPrimIdent(self, ctx):
        linea, columna = posicion_token(ctx.ID())
        simbolo = self.tabla.resolver_variable(ctx.ID().getText(), linea, columna)
        ctx.simbolo = simbolo
        return simbolo.tipo if simbolo is not None else T.ERROR

    def visitPrimTupla(self, ctx):
        return self.visit(ctx.literalTupla())

    def visitPrimArray(self, ctx):
        return self.visit(ctx.literalArray())

    def visitPrimStruct(self, ctx):
        return self.visit(ctx.literalStruct())

    def visitPrimEnum(self, ctx):
        return self.visit(ctx.valorEnum())

    def visitPrimMatch(self, ctx):
        return self.visit(ctx.expresionMatch())

    def visitLiteralTupla(self, ctx):
        tipos = [self.visit(e) for e in ctx.expresion()]
        return T.ERROR if T.ERROR in tipos else T.TipoTupla(tipos)

    def visitLiteralArray(self, ctx):
        expresiones = ctx.expresion()
        tipos = [self.visit(e) for e in expresiones]
        if T.ERROR in tipos:
            return T.ERROR
        primero = tipos[0]
        for e, t in zip(expresiones[1:], tipos[1:]):
            if t != primero:
                return self.error(e, f"Todos los elementos del array deben ser del mismo tipo: "
                                     f"el primero es {primero} y este es {t}")
        return T.TipoArray(primero, len(tipos))

    def visitLiteralStruct(self, ctx):
        nombre = ctx.ID().getText()
        struct = self.tabla.buscar_struct(nombre)
        if struct is None:
            for inicial in ctx.inicCampo():
                self.visit(inicial.expresion())
            if self.tabla.buscar_enum(nombre):
                return self.error_token(ctx.ID(), f"'{nombre}' es un enum, no un struct")
            return self.error_token(ctx.ID(), f"El struct '{nombre}' no existe")

        vistos = set()
        for inicial in ctx.inicCampo():
            campo = inicial.ID().getText()
            tipo = self.visit(inicial.expresion())
            esperado = struct.tipo_campo(campo)
            if esperado is None:
                self.error_token(inicial.ID(), f"El struct '{nombre}' no tiene el campo '{campo}'")
            elif campo in vistos:
                self.error_token(inicial.ID(), f"El campo '{campo}' se inicializa dos veces")
            elif not asignable(esperado, tipo):
                self.error(inicial.expresion(),
                           f"El campo '{campo}' de '{nombre}' es de tipo {esperado}, no {tipo}")
            vistos.add(campo)
        faltantes = [c for c in struct.campos if c not in vistos]
        if faltantes:
            lista = ", ".join(f"'{c}'" for c in faltantes)
            self.error_token(ctx.ID(), f"Faltan los campos {lista} del struct '{nombre}'")
        return struct.tipo

    def visitValorEnum(self, ctx):
        nombre, variante = ctx.ID(0).getText(), ctx.ID(1).getText()
        argumentos = ctx.listaArgumentos().expresion() if ctx.listaArgumentos() else []
        enum = self.tabla.buscar_enum(nombre)
        if enum is None:
            for a in argumentos:
                self.visit(a)
            if self.tabla.buscar_struct(nombre):
                return self.error_token(ctx.ID(0), f"'{nombre}' es un struct, no un enum")
            return self.error_token(ctx.ID(0), f"El enum '{nombre}' no existe")
        tipos_datos = enum.tipos_variante(variante)
        tipos = [self.visit(a) for a in argumentos]
        if tipos_datos is None:
            return self.error_token(ctx.ID(1), f"El enum '{nombre}' no tiene la variante '{variante}'")
        if len(tipos) != len(tipos_datos):
            return self.error_token(ctx.ID(1), self.mensaje_datos(nombre, variante, tipos_datos,
                                                                  f"recibe {len(tipos)}"))
        for i, (a, tipo, esperado) in enumerate(zip(argumentos, tipos, tipos_datos), start=1):
            if not asignable(esperado, tipo):
                self.error(a, f"El dato {i} de '{nombre}::{variante}' debe ser {esperado}, no {tipo}")
        return enum.tipo

    @staticmethod
    def mensaje_datos(nombre, variante, tipos_datos, que):
        if not tipos_datos:
            return f"La variante '{nombre}::{variante}' no lleva datos pero {que}"
        return f"La variante '{nombre}::{variante}' lleva {len(tipos_datos)} dato(s) pero {que}"

    def visitLitEntero(self, ctx):
        return T.I32

    def visitLitFlotante(self, ctx):
        return T.F64

    def visitLitBooleano(self, ctx):
        return T.BOOL

    def visitLitChar(self, ctx):
        return T.CHAR

    def visitLitTexto(self, ctx):
        return T.STRING

    # ----- Match y patrones -----

    def visitExpresionMatch(self, ctx):
        tipo_valor = self.visit(ctx.expresion())
        tipo_patron = sin_referencia(tipo_valor)
        ramas = []
        patrones_validos = True
        for brazo in ctx.brazoMatch():
            self.tabla.abrir_ambito()
            if not self.revisar_patron(brazo.patron(), tipo_patron):
                patrones_validos = False
            ramas.append((brazo.expresion(), self.visit(brazo.expresion())))
            self.tabla.cerrar_ambito()

        if tipo_patron != T.ERROR and patrones_validos:
            testigo = self.faltante([tipo_patron], [[b.patron()] for b in ctx.brazoMatch()])
            if testigo is not None:
                self.error(ctx, f"El match no es exhaustivo: no se cubre el patrón '{testigo[0]}'")
        return self.unificar(ramas, "Los brazos del match")

    def revisar_patron(self, patron, tipo):
        """Revisa el patrón contra el tipo y declara sus variables. False si hubo error."""
        tipo = sin_referencia(tipo)
        if isinstance(patron, P.PatComodinContext):
            return True

        if isinstance(patron, P.PatIdentContext):
            self.declarar(patron, patron.ID().getText(), tipo, False, patron.ID())
            return True

        if isinstance(patron, P.PatLiteralContext):
            if isinstance(patron.literal(), P.LitTextoContext):
                self.error(patron, "RustiQ no soporta patrones de texto (String) en un match")
                return False
            tipo_literal = self.visit(patron.literal())
            if tipo != T.ERROR and tipo_literal != tipo:
                self.error(patron, f"El patrón '{patron.getText()}' es de tipo {tipo_literal} "
                                   f"pero el valor del match es de tipo {tipo}")
                return False
            return True

        if isinstance(patron, P.PatVarianteContext):
            nombre, variante = patron.ID(0).getText(), patron.ID(1).getText()
            enum = self.tabla.buscar_enum(nombre)
            if enum is None:
                self.error_token(patron.ID(0), f"El enum '{nombre}' no existe")
                return False
            tipos_datos = enum.tipos_variante(variante)
            if tipos_datos is None:
                self.error_token(patron.ID(1), f"El enum '{nombre}' no tiene la variante '{variante}'")
                return False
            if tipo != T.ERROR and tipo != enum.tipo:
                self.error(patron, f"El patrón '{nombre}::{variante}' no corresponde al tipo "
                                   f"{tipo} del valor del match")
                return False
            subpatrones = patron.listaPatrones().patron() if patron.listaPatrones() else []
            if len(subpatrones) != len(tipos_datos):
                self.error(patron, self.mensaje_datos(nombre, variante, tipos_datos,
                                                      f"el patrón tiene {len(subpatrones)}"))
                return False
            ok = True
            for sub, tipo_dato in zip(subpatrones, tipos_datos):
                ok = self.revisar_patron(sub, tipo_dato) and ok
            return ok

        # PatTupla
        subpatrones = patron.patron()
        if tipo == T.ERROR:
            for sub in subpatrones:
                self.revisar_patron(sub, T.ERROR)
            return True
        if not isinstance(tipo, T.TipoTupla):
            self.error(patron, f"El patrón de tupla no corresponde al tipo {tipo} del valor del match")
            return False
        if len(subpatrones) != len(tipo.elementos):
            self.error(patron, f"La tupla tiene {len(tipo.elementos)} elementos pero el patrón "
                               f"tiene {len(subpatrones)}")
            return False
        ok = True
        for sub, tipo_elem in zip(subpatrones, tipo.elementos):
            ok = self.revisar_patron(sub, tipo_elem) and ok
        return ok

    # ----- Exhaustividad -----
    #
    # Algoritmo clásico de "matriz de patrones": cada brazo es una fila; se
    # toma la primera columna y se especializa la matriz por cada constructor
    # posible de su tipo (cada variante del enum, true/false, los elementos de
    # la tupla). Si para algún constructor la matriz especializada no es
    # exhaustiva, se arma un patrón "testigo" que no está cubierto.
    # None representa un comodín.

    @staticmethod
    def irrefutable(patron):
        return patron is None or isinstance(patron, (P.PatComodinContext, P.PatIdentContext))

    def faltante(self, tipos, filas):
        """Devuelve una lista de textos (un patrón por columna) no cubierta, o None."""
        if not tipos:
            return None if filas else []
        tipo, resto = sin_referencia(tipos[0]), tipos[1:]

        if isinstance(tipo, T.TipoEnum):
            enum = self.tabla.buscar_enum(tipo.nombre)
            for variante, datos in enum.variantes.items():
                nuevas = []
                for fila in filas:
                    p = fila[0]
                    if self.irrefutable(p):
                        nuevas.append([None] * len(datos) + fila[1:])
                    elif isinstance(p, P.PatVarianteContext) and p.ID(1).getText() == variante:
                        subs = list(p.listaPatrones().patron()) if p.listaPatrones() else []
                        if len(subs) == len(datos):
                            nuevas.append(subs + fila[1:])
                testigo = self.faltante(list(datos) + resto, nuevas)
                if testigo is not None:
                    texto = f"{enum.nombre}::{variante}"
                    if datos:
                        texto += "(" + ", ".join(testigo[:len(datos)]) + ")"
                    return [texto] + testigo[len(datos):]
            return None

        if tipo == T.BOOL:
            for valor in ("true", "false"):
                nuevas = [fila[1:] for fila in filas
                          if self.irrefutable(fila[0])
                          or (isinstance(fila[0], P.PatLiteralContext) and fila[0].getText() == valor)]
                testigo = self.faltante(resto, nuevas)
                if testigo is not None:
                    return [valor] + testigo
            return None

        if isinstance(tipo, T.TipoTupla):
            n = len(tipo.elementos)
            nuevas = []
            for fila in filas:
                p = fila[0]
                if self.irrefutable(p):
                    nuevas.append([None] * n + fila[1:])
                elif isinstance(p, P.PatTuplaContext) and len(p.patron()) == n:
                    nuevas.append(list(p.patron()) + fila[1:])
            testigo = self.faltante(list(tipo.elementos) + resto, nuevas)
            if testigo is not None:
                return ["(" + ", ".join(testigo[:n]) + ")"] + testigo[n:]
            return None

        # i32, f64, char, String, structs, arrays: infinitos valores, solo
        # un comodín (o una variable) los cubre todos.
        nuevas = [fila[1:] for fila in filas if self.irrefutable(fila[0])]
        testigo = self.faltante(resto, nuevas)
        return None if testigo is None else ["_"] + testigo

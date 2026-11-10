from generado.RustiQVisitor import RustiQVisitor
from generado.RustiQParser import RustiQParser
import tipos as T


class ErrorNoSoportado(Exception):
    """Una construcción que el generador todavía no sabe traducir."""

    def __init__(self, ctx, mensaje):
        super().__init__(mensaje)
        self.linea = ctx.start.line
        self.columna = ctx.start.column + 1
        self.mensaje = mensaje


# Funciones que el entorno (Python o el navegador) le presta al módulo.
PREDEFINIDAS = {
    "print_i32": T.I32,
    "print_f64": T.F64,
    "print_bool": T.BOOL,
    "print_char": T.CHAR,
}

# (operador, tipo wasm) -> instrucción
OPERADORES = {
    ("+", "i32"): "i32.add",   ("+", "f64"): "f64.add",
    ("-", "i32"): "i32.sub",   ("-", "f64"): "f64.sub",
    ("*", "i32"): "i32.mul",   ("*", "f64"): "f64.mul",
    ("/", "i32"): "i32.div_s", ("/", "f64"): "f64.div",
    ("%", "i32"): "i32.rem_s", ("%", "f64"): "call $__f64_rem",
    ("==", "i32"): "i32.eq",   ("==", "f64"): "f64.eq",
    ("!=", "i32"): "i32.ne",   ("!=", "f64"): "f64.ne",
    ("<", "i32"): "i32.lt_s",  ("<", "f64"): "f64.lt",
    ("<=", "i32"): "i32.le_s", ("<=", "f64"): "f64.le",
    (">", "i32"): "i32.gt_s",  (">", "f64"): "f64.gt",
    (">=", "i32"): "i32.ge_s", (">=", "f64"): "f64.ge",
}

ESCAPES = {"n": "\n", "t": "\t", "r": "\r", "\\": "\\", "'": "'", '"': '"'}


def tipo_wasm(tipo):
    """Tipo de RustiQ -> tipo de Wasm. None si no ocupa valor (unit)."""
    if tipo == T.UNIT:
        return None
    if tipo == T.F64:
        return "f64"
    if tipo in (T.I32, T.BOOL, T.CHAR):
        return "i32"
    raise ValueError(f"Tipo sin representación en Wasm todavía: {tipo}")


class GeneradorWat(RustiQVisitor):
    """
    Recorre el árbol de ANTLR y escribe el módulo WAT.

    Cada visit de una expresión EMITE sus instrucciones y DEVUELVE su tipo
    (de tipos.py). Así sabemos si usar i32.add o f64.add.
    """

    def __init__(self):
        self.funciones = {}       # nombre -> (tipos de parámetros, tipo de retorno)
        self.globales = {}        # const globales: nombre -> (nombre wasm, tipo)
        self.usa_f64_rem = False
        self._nuevo_contexto_funcion(T.UNIT)

    # =====================================================
    #  Utilidades
    # =====================================================

    def _nuevo_contexto_funcion(self, retorno):
        self.cuerpo = []          # instrucciones de la función actual
        self.locales = []         # (nombre wasm, tipo wasm)
        self.usados = set()       # nombres wasm ya usados en esta función
        self.ambitos = [{}]       # nombre RustiQ -> (nombre wasm, tipo)
        self.bucles = []          # pila de números de etiqueta
        self.contador = 0
        self.sangria = 2
        self.retorno = retorno

    def emitir(self, instruccion):
        self.cuerpo.append("  " * self.sangria + instruccion)

    def nueva_etiqueta(self):
        self.contador += 1
        return self.contador

    def nombre_wasm(self, nombre):
        """Da un nombre único: $x, $x_1, $x_2... (para el sombreado)."""
        candidato, k = f"${nombre}", 1
        while candidato in self.usados:
            candidato, k = f"${nombre}_{k}", k + 1
        self.usados.add(candidato)
        return candidato

    def nuevo_local(self, nombre, tipo):
        wasm = self.nombre_wasm(nombre)
        self.locales.append((wasm, tipo_wasm(tipo)))
        self.ambitos[-1][nombre] = (wasm, tipo)
        return wasm

    def buscar_variable(self, nombre):
        for ambito in reversed(self.ambitos):
            if nombre in ambito:
                return ambito[nombre], "local"
        if nombre in self.globales:
            return self.globales[nombre], "global"
        return None, None

    def convertir_tipo(self, ctx):
        """Provisional: cuando exista el recolector, se usa su convertir_tipo."""
        if isinstance(ctx, RustiQParser.TipoPrimContext):
            return {"i32": T.I32, "f64": T.F64, "bool": T.BOOL, "char": T.CHAR}[ctx.getText()]
        raise ErrorNoSoportado(ctx, f"El tipo '{ctx.getText()}' todavía no se genera en Wasm")

    def descartar_si_hay_valor(self, tipo):
        if tipo_wasm(tipo) is not None:
            self.emitir("drop")

    # =====================================================
    #  Programa y funciones
    # =====================================================

    def visitPrograma(self, ctx):
        declaraciones = [item.getChild(0) for item in ctx.item()]
        funciones = [d for d in declaraciones if isinstance(d, RustiQParser.DeclFuncionContext)]
        constantes = [d for d in declaraciones if isinstance(d, RustiQParser.DeclConstContext)]

        # 1) Firmas primero, para poder llamar funciones declaradas más abajo.
        for f in funciones:
            params = f.listaParametros().parametro() if f.listaParametros() else []
            tipos_params = [self.convertir_tipo(p.tipo()) for p in params]
            retorno = self.convertir_tipo(f.tipo()) if f.tipo() else T.UNIT
            self.funciones[f.ID().getText()] = (tipos_params, retorno)

        # 2) Constantes globales: un global de Wasm + una función que las inicializa.
        texto_constantes = self.generar_constantes(constantes)

        # 3) Cada función.
        texto_funciones = [self.generar_funcion(f) for f in funciones]

        partes = ["(module"]
        for nombre, tipo in PREDEFINIDAS.items():
            partes.append(f'  (import "env" "{nombre}" (func ${nombre} (param {tipo_wasm(tipo)})))')
        partes.append('  (memory (export "memory") 1)')
        partes += texto_constantes
        if self.usa_f64_rem:
            partes.append(F64_REM)
        partes += texto_funciones
        if "main" in self.funciones:
            partes.append('  (export "main" (func $main))')
        partes.append(")")
        return "\n".join(partes)

    def generar_constantes(self, constantes):
        if not constantes:
            return []
        lineas = []
        self._nuevo_contexto_funcion(T.UNIT)
        for c in constantes:
            nombre, tipo = c.ID().getText(), self.convertir_tipo(c.tipo())
            w = tipo_wasm(tipo)
            self.globales[nombre] = (f"${nombre}", tipo)
            lineas.append(f"  (global ${nombre} (mut {w}) ({w}.const 0))")
            self.visit(c.expresion())
            self.emitir(f"global.set ${nombre}")
        lineas.append(self.armar_funcion("$__iniciar_constantes", [], None))
        return lineas

    def generar_funcion(self, ctx):
        nombre = ctx.ID().getText()
        tipos_params, retorno = self.funciones[nombre]
        self._nuevo_contexto_funcion(retorno)

        params = ctx.listaParametros().parametro() if ctx.listaParametros() else []
        firma = []
        for p, tipo in zip(params, tipos_params):
            wasm = self.nombre_wasm(p.ID().getText())
            self.ambitos[0][p.ID().getText()] = (wasm, tipo)
            firma.append(f"(param {wasm} {tipo_wasm(tipo)})")

        if nombre == "main" and self.globales:
            self.emitir("call $__iniciar_constantes")

        quiere_valor = tipo_wasm(retorno) is not None
        tipo_cuerpo = self.generar_bloque(ctx.bloque(), quiere_valor)
        if quiere_valor and tipo_wasm(tipo_cuerpo) is None:
            # El valor sale por 'return' dentro del cuerpo; al final no queda nada.
            self.emitir("unreachable")

        return self.armar_funcion(f"${nombre}", firma, tipo_wasm(retorno))

    def armar_funcion(self, nombre, firma, resultado):
        cabecera = f"  (func {nombre}"
        if firma:
            cabecera += " " + " ".join(firma)
        if resultado:
            cabecera += f" (result {resultado})"
        lineas = [cabecera]
        lineas += [f"    (local {n} {t})" for n, t in self.locales]
        lineas += self.cuerpo
        lineas.append("  )")
        return "\n".join(lineas)

    # =====================================================
    #  Bloques y sentencias
    # =====================================================

    def generar_bloque(self, ctx, quiere_valor):
        """
        Genera { sentencias; expresion_final }.
        Si quiere_valor, deja el valor de la expresión final en la pila y devuelve su tipo.
        """
        self.ambitos.append({})
        sentencias = ctx.sentencia()
        tipo = T.UNIT

        if ctx.expresion():
            for s in sentencias:
                self.visit(s)
            tipo = self.visit(ctx.expresion())
        elif quiere_valor and sentencias and sentencias[-1].sentenciaIf() \
                and if_con_valor(sentencias[-1].sentenciaIf()):
            # fn f() -> i32 { if c { 1 } else { 2 } }
            for s in sentencias[:-1]:
                self.visit(s)
            tipo = self.generar_if(sentencias[-1].sentenciaIf(), True)
        else:
            for s in sentencias:
                self.visit(s)

        self.ambitos.pop()
        if not quiere_valor:
            self.descartar_si_hay_valor(tipo)
            return T.UNIT
        return tipo

    def visitBloque(self, ctx):
        return self.generar_bloque(ctx, False)

    def visitSentencia(self, ctx):
        hijo = ctx.getChild(0)
        if isinstance(hijo, RustiQParser.ExpresionContext):
            self.descartar_si_hay_valor(self.visit(hijo))
        else:
            self.visit(hijo)
        return T.UNIT

    def visitDeclLet(self, ctx):
        nombre = ctx.ID().getText()
        tipo = self.convertir_tipo(ctx.tipo()) if ctx.tipo() else None
        if ctx.expresion():
            tipo_valor = self.visit(ctx.expresion())   # antes de declarar: let x = x + 1;
            tipo = tipo or tipo_valor
            wasm = self.nuevo_local(nombre, tipo)
            self.emitir(f"local.set {wasm}")
        else:
            self.nuevo_local(nombre, tipo)
        return T.UNIT

    def visitDeclConstLocal(self, ctx):
        nombre = ctx.ID().getText()
        tipo = self.convertir_tipo(ctx.tipo())
        self.visit(ctx.expresion())
        self.emitir(f"local.set {self.nuevo_local(nombre, tipo)}")
        return T.UNIT

    def visitAsignacion(self, ctx):
        lugar = ctx.lugar()
        if lugar.getChildCount() > 1:
            raise ErrorNoSoportado(lugar, "Asignar a campos o índices se agrega con la memoria")
        (wasm, tipo), clase = self.buscar_variable(lugar.ID(0).getText())
        op = ctx.opAsignacion().getText()

        if op == "=":
            self.visit(ctx.expresion())
        else:
            self.emitir(f"{clase}.get {wasm}")
            self.visit(ctx.expresion())
            self.emitir(OPERADORES[(op[0], tipo_wasm(tipo))])
        self.emitir(f"{clase}.set {wasm}")
        return T.UNIT

    def visitSentenciaReturn(self, ctx):
        if ctx.expresion():
            self.visit(ctx.expresion())
        self.emitir("return")
        return T.UNIT

    def visitSentenciaIf(self, ctx):
        return self.generar_if(ctx, False)

    def generar_if(self, ctx, con_valor):
        self.visit(ctx.expresion())                  # condición (bool = i32)
        linea_if = len(self.cuerpo)
        self.emitir("if")
        self.sangria += 1
        tipo = self.generar_bloque(ctx.bloque(0), con_valor)
        self.sangria -= 1

        if ctx.ELSE():
            self.emitir("else")
            self.sangria += 1
            if ctx.sentenciaIf():
                self.generar_if(ctx.sentenciaIf(), con_valor)
            else:
                self.generar_bloque(ctx.bloque(1), con_valor)
            self.sangria -= 1
        self.emitir("end")

        if con_valor and tipo_wasm(tipo):
            self.cuerpo[linea_if] += f" (result {tipo_wasm(tipo)})"
        return tipo if con_valor else T.UNIT

    def visitSentenciaWhile(self, ctx):
        n = self.nueva_etiqueta()
        self.emitir(f"block $fin_{n}")
        self.sangria += 1
        self.emitir(f"loop $inicio_{n}")
        self.sangria += 1
        self.visit(ctx.expresion())
        self.emitir("i32.eqz")
        self.emitir(f"br_if $fin_{n}")
        self.bucles.append(n)
        self.generar_bloque(ctx.bloque(), False)
        self.bucles.pop()
        self.emitir(f"br $inicio_{n}")
        self.sangria -= 1
        self.emitir("end")
        self.sangria -= 1
        self.emitir("end")
        return T.UNIT

    def visitSentenciaLoop(self, ctx):
        n = self.nueva_etiqueta()
        self.emitir(f"block $fin_{n}")
        self.sangria += 1
        self.emitir(f"loop $inicio_{n}")
        self.sangria += 1
        self.bucles.append(n)
        self.generar_bloque(ctx.bloque(), False)
        self.bucles.pop()
        self.emitir(f"br $inicio_{n}")
        self.sangria -= 1
        self.emitir("end")
        self.sangria -= 1
        self.emitir("end")
        return T.UNIT

    def visitSentenciaBreak(self, ctx):
        self.emitir(f"br $fin_{self.bucles[-1]}")
        return T.UNIT

    def visitSentenciaContinue(self, ctx):
        self.emitir(f"br $inicio_{self.bucles[-1]}")
        return T.UNIT

    # =====================================================
    #  Expresiones
    # =====================================================

    def visitExpresion(self, ctx):
        return self.visit(ctx.disyuncion())

    def visitDisyuncion(self, ctx):
        # a || b  ->  a; if (result i32) 1 else b end   (b solo se evalúa si a es false)
        operandos = ctx.conjuncion()
        tipo = self.visit(operandos[0])
        for siguiente in operandos[1:]:
            self.emitir("if (result i32)")
            self.sangria += 1
            self.emitir("i32.const 1")
            self.sangria -= 1
            self.emitir("else")
            self.sangria += 1
            self.visit(siguiente)
            self.sangria -= 1
            self.emitir("end")
            tipo = T.BOOL
        return tipo

    def visitConjuncion(self, ctx):
        # a && b  ->  a; if (result i32) b else 0 end   (b solo se evalúa si a es true)
        operandos = ctx.comparacion()
        tipo = self.visit(operandos[0])
        for siguiente in operandos[1:]:
            self.emitir("if (result i32)")
            self.sangria += 1
            self.visit(siguiente)
            self.sangria -= 1
            self.emitir("else")
            self.sangria += 1
            self.emitir("i32.const 0")
            self.sangria -= 1
            self.emitir("end")
            tipo = T.BOOL
        return tipo

    def visitComparacion(self, ctx):
        izquierda = self.visit(ctx.suma(0))
        if not ctx.opRelacional():
            return izquierda
        self.visit(ctx.suma(1))
        self.emitir(OPERADORES[(ctx.opRelacional().getText(), tipo_wasm(izquierda))])
        return T.BOOL

    def generar_binaria(self, ctx):
        """Para suma y producto: hijo op hijo op hijo ..."""
        hijos = list(ctx.getChildren())
        tipo = self.visit(hijos[0])
        for i in range(1, len(hijos), 2):
            op = hijos[i].getText()
            self.visit(hijos[i + 1])
            if (op, tipo_wasm(tipo)) == ("%", "f64"):
                self.usa_f64_rem = True
            self.emitir(OPERADORES[(op, tipo_wasm(tipo))])
        return tipo

    def visitSuma(self, ctx):
        return self.generar_binaria(ctx)

    def visitProducto(self, ctx):
        return self.generar_binaria(ctx)

    def visitUnarioNegativo(self, ctx):
        tipo = self.visit(ctx.unario())
        if tipo == T.F64:
            self.emitir("f64.neg")
        else:
            self.emitir("i32.const -1")
            self.emitir("i32.mul")
        return tipo

    def visitUnarioNegacion(self, ctx):
        self.visit(ctx.unario())
        self.emitir("i32.eqz")
        return T.BOOL

    def visitUnarioRef(self, ctx):
        raise ErrorNoSoportado(ctx, "Las referencias se agregan con la memoria")

    visitUnarioRefMut = visitUnarioRef
    visitUnarioDeref = visitUnarioRef

    def visitUnarioPostfijo(self, ctx):
        return self.visit(ctx.postfijo())

    def visitPostfijo(self, ctx):
        sufijos = list(ctx.getChildren())[1:]
        if not sufijos:
            return self.visit(ctx.primario())
        primario = ctx.primario()
        if (len(sufijos) == 1 and isinstance(primario, RustiQParser.PrimIdentContext)
                and isinstance(sufijos[0], RustiQParser.SufijoLlamadaContext)):
            return self.generar_llamada(primario.ID().getText(), sufijos[0])
        raise ErrorNoSoportado(ctx, "Campos e índices se agregan con la memoria")

    def generar_llamada(self, nombre, sufijo):
        argumentos = sufijo.listaArgumentos().expresion() if sufijo.listaArgumentos() else []
        for a in argumentos:
            self.visit(a)
        self.emitir(f"call ${nombre}")
        if nombre in PREDEFINIDAS:
            return T.UNIT
        return self.funciones[nombre][1]

    # =====================================================
    #  Primarios y literales
    # =====================================================

    def visitPrimLiteral(self, ctx):
        return self.visit(ctx.literal())

    def visitPrimParen(self, ctx):
        return self.visit(ctx.expresion())

    def visitPrimBloque(self, ctx):
        return self.generar_bloque(ctx.bloque(), True)

    def visitPrimIdent(self, ctx):
        (wasm, tipo), clase = self.buscar_variable(ctx.ID().getText())
        self.emitir(f"{clase}.get {wasm}")
        return tipo

    def no_soportado_todavia(self, ctx):
        raise ErrorNoSoportado(ctx, f"'{ctx.getText()}' se agrega con la memoria")

    visitPrimTupla = visitPrimArray = visitPrimStruct = no_soportado_todavia
    visitPrimEnum = visitPrimMatch = visitLitTexto = no_soportado_todavia

    def visitLitEntero(self, ctx):
        self.emitir(f"i32.const {ctx.getText()}")
        return T.I32

    def visitLitFlotante(self, ctx):
        self.emitir(f"f64.const {ctx.getText()}")
        return T.F64

    def visitLitBooleano(self, ctx):
        self.emitir("i32.const 1" if ctx.getText() == "true" else "i32.const 0")
        return T.BOOL

    def visitLitChar(self, ctx):
        contenido = ctx.getText()[1:-1]
        if contenido.startswith("\\"):
            contenido = ESCAPES[contenido[1]]
        self.emitir(f"i32.const {ord(contenido)}")
        return T.CHAR


def if_con_valor(ctx):
    """¿Este if tiene else en todas sus ramas? (solo así puede producir un valor)"""
    if not ctx.ELSE():
        return False
    if ctx.sentenciaIf():
        return if_con_valor(ctx.sentenciaIf())
    return True


# a % b para f64 (Wasm no lo trae):  a - trunc(a / b) * b
F64_REM = """  (func $__f64_rem (param $a f64) (param $b f64) (result f64)
    local.get $a
    local.get $a
    local.get $b
    f64.div
    f64.trunc
    local.get $b
    f64.mul
    f64.sub
  )"""

from generado.RustiQVisitor import RustiQVisitor
from generado.RustiQParser import RustiQParser as P
from memoria import tipo_wasm, sin_referencia
from recolector import convertir_tipo, PREDEFINIDAS
import memoria as M
import tipos as T


class ErrorNoSoportado(Exception):
    """Una construcción que el generador todavía no sabe traducir."""

    def __init__(self, ctx, mensaje):
        super().__init__(mensaje)
        self.linea = ctx.start.line
        self.columna = ctx.start.column + 1
        self.mensaje = mensaje


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


def decodificar_escapes(texto):
    resultado, i = [], 0
    while i < len(texto):
        if texto[i] == "\\":
            resultado.append(ESCAPES[texto[i + 1]])
            i += 2
        else:
            resultado.append(texto[i])
            i += 1
    return "".join(resultado)


def con_offset(instruccion, offset):
    return f"{instruccion} offset={offset}" if offset else instruccion


class GeneradorWat(RustiQVisitor):
    """
    Recorre el árbol de ANTLR y escribe el módulo WAT.

    Recibe la tabla de símbolos que llenó el recolector (structs, enums y
    firmas de funciones). Solo se llega aquí si las fases semánticas no
    reportaron errores, así que el generador confía en los tipos y no revisa.

    Cada visit de una expresión EMITE sus instrucciones y DEVUELVE su tipo
    (de tipos.py). Así sabemos si usar i32.add o f64.add, o qué offset tiene
    un campo. La representación en memoria está explicada en memoria.py.
    """

    def __init__(self, tabla):
        self.tabla = tabla
        self.globales = {}        # const globales: nombre -> (nombre wasm, tipo)
        self.textos = {}          # literal de texto -> dirección en memoria
        self.datos = []           # segmentos (data ...)
        self.siguiente_dato = M.INICIO_DATOS
        self.copiadores = {}      # str(tipo) -> (nombre wasm, texto de la función)
        self.usa_f64_rem = False
        self._sin_copia = False
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

    def temporal(self, tipo_w="i32"):
        """Un local auxiliar que no corresponde a ninguna variable del programa."""
        wasm = self.nombre_wasm("__t")
        self.locales.append((wasm, tipo_w))
        return wasm

    def buscar_variable(self, nombre):
        for ambito in reversed(self.ambitos):
            if nombre in ambito:
                return ambito[nombre], "local"
        if nombre in self.globales:
            return self.globales[nombre], "global"
        return None, None

    def descartar_si_hay_valor(self, tipo):
        if tipo_wasm(tipo) is not None:
            self.emitir("drop")

    def reservar(self, n_bytes):
        """Pide memoria y deja el puntero en un temporal (que se devuelve)."""
        puntero = self.temporal()
        self.emitir(f"i32.const {n_bytes}")
        self.emitir("call $__alloc")
        self.emitir(f"local.set {puntero}")
        return puntero

    def convertir_tipo(self, ctx):
        return convertir_tipo(ctx, self.tabla)

    # =====================================================
    #  Programa y funciones
    # =====================================================

    def visitPrograma(self, ctx):
        declaraciones = [item.getChild(0) for item in ctx.item()]
        de_tipo = lambda clase: [d for d in declaraciones if isinstance(d, clase)]
        funciones = de_tipo(P.DeclFuncionContext)

        # Los structs, enums y firmas ya están en la tabla (los puso el
        # recolector). Solo falta generar constantes globales y funciones.
        texto_constantes = self.generar_constantes(de_tipo(P.DeclConstContext))
        texto_funciones = [self.generar_funcion(f) for f in funciones]

        heap = (self.siguiente_dato + 7) // 8 * 8
        partes = ["(module"]
        for nombre, tipo in PREDEFINIDAS:
            partes.append(f'  (import "env" "{nombre}" (func ${nombre} (param {tipo_wasm(tipo)})))')
        partes.append('  (memory (export "memory") 1)')
        partes += self.datos
        partes.append(f"  (global $__heap (mut i32) (i32.const {heap}))")
        partes += texto_constantes
        partes.append(M.FUNCION_ALLOC)
        if self.usa_f64_rem:
            partes.append(F64_REM)
        partes += [texto for _, texto in self.copiadores.values()]
        partes += texto_funciones
        if self.tabla.buscar_funcion("main") is not None:
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
        simbolo = self.tabla.buscar_funcion(nombre)
        retorno = simbolo.retorno
        self._nuevo_contexto_funcion(retorno)

        params = ctx.listaParametros().parametro() if ctx.listaParametros() else []
        firma = []
        for p, tipo in zip(params, simbolo.tipos_parametros()):
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
        if isinstance(hijo, P.ExpresionContext):
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
        op = ctx.opAsignacion().getText()
        (wasm, tipo), clase = self.buscar_variable(lugar.ID(0).getText())
        accesos = accesos_de_lugar(lugar)

        if not accesos:                              # x = valor;  x += valor;
            if op == "=":
                self.visit(ctx.expresion())
            else:
                self.emitir(f"{clase}.get {wasm}")
                self.visit(ctx.expresion())
                self.emitir(OPERADORES[(op[0], tipo_wasm(tipo))])
            self.emitir(f"{clase}.set {wasm}")
            return T.UNIT

        # p.x = valor;  a[i] = valor;  p.lista[2] += valor;
        self.emitir(f"{clase}.get {wasm}")
        for acceso in accesos[:-1]:
            tipo = self.cargar_acceso(tipo, acceso)
        direccion, offset, tipo = self.direccion_acceso(tipo, accesos[-1])

        self.emitir(f"local.get {direccion}")
        if op == "=":
            self.visit(ctx.expresion())
        else:
            self.emitir(f"local.get {direccion}")
            self.emitir(con_offset(M.cargar(tipo), offset))
            self.visit(ctx.expresion())
            self.emitir(OPERADORES[(op[0], tipo_wasm(tipo))])
        self.emitir(con_offset(M.guardar(tipo), offset))
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
                otro = self.generar_if(ctx.sentenciaIf(), con_valor)
            else:
                otro = self.generar_bloque(ctx.bloque(1), con_valor)
            tipo = tipo if tipo_wasm(tipo) else otro
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
        return sin_referencia(tipo)

    def visitSuma(self, ctx):
        return self.generar_binaria(ctx)

    def visitProducto(self, ctx):
        return self.generar_binaria(ctx)

    def visitUnarioNegativo(self, ctx):
        tipo = self.visit(ctx.unario())
        if tipo_wasm(tipo) == "f64":
            self.emitir("f64.neg")
        else:
            self.emitir("i32.const -1")
            self.emitir("i32.mul")
        return sin_referencia(tipo)

    def visitUnarioNegacion(self, ctx):
        self.visit(ctx.unario())
        self.emitir("i32.eqz")
        return T.BOOL

    def generar_referencia(self, ctx, mutable):
        # &x: un valor compuesto ya es un puntero, así que se usa tal cual
        # (sin copiarlo); un escalar se representa con su valor (ver memoria.py).
        if isinstance(ctx.unario(), P.UnarioPostfijoContext):
            self._sin_copia = True
        tipo = self.visit(ctx.unario())
        self._sin_copia = False
        return T.TipoReferencia(tipo, mutable)

    def visitUnarioRef(self, ctx):
        return self.generar_referencia(ctx, False)

    def visitUnarioRefMut(self, ctx):
        return self.generar_referencia(ctx, True)

    def visitUnarioDeref(self, ctx):
        tipo = self.visit(ctx.unario())
        interno = tipo.interno if isinstance(tipo, T.TipoReferencia) else tipo
        return self.copiar_si_hace_falta(interno)

    def visitUnarioPostfijo(self, ctx):
        return self.visit(ctx.postfijo())

    def visitPostfijo(self, ctx):
        """primario seguido de llamadas (f(...)), campos (.x) e índices ([i])."""
        copiar = not self._sin_copia
        self._sin_copia = False
        primario, *sufijos = list(ctx.getChildren())

        if sufijos and isinstance(sufijos[0], P.SufijoLlamadaContext):
            if not isinstance(primario, P.PrimIdentContext):
                raise ErrorNoSoportado(ctx, "Solo se puede llamar a una función por su nombre")
            tipo = self.generar_llamada(primario.ID().getText(), sufijos[0])
            sufijos, es_lugar = sufijos[1:], False
        else:
            tipo = self.visit(primario)
            es_lugar = isinstance(primario, P.PrimIdentContext)

        for sufijo in sufijos:
            if isinstance(sufijo, P.SufijoLlamadaContext):
                raise ErrorNoSoportado(sufijo, "Solo se puede llamar a una función por su nombre")
            tipo = self.cargar_acceso(tipo, sufijo)
            es_lugar = True

        if copiar and es_lugar:
            tipo = self.copiar_si_hace_falta(tipo)
        return tipo

    def generar_llamada(self, nombre, sufijo):
        argumentos = sufijo.listaArgumentos().expresion() if sufijo.listaArgumentos() else []
        for a in argumentos:
            self.visit(a)
        self.emitir(f"call ${nombre}")
        return self.tabla.buscar_funcion(nombre).retorno

    # ----- Campos e índices -----

    def cargar_acceso(self, tipo, acceso):
        """Con el puntero en la pila, deja el valor del campo o del elemento."""
        direccion, offset, tipo_elem = self.direccion_acceso(tipo, acceso)
        self.emitir(f"local.get {direccion}")
        self.emitir(con_offset(M.cargar(tipo_elem), offset))
        return tipo_elem

    def direccion_acceso(self, tipo, acceso):
        """
        Con el puntero en la pila, calcula dónde está el campo o el elemento.
        Devuelve (temporal con la dirección base, offset, tipo del elemento).
        """
        tipo = sin_referencia(tipo)              # p.x funciona igual si p es &Punto
        direccion = self.temporal()

        if isinstance(acceso, (P.SufijoCampoContext, str)):
            campo = acceso if isinstance(acceso, str) else acceso.ID().getText()
            struct = self.tabla.buscar_struct(tipo.nombre)
            self.emitir(f"local.set {direccion}")
            return direccion, M.offset_campo(struct, campo), struct.tipo_campo(campo)

        # Índice: a[i]  ->  a + i * 8, revisando que 0 <= i < largo
        indice = self.temporal()
        self.emitir(f"local.set {direccion}")
        self.visit(acceso.expresion())
        self.emitir(f"local.set {indice}")
        self.emitir(f"local.get {indice}")
        self.emitir(f"i32.const {tipo.longitud}")
        self.emitir("i32.ge_u")
        self.emitir("if")
        self.emitir("  unreachable")             # índice fuera de rango
        self.emitir("end")
        self.emitir(f"local.get {direccion}")
        self.emitir(f"local.get {indice}")
        self.emitir(f"i32.const {M.SLOT}")
        self.emitir("i32.mul")
        self.emitir("i32.add")
        self.emitir(f"local.set {direccion}")
        return direccion, 0, tipo.elemento

    # ----- Copias de arrays y tuplas -----

    def copiar_si_hace_falta(self, tipo):
        if M.necesita_copia(tipo):
            self.emitir(f"call {self.copiador(tipo)}")
        return tipo

    def copiador(self, tipo):
        """Genera (una sola vez por tipo) una función que copia el bloque completo."""
        clave = str(tipo)
        if clave in self.copiadores:
            return self.copiadores[clave][0]
        nombre = f"$__copiar_{len(self.copiadores)}"
        self.copiadores[clave] = (nombre, "")
        tam = M.tamano_bloque(tipo)
        lineas = [
            f"  (func {nombre} (param $p i32) (result i32)",
            "    (local $q i32)",
            f"    i32.const {tam}", "    call $__alloc", "    local.set $q",
            "    local.get $q", "    local.get $p", f"    i32.const {tam}", "    memory.copy",
        ]
        for i, tipo_slot in enumerate(M.tipos_de_slots(tipo)):
            if M.necesita_copia(tipo_slot):              # arrays dentro de arrays
                off = M.offset_slot(i)
                lineas += [
                    "    local.get $q", "    local.get $p", f"    {con_offset('i32.load', off)}",
                    f"    call {self.copiador(tipo_slot)}", f"    {con_offset('i32.store', off)}",
                ]
        lineas += ["    local.get $q", "  )"]
        self.copiadores[clave] = (nombre, "\n".join(lineas))
        return nombre

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

    def guardar_elementos(self, puntero, expresiones):
        """Evalúa cada expresión y la guarda en el slot i del bloque."""
        tipos = []
        for i, e in enumerate(expresiones):
            self.emitir(f"local.get {puntero}")
            tipo = self.visit(e)
            self.emitir(con_offset(M.guardar(tipo), M.offset_slot(i)))
            tipos.append(tipo)
        return tipos

    def visitLiteralTupla(self, ctx):
        expresiones = ctx.expresion()
        puntero = self.reservar(len(expresiones) * M.SLOT)
        tipos = self.guardar_elementos(puntero, expresiones)
        self.emitir(f"local.get {puntero}")
        return T.TipoTupla(tipos)

    def visitLiteralArray(self, ctx):
        expresiones = ctx.expresion()
        puntero = self.reservar(len(expresiones) * M.SLOT)
        tipos = self.guardar_elementos(puntero, expresiones)
        self.emitir(f"local.get {puntero}")
        return T.TipoArray(tipos[0], len(expresiones))

    def visitLiteralStruct(self, ctx):
        struct = self.tabla.buscar_struct(ctx.ID().getText())
        puntero = self.reservar(len(struct.campos) * M.SLOT)
        for inicial in ctx.inicCampo():
            campo = inicial.ID().getText()
            self.emitir(f"local.get {puntero}")
            self.visit(inicial.expresion())
            self.emitir(con_offset(M.guardar(struct.tipo_campo(campo)),
                                   M.offset_campo(struct, campo)))
        self.emitir(f"local.get {puntero}")
        return struct.tipo

    def visitValorEnum(self, ctx):
        # Estado::Completado(200)  ->  [ tag ][ 200 ]
        enum = self.tabla.buscar_enum(ctx.ID(0).getText())
        variante = ctx.ID(1).getText()
        argumentos = ctx.listaArgumentos().expresion() if ctx.listaArgumentos() else []
        puntero = self.reservar((1 + len(argumentos)) * M.SLOT)
        self.emitir(f"local.get {puntero}")
        self.emitir(f"i32.const {M.tag_de_variante(enum, variante)}")
        self.emitir("i32.store")
        for i, (a, tipo_dato) in enumerate(zip(argumentos, enum.tipos_variante(variante))):
            self.emitir(f"local.get {puntero}")
            self.visit(a)
            self.emitir(con_offset(M.guardar(tipo_dato), M.offset_dato_variante(i)))
        self.emitir(f"local.get {puntero}")
        return enum.tipo

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
        self.emitir(f"i32.const {ord(decodificar_escapes(ctx.getText()[1:-1]))}")
        return T.CHAR

    def visitLitTexto(self, ctx):
        # Cada literal distinto se guarda una vez en la memoria: [ largo ][ bytes ]
        texto = decodificar_escapes(ctx.getText()[1:-1])
        if texto not in self.textos:
            contenido = texto.encode("utf-8")
            direccion = (self.siguiente_dato + 3) // 4 * 4
            bytes_bloque = len(contenido).to_bytes(4, "little") + contenido
            self.datos.append(f'  (data (i32.const {direccion}) "{M.bytes_wat(bytes_bloque)}")')
            self.textos[texto] = direccion
            self.siguiente_dato = direccion + len(bytes_bloque)
        self.emitir(f"i32.const {self.textos[texto]}")
        return T.STRING

    # =====================================================
    #  Match
    # =====================================================

    def visitExpresionMatch(self, ctx):
        """
        match v { p1 => e1, p2 => e2 }  se traduce a:

            block $match_N (result T)
              block $brazo_N_1   ;; si p1 no calza, salta al final de este bloque
                ...pruebas de p1 (br_if $brazo_N_1)...
                e1
                br $match_N
              end
              block $brazo_N_2 ... end
              unreachable       ;; ningún brazo calzó (el semántico revisa exhaustividad)
            end
        """
        tipo_valor = sin_referencia(self.visit(ctx.expresion()))
        valor = self.temporal(tipo_wasm(tipo_valor))
        self.emitir(f"local.set {valor}")

        n = self.nueva_etiqueta()
        linea_match = len(self.cuerpo)
        self.emitir(f"block $match_{n}")
        self.sangria += 1
        tipo_resultado = T.UNIT
        for k, brazo in enumerate(ctx.brazoMatch(), start=1):
            siguiente = f"$brazo_{n}_{k}"
            self.emitir(f"block {siguiente}")
            self.sangria += 1
            self.ambitos.append({})
            self.probar_patron(brazo.patron(), valor, tipo_valor, siguiente)
            tipo = self.visit(brazo.expresion())
            if tipo_wasm(tipo_resultado) is None:
                tipo_resultado = tipo
            self.ambitos.pop()
            self.emitir(f"br $match_{n}")
            self.sangria -= 1
            self.emitir("end")
        self.emitir("unreachable")
        self.sangria -= 1
        self.emitir("end")

        if tipo_wasm(tipo_resultado):
            self.cuerpo[linea_match] += f" (result {tipo_wasm(tipo_resultado)})"
        return tipo_resultado

    def probar_patron(self, patron, valor, tipo, siguiente):
        """
        Emite las pruebas del patrón contra el local 'valor'. Si alguna falla,
        salta a 'siguiente' (el próximo brazo). Si calza, deja las variables
        del patrón declaradas en el ámbito actual.
        """
        tipo = sin_referencia(tipo)

        if isinstance(patron, P.PatComodinContext):            # _
            return

        if isinstance(patron, P.PatIdentContext):              # x  (siempre calza)
            local = self.nuevo_local(patron.ID().getText(), tipo)
            self.emitir(f"local.get {valor}")
            self.emitir(f"local.set {local}")
            return

        if isinstance(patron, P.PatLiteralContext):            # 0, 'a', true, 2.5
            if isinstance(patron.literal(), P.LitTextoContext):
                raise ErrorNoSoportado(patron, "Patrones de texto no soportados")
            self.emitir(f"local.get {valor}")
            self.visit(patron.literal())
            self.emitir("f64.ne" if tipo_wasm(tipo) == "f64" else "i32.ne")
            self.emitir(f"br_if {siguiente}")
            return

        if isinstance(patron, P.PatVarianteContext):           # Estado::Completado(c)
            enum = self.tabla.buscar_enum(patron.ID(0).getText())
            variante = patron.ID(1).getText()
            self.emitir(f"local.get {valor}")
            self.emitir("i32.load")                            # el tag
            self.emitir(f"i32.const {M.tag_de_variante(enum, variante)}")
            self.emitir("i32.ne")
            self.emitir(f"br_if {siguiente}")
            subpatrones = patron.listaPatrones().patron() if patron.listaPatrones() else []
            tipos = enum.tipos_variante(variante)
            for i, (sub, tipo_dato) in enumerate(zip(subpatrones, tipos)):
                self.probar_slot(sub, valor, M.offset_dato_variante(i), tipo_dato, siguiente)
            return

        if isinstance(patron, P.PatTuplaContext):              # (a, 0)
            for i, (sub, tipo_elem) in enumerate(zip(patron.patron(), tipo.elementos)):
                self.probar_slot(sub, valor, M.offset_slot(i), tipo_elem, siguiente)
            return

        raise ErrorNoSoportado(patron, "Patrón no soportado")

    def probar_slot(self, patron, valor, offset, tipo, siguiente):
        """Carga un slot del bloque a un temporal y prueba el subpatrón contra él."""
        if isinstance(patron, P.PatComodinContext):
            return
        temporal = self.temporal(tipo_wasm(tipo))
        self.emitir(f"local.get {valor}")
        self.emitir(con_offset(M.cargar(tipo), offset))
        self.emitir(f"local.set {temporal}")
        self.probar_patron(patron, temporal, tipo, siguiente)


def accesos_de_lugar(lugar):
    """lugar = ID ( .campo | [indice] )*  ->  lista de 'campo' (str) o expresión de índice."""
    hijos = list(lugar.getChildren())[1:]
    accesos, i = [], 0
    while i < len(hijos):
        if hijos[i].getText() == ".":
            accesos.append(hijos[i + 1].getText())
            i += 2
        else:
            accesos.append(IndiceDeLugar(hijos[i + 1]))
            i += 3
    return accesos


class IndiceDeLugar:
    """Adapta un [expr] de 'lugar' para que se use igual que un SufijoIndice."""

    def __init__(self, expresion):
        self._expresion = expresion

    def expresion(self):
        return self._expresion


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

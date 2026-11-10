"""
GENERADOR DE CÓDIGO (Fase 4, backend del compilador): árbol de ANTLR -> texto WAT.

[DEFENSA] Idea central
  - Es un Visitor sobre el árbol que genera ANTLR (no se construye un AST propio).
  - Cada visit de una EXPRESIÓN hace dos cosas:
        1. EMITE sus instrucciones WAT con self.emitir(...)
        2. DEVUELVE su tipo (de tipos.py): I32, F64, BOOL, TipoStruct, ...
    El tipo decide la instrucción: 2 + 3 -> i32.add,  2.0 + 3.0 -> f64.add.
  - Wasm es una máquina de PILA: para a + b se emite "a", luego "b", luego "add".

[DEFENSA] Qué produce
  Un módulo WAT con: imports de print_*, la memoria, los textos literales,
  el asignador de memoria, las funciones del programa y el export de main.
  Después ejecutor_wasm.py lo convierte a .wasm, lo valida y lo ejecuta.

Cómo se guardan structs, arrays, enums y String en memoria: ver memoria.py.
"""
from generado.RustiQVisitor import RustiQVisitor
from generado.RustiQParser import RustiQParser as P
from errores import ListaErrores
from tabla_simbolos import TablaSimbolos
from memoria import tipo_wasm, sin_referencia
import memoria as M
import tipos as T


class ErrorNoSoportado(Exception):
    """
    Una construcción que el generador no sabe traducir. Se reporta como error de
    fase "generación" con línea y columna, en vez de producir un .wasm incorrecto.
    """

    def __init__(self, ctx, mensaje):
        super().__init__(mensaje)
        self.linea = ctx.start.line
        self.columna = ctx.start.column + 1
        self.mensaje = mensaje


# [DEFENSA] Wasm no puede imprimir por sí solo. Estas funciones son IMPORTS: el
# entorno que ejecuta el módulo se las "presta" (ejecutor_wasm.py en Python y
# ejecutor.worker.js en el navegador). RustiQ no tiene println!, así que se usan
# como funciones predefinidas.
PREDEFINIDAS = {
    "print_i32": T.I32,
    "print_f64": T.F64,
    "print_bool": T.BOOL,
    "print_char": T.CHAR,
    "print_str": T.STRING,      # recibe el puntero al String
}

# [DEFENSA] Tabla (operador, tipo wasm) -> instrucción.
#   - "_s" = con signo (signed): i32 de RustiQ es entero con signo.
#   - bool y char también son i32, por eso se comparan con las mismas instrucciones.
#   - Wasm no tiene % para f64: se genera una función auxiliar ($__f64_rem).
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

PRIMITIVOS = {"i32": T.I32, "f64": T.F64, "bool": T.BOOL, "char": T.CHAR}


def decodificar_escapes(texto):
    """Convierte las secuencias \\n, \\t, \\" ... del código fuente en los caracteres reales."""
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
    """i32.load offset=8: lee 8 bytes después de la dirección que está en la pila."""
    return f"{instruccion} offset={offset}" if offset else instruccion


class GeneradorWat(RustiQVisitor):
    """
    Recorre el árbol de ANTLR y escribe el módulo WAT.

    Cada visit de una expresión EMITE sus instrucciones y DEVUELVE su tipo
    (de tipos.py). Así sabemos si usar i32.add o f64.add, o qué offset tiene
    un campo. La representación en memoria está explicada en memoria.py.
    """

    def __init__(self):
        # Estado de TODO el módulo (se comparte entre funciones).
        self.tabla = TablaSimbolos(ListaErrores())   # structs y enums
        self.nombres_struct = set()
        self.nombres_enum = set()
        self.funciones = {}       # nombre -> (tipos de parámetros, tipo de retorno)
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
        """
        Reinicia el estado de UNA función. En Wasm las variables locales se
        declaran al inicio de la función, así que se van juntando en
        self.locales mientras se genera el cuerpo, y se escriben al final.
        """
        self.cuerpo = []          # instrucciones de la función actual
        self.locales = []         # (nombre wasm, tipo wasm)
        self.usados = set()       # nombres wasm ya usados en esta función
        self.ambitos = [{}]       # nombre RustiQ -> (nombre wasm, tipo)
        self.bucles = []          # pila de números de etiqueta
        self.contador = 0
        self.sangria = 2
        self.retorno = retorno

    def emitir(self, instruccion):
        """Agrega una línea de WAT a la función actual (con sangría para que se lea bien)."""
        self.cuerpo.append("  " * self.sangria + instruccion)

    def nueva_etiqueta(self):
        """Número único para nombrar bloques: $fin_1, $inicio_1, $match_2..."""
        self.contador += 1
        return self.contador

    def nombre_wasm(self, nombre):
        """
        Da un nombre único: $x, $x_1, $x_2...
        [DEFENSA] Sombreado: Wasm no tiene bloques con variables propias (todos
        los locales son de la función), así que dos 'let x' se vuelven $x y $x_1.
        """
        candidato, k = f"${nombre}", 1
        while candidato in self.usados:
            candidato, k = f"${nombre}_{k}", k + 1
        self.usados.add(candidato)
        return candidato

    def nuevo_local(self, nombre, tipo):
        """Declara una variable de RustiQ: crea su local de Wasm y la anota en el ámbito actual."""
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
        """Busca desde el ámbito más interno hacia afuera; al final, las const globales."""
        for ambito in reversed(self.ambitos):
            if nombre in ambito:
                return ambito[nombre], "local"
        if nombre in self.globales:
            return self.globales[nombre], "global"
        return None, None

    def variable_o_error(self, nombre, ctx):
        # Respaldo mientras no exista verificador_tipos.py (que reportará esto antes).
        simbolo, clase = self.buscar_variable(nombre)
        if simbolo is None:
            raise ErrorNoSoportado(ctx, f"La variable '{nombre}' no está declarada")
        return simbolo, clase

    def descartar_si_hay_valor(self, tipo):
        """
        Si una expresión se usa como sentencia (f(x);) y deja un valor en la pila,
        hay que sacarlo con 'drop': Wasm valida que la pila quede balanceada.
        """
        if tipo_wasm(tipo) is not None:
            self.emitir("drop")

    def reservar(self, n_bytes):
        """
        Pide n_bytes al asignador ($__alloc, en memoria.py) y guarda el puntero
        en un temporal. Se usa para crear structs, arrays, tuplas y enums.
        """
        puntero = self.temporal()
        self.emitir(f"i32.const {n_bytes}")
        self.emitir("call $__alloc")
        self.emitir(f"local.set {puntero}")
        return puntero

    def convertir_tipo(self, ctx):
        """
        Convierte el tipo escrito en el código (i32, [f64; 3], &mut Punto...) en
        un objeto de tipos.py. Provisional: cuando exista el recolector, se usa el suyo.
        """
        if isinstance(ctx, P.TipoPrimContext):
            return PRIMITIVOS[ctx.getText()]
        if isinstance(ctx, P.TipoStringContext):
            return T.STRING
        if isinstance(ctx, P.TipoArrContext):
            arr = ctx.tipoArray()
            return T.TipoArray(self.convertir_tipo(arr.tipo()), int(arr.INT_LIT().getText()))
        if isinstance(ctx, P.TipoTupContext):
            return T.TipoTupla([self.convertir_tipo(t) for t in ctx.tipoTupla().tipo()])
        if isinstance(ctx, P.TipoRefContext):
            ref = ctx.tipoReferencia()
            return T.TipoReferencia(self.convertir_tipo(ref.tipo()), ref.MUT() is not None)
        nombre = ctx.getText()
        if nombre in self.nombres_struct:
            return T.TipoStruct(nombre)
        if nombre in self.nombres_enum:
            return T.TipoEnum(nombre)
        raise ErrorNoSoportado(ctx, f"El tipo '{nombre}' no existe")

    # =====================================================
    #  Programa y funciones
    # =====================================================

    def visitPrograma(self, ctx):
        """
        [DEFENSA] Arma el módulo completo, en este orden:
            (module
              (import "env" "print_i32" ...)      funciones prestadas
              (memory (export "memory") 1)        1 página = 64 KB, crece si hace falta
              (data ...)                          los textos literales
              (global $__heap ...)                dónde empieza la memoria libre
              (func $__alloc ...)                 el asignador
              (func $main ...) ...                las funciones del programa
              (export "main" (func $main)))       lo que se llama para ejecutar
        Primero se registran todas las firmas para poder llamar a funciones
        declaradas más abajo en el archivo.
        """
        declaraciones = [item.getChild(0) for item in ctx.item()]
        de_tipo = lambda clase: [d for d in declaraciones if isinstance(d, clase)]
        funciones = de_tipo(P.DeclFuncionContext)

        # 1) Structs y enums (provisional, hasta que exista recolector.py).
        self.registrar_tipos(de_tipo(P.DeclStructContext), de_tipo(P.DeclEnumContext))

        # 2) Firmas, para poder llamar funciones declaradas más abajo.
        for f in funciones:
            params = f.listaParametros().parametro() if f.listaParametros() else []
            tipos_params = [self.convertir_tipo(p.tipo()) for p in params]
            retorno = self.convertir_tipo(f.tipo()) if f.tipo() else T.UNIT
            self.funciones[f.ID().getText()] = (tipos_params, retorno)

        # 3) Constantes globales y funciones.
        texto_constantes = self.generar_constantes(de_tipo(P.DeclConstContext))
        texto_funciones = [self.generar_funcion(f) for f in funciones]

        heap = (self.siguiente_dato + 7) // 8 * 8
        partes = ["(module"]
        for nombre, tipo in PREDEFINIDAS.items():
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
        if "main" in self.funciones:
            partes.append('  (export "main" (func $main))')
        partes.append(")")
        return "\n".join(partes)

    def registrar_tipos(self, structs, enums):
        """
        Anota structs (campos en orden) y enums (variantes en orden) en la tabla
        de símbolos. Primero los nombres, para que un struct pueda usar un tipo
        declarado después. Provisional hasta que exista recolector.py.
        """
        self.nombres_struct = {s.ID().getText() for s in structs}
        self.nombres_enum = {e.ID().getText() for e in enums}
        for s in structs:
            campos = [(c.ID().getText(), self.convertir_tipo(c.tipo()), 0, 0) for c in s.declCampo()]
            self.tabla.declarar_struct(s.ID().getText(), campos, 0, 0)
        for e in enums:
            variantes = []
            for v in e.variante():
                tipos = [self.convertir_tipo(t) for t in v.listaTipos().tipo()] if v.listaTipos() else []
                variantes.append((v.ID().getText(), tipos, 0, 0))
            self.tabla.declarar_enum(e.ID().getText(), variantes, 0, 0)

    def generar_constantes(self, constantes):
        """
        const globales -> globals de Wasm. Un global de Wasm solo se puede
        inicializar con una constante simple, así que el valor real se calcula
        en $__iniciar_constantes, que main llama al empezar.
        """
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
        """
        fn f(a: i32) -> i32 { ... }  ->  (func $f (param $a i32) (result i32) ... )
        Los parámetros ya son locales en Wasm. El valor de retorno es lo que
        queda en la pila al final del cuerpo (la expresión final del bloque).
        """
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
            # 'unreachable' le dice al validador de Wasm que nunca se llega aquí.
            self.emitir("unreachable")

        return self.armar_funcion(f"${nombre}", firma, tipo_wasm(retorno))

    def armar_funcion(self, nombre, firma, resultado):
        """Escribe el texto final: cabecera, (local ...) declarados y el cuerpo."""
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
        Cada bloque abre un ámbito nuevo (para el sombreado) y lo cierra al final.
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
        """Una expresión usada como sentencia (f(x);) descarta su valor con drop."""
        hijo = ctx.getChild(0)
        if isinstance(hijo, P.ExpresionContext):
            self.descartar_si_hay_valor(self.visit(hijo))
        else:
            self.visit(hijo)
        return T.UNIT

    def visitDeclLet(self, ctx):
        """
        let x = valor;  ->  (valor) + local.set $x
        Si no hay tipo escrito, se usa el tipo que devolvió el valor (inferencia).
        """
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
        """
        x = v      ->  v; local.set $x
        x += v     ->  local.get $x; v; i32.add; local.set $x
        p.x = v    ->  dirección de p; v; f64.store offset=0     (escribe en memoria)
        a[i] += v  ->  dirección de a[i]; leer; v; sumar; guardar
        """
        lugar = ctx.lugar()
        op = ctx.opAsignacion().getText()
        (wasm, tipo), clase = self.variable_o_error(lugar.ID(0).getText(), lugar)
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
        """return v;  ->  v; return   (el valor queda en la pila y la función termina)"""
        if ctx.expresion():
            self.visit(ctx.expresion())
        self.emitir("return")
        return T.UNIT

    def visitSentenciaIf(self, ctx):
        return self.generar_if(ctx, False)

    def generar_if(self, ctx, con_valor):
        """
        if c { A } else { B }  ->  c; if (result T) A else B end
        La condición es un i32 (0 = false). Si el if se usa como valor
        (if a > b { a } else { b }), el bloque lleva (result T).
        """
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
        """
        [DEFENSA] while c { cuerpo }  se traduce a dos bloques anidados:
            block $fin_N              <- break salta aquí (sale del bloque)
              loop $inicio_N          <- continue salta aquí (vuelve a empezar)
                c; i32.eqz; br_if $fin_N     si c es falsa, salir
                cuerpo
                br $inicio_N                 repetir
              end
            end
        En Wasm 'br' a un block salta a su FINAL y 'br' a un loop salta a su INICIO.
        """
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
        """loop { cuerpo }: igual que while, pero sin condición (solo sale con break o return)."""
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
        """break -> salta al final del bucle más interno (self.bucles es una pila)."""
        self.emitir(f"br $fin_{self.bucles[-1]}")
        return T.UNIT

    def visitSentenciaContinue(self, ctx):
        """continue -> salta al inicio del bucle más interno."""
        self.emitir(f"br $inicio_{self.bucles[-1]}")
        return T.UNIT

    # =====================================================
    #  Expresiones
    #  La gramática anida las reglas por precedencia:
    #  disyuncion (||) > conjuncion (&&) > comparacion > suma > producto > unario
    #  Por eso 2 + 3 * 4 ya llega agrupado como 2 + (3 * 4).
    # =====================================================

    def visitExpresion(self, ctx):
        return self.visit(ctx.disyuncion())

    def visitDisyuncion(self, ctx):
        # [DEFENSA] Cortocircuito, como en Rust:
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
        # [DEFENSA] Cortocircuito:
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
        """a < b -> a; b; i32.lt_s (o f64.lt). El resultado es un bool (i32 0/1)."""
        izquierda = self.visit(ctx.suma(0))
        if not ctx.opRelacional():
            return izquierda
        self.visit(ctx.suma(1))
        self.emitir(OPERADORES[(ctx.opRelacional().getText(), tipo_wasm(izquierda))])
        return T.BOOL

    def generar_binaria(self, ctx):
        """
        Para suma y producto: hijo op hijo op hijo ...
        a - b + c  ->  a; b; i32.sub; c; i32.add   (de izquierda a derecha)
        El tipo del primer operando decide la instrucción (i32.* o f64.*).
        """
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
        """-x: f64 tiene f64.neg; i32 no tiene 'neg' en Wasm, se multiplica por -1."""
        tipo = self.visit(ctx.unario())
        if tipo_wasm(tipo) == "f64":
            self.emitir("f64.neg")
        else:
            self.emitir("i32.const -1")
            self.emitir("i32.mul")
        return sin_referencia(tipo)

    def visitUnarioNegacion(self, ctx):
        """!x: i32.eqz devuelve 1 si x es 0 y 0 si no; justo la negación de un bool."""
        self.visit(ctx.unario())
        self.emitir("i32.eqz")
        return T.BOOL

    def generar_referencia(self, ctx, mutable):
        # [DEFENSA] Referencias:
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
        """*r: la referencia ya es el valor (escalar) o el puntero (compuesto); no hay que leer nada."""
        tipo = self.visit(ctx.unario())
        interno = tipo.interno if isinstance(tipo, T.TipoReferencia) else tipo
        return self.copiar_si_hace_falta(interno)

    def visitUnarioPostfijo(self, ctx):
        return self.visit(ctx.postfijo())

    def visitPostfijo(self, ctx):
        """
        primario seguido de llamadas (f(...)), campos (.x) e índices ([i]).
        p.esquina.x -> carga p, luego el campo esquina, luego el campo x.

        [DEFENSA] Copia de arrays/tuplas: si el resultado es un array o tupla
        copiable leído de una variable (let b = a;), se copia el bloque para que
        modificar b no cambie a. Con & no se copia (_sin_copia).
        """
        copiar = not self._sin_copia
        self._sin_copia = False
        primario, *sufijos = list(ctx.getChildren())

        if sufijos and isinstance(sufijos[0], P.SufijoLlamadaContext):
            if not isinstance(primario, P.PrimIdentContext):
                raise ErrorNoSoportado(ctx, "Solo se puede llamar a una función por su nombre")
            nombre = primario.ID().getText()
            if nombre not in self.funciones and nombre not in PREDEFINIDAS:
                raise ErrorNoSoportado(primario, f"La función '{nombre}' no existe")
            tipo = self.generar_llamada(nombre, sufijos[0])
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
        """
        f(a, b)  ->  a; b; call $f
        En Wasm primero se ponen los argumentos en la pila y luego se llama.
        Devuelve el tipo de retorno de la función (las print_* no devuelven nada).
        """
        argumentos = sufijo.listaArgumentos().expresion() if sufijo.listaArgumentos() else []
        for a in argumentos:
            self.visit(a)
        self.emitir(f"call ${nombre}")
        if nombre in PREDEFINIDAS:
            return T.UNIT
        return self.funciones[nombre][1]

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

        # [DEFENSA] Índice: a[i]  ->  a + i * 8, revisando que 0 <= i < largo.
        # i32.ge_u compara SIN signo: un i negativo se ve como un número enorme,
        # así que una sola comparación cubre i < 0 e i >= largo. Si falla se
        # ejecuta 'unreachable' y el programa se detiene con error de ejecución.
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
        """Arrays y tuplas son Copy en Rust: si el tipo lo necesita, llama a su copiador."""
        if M.necesita_copia(tipo):
            self.emitir(f"call {self.copiador(tipo)}")
        return tipo

    def copiador(self, tipo):
        """
        Genera (una sola vez por tipo) una función que copia el bloque completo.
        Reserva un bloque nuevo y copia los bytes con memory.copy. Si hay arrays
        dentro del array ([[i32; 2]; 2]), también los copia (copia profunda).
        """
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
        """x -> local.get $x (o global.get si es una const global)."""
        (wasm, tipo), clase = self.variable_o_error(ctx.ID().getText(), ctx)
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
        """(3, 2.5) -> reserva 2 slots, guarda 3 en el slot 0 y 2.5 en el slot 1, deja el puntero."""
        expresiones = ctx.expresion()
        puntero = self.reservar(len(expresiones) * M.SLOT)
        tipos = self.guardar_elementos(puntero, expresiones)
        self.emitir(f"local.get {puntero}")
        return T.TipoTupla(tipos)

    def visitLiteralArray(self, ctx):
        """[10, 20, 30] -> reserva 3 slots y guarda cada elemento; deja el puntero."""
        expresiones = ctx.expresion()
        puntero = self.reservar(len(expresiones) * M.SLOT)
        tipos = self.guardar_elementos(puntero, expresiones)
        self.emitir(f"local.get {puntero}")
        return T.TipoArray(tipos[0], len(expresiones))

    def visitLiteralStruct(self, ctx):
        """
        Punto { y: 2.0, x: 1.0 } -> reserva un slot por campo y guarda cada valor
        en el offset de SU campo (el orden de la declaración, no el del literal).
        """
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
        # [DEFENSA] Estado::Completado(200)  ->  [ tag ][ 200 ]
        # El tag es el número de la variante (Pendiente=0, Completado=1, Error=2);
        # el match lo lee para saber qué variante es.
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

    # ----- Literales escalares: van directo a la pila -----

    def visitLitEntero(self, ctx):
        self.emitir(f"i32.const {ctx.getText()}")
        return T.I32

    def visitLitFlotante(self, ctx):
        self.emitir(f"f64.const {ctx.getText()}")
        return T.F64

    def visitLitBooleano(self, ctx):
        """Wasm no tiene booleanos: true = 1, false = 0."""
        self.emitir("i32.const 1" if ctx.getText() == "true" else "i32.const 0")
        return T.BOOL

    def visitLitChar(self, ctx):
        """Un char es su código Unicode: 'R' -> i32.const 82."""
        self.emitir(f"i32.const {ord(decodificar_escapes(ctx.getText()[1:-1]))}")
        return T.CHAR

    def visitLitTexto(self, ctx):
        # [DEFENSA] Cada literal distinto se guarda una vez en la memoria, en un
        # segmento (data ...) que Wasm copia al iniciar: [ largo ][ bytes UTF-8 ].
        # La expresión solo deja en la pila la dirección (puntero) del texto.
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
        [DEFENSA]
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


# =====================================================
#  Funciones auxiliares
# =====================================================

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

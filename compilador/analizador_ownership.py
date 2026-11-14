"""
Tercera pasada semántica: OWNERSHIP y PRÉSTAMOS (fase "ownership").

Corre solo si el verificador de tipos no reportó errores, así que puede
confiar en las anotaciones que este dejó en el árbol: `nodo.tipo` en cada
expresión y `nodo.simbolo` en cada identificador, parámetro, let y patrón.

Reglas que revisa
-----------------
Movimientos (ownership):
  - Un valor NO copiable (String, struct, enum, &mut T) se MUEVE cuando se
    usa como valor: `let b = a;`, `f(a)`, `return a`, guardarlo en un struct,
    array, tupla o variante. Después de moverse, la variable no se puede usar.
  - Copiables (i32, f64, bool, char, &T, arrays y tuplas de copiables) se
    copian y siguen disponibles.
  - Leer un campo o índice NO mueve el contenedor, salvo que lo leído no sea
    copiable (p. ej. un String dentro de un struct): entonces se mueve.
  - Un `match` sobre una variable no la mueve, salvo que un patrón ate por
    valor un dato no copiable (como el String de `Estado::Error(s)`).
  - Pasar una variable `&mut T` a una función no la mueve (se re-presta),
    igual que en Rust.
  - Mover una variable de fuera de un bucle dentro del bucle es error: en la
    siguiente vuelta ya estaría movida.
  - `let x: T;` deja a x sin inicializar: usarla antes de asignarle es error.

Mutabilidad:
  - Asignar a una variable sin `mut` es error (salvo la primera asignación de
    una variable declarada sin valor: `let x: i32; x = 5;`).
  - `&mut x` exige que x sea `mut`. Modificar `p.x` cuando p es `&T` es error.

Préstamos (borrowing). Cada `&x` o `&mut x` crea un préstamo que dura hasta
el ÚLTIMO USO de la variable que lo guarda (como el "non-lexical lifetimes"
de Rust), o hasta el final de la sentencia si nadie lo guarda (p. ej. un
argumento `f(&mut x)`). Mientras un préstamo está activo:
  - no se puede crear `&mut x` si hay cualquier otro préstamo de x;
  - no se puede crear `&x` si hay un `&mut x`;
  - no se puede modificar, mover ni leer x si hay un `&mut x` activo
    (modificar y mover tampoco con un `&x` activo).
  - Una función no puede devolver una referencia a una variable local, y un
    préstamo no puede sobrevivir al bloque donde vive la variable prestada.

Para saber dónde está el último uso de una variable, antes de analizar cada
función se recorre su árbol apuntando la posición (índice de token) de cada
uso; si el uso está dentro de un bucle que empieza después del préstamo, el
préstamo se extiende hasta el final del bucle (en la siguiente vuelta la
referencia se vuelve a usar).
"""
from generado.RustiQVisitor import RustiQVisitor
from generado.RustiQParser import RustiQParser as P
from recolector import posicion
from verificador_tipos import primario_directo, termina_expresion, contiene_break
import tipos as T

FASE = "ownership"


class Prestamo:
    def __init__(self, objetivo, mutable, linea, columna, fin):
        self.objetivo = objetivo      # SimboloVariable prestado
        self.mutable = mutable        # True si es &mut
        self.linea = linea
        self.columna = columna
        self.fin = fin                # índice del último token donde sigue activo
        self.titular = None           # variable que guarda la referencia (None: temporal)

    def descripcion(self):
        que = "como mutable" if self.mutable else "con '&'"
        return f"{que} en la línea {self.linea}"


class EstadoVariable:
    def __init__(self, inicializada):
        self.inicializada = inicializada
        self.asignada = inicializada  # ¿recibió valor alguna vez? (para "let x; x = 1;")
        self.movida = None            # None, o (linea, columna, detalle) del movimiento
        self.prestamos = []           # préstamos que OTROS tienen sobre esta variable
        self.presta = []              # si es una referencia: préstamos que ella guarda

    def copia(self):
        otro = EstadoVariable(self.inicializada)
        otro.asignada = self.asignada
        otro.movida = self.movida
        otro.prestamos = list(self.prestamos)
        otro.presta = list(self.presta)
        return otro


class Bucle:
    def __init__(self, inicio):
        self.inicio = inicio          # (linea, columna) donde empieza el bucle
        self.movidos = {}             # variables de fuera movidas adentro: simbolo -> (linea, col)


def lugar_de(nodo):
    """
    Si el nodo (un `unario` o una `expresion`) es un LUGAR —una variable sola o
    con accesos a campos/índices: x, p.x, a[i].y— devuelve (PrimIdent, sufijos).
    Si no (literal, llamada, operación...), devuelve None.
    """
    if isinstance(nodo, P.ExpresionContext):
        nodo = nodo.disyuncion()
        while nodo.getChildCount() == 1 and not isinstance(nodo, P.UnarioPostfijoContext):
            nodo = nodo.getChild(0)
    if not isinstance(nodo, P.UnarioPostfijoContext):
        return None
    primario, *sufijos = list(nodo.postfijo().getChildren())
    if not isinstance(primario, P.PrimIdentContext):
        return None
    if any(isinstance(s, P.SufijoLlamadaContext) for s in sufijos):
        return None
    return primario, sufijos


def es_referencia(tipo):
    return isinstance(tipo, T.TipoReferencia)


def es_sobrescritura(nodo):
    """¿Es el lado izquierdo de `x = ...` (sin campos ni índices)? Eso no lee a x."""
    if not isinstance(nodo, P.LugarContext) or nodo.getChildCount() != 1:
        return False
    return nodo.parentCtx.opAsignacion().getText() == "="


class AnalizadorOwnership(RustiQVisitor):
    def __init__(self, tabla, errores):
        self.tabla = tabla
        self.errores = errores
        self.estados = {}             # SimboloVariable -> EstadoVariable
        self.usos = {}                # SimboloVariable -> [(indice de token, [bucles que lo contienen])]
        self.sobrescrituras = {}      # SimboloVariable -> [índices de token de cada `x = ...`]
        self.fin_sentencia = 0        # índice del último token de la sentencia actual
        self.bucles = []              # pila de Bucle
        self.declarados = []          # pila: variables declaradas en cada bloque abierto
        self.funcion = None

    # =====================================================
    #  Utilidades
    # =====================================================

    def error(self, ctx, mensaje):
        linea, columna = posicion(ctx)
        self.errores.agregar(FASE, linea, columna, mensaje)

    def estado(self, simbolo):
        return self.estados.get(simbolo)

    def activos(self, simbolo, indice):
        """Préstamos de la variable que siguen vivos en la posición dada."""
        estado = self.estado(simbolo)
        if estado is None:
            return []
        return [p for p in estado.prestamos if p.fin >= indice]

    def ultimo_uso(self, simbolo, desde):
        """
        Índice de token del último uso de la variable después de `desde` y
        antes de que se le asigne otro valor (r = &y termina el préstamo viejo).
        """
        tope = min([i for i in self.sobrescrituras.get(simbolo, []) if i > desde] or [float("inf")])
        ultimo = -1
        for indice, bucles in self.usos.get(simbolo, []):
            if indice <= desde or indice > tope:
                continue
            ultimo = max(ultimo, indice)
            for inicio, fin in bucles:
                if inicio > desde:
                    ultimo = max(ultimo, fin)
        return ultimo

    def registrar_usos(self, nodo, bucles):
        """Pre-recorrido de una función: apunta dónde se usa cada variable."""
        simbolo = getattr(nodo, "simbolo", None)
        if simbolo is not None and isinstance(nodo, (P.PrimIdentContext, P.LugarContext)):
            if es_sobrescritura(nodo):
                self.sobrescrituras.setdefault(simbolo, []).append(nodo.start.tokenIndex)
            else:
                self.usos.setdefault(simbolo, []).append((nodo.start.tokenIndex, list(bucles)))
        if isinstance(nodo, (P.SentenciaWhileContext, P.SentenciaLoopContext)):
            bucles = bucles + [(nodo.start.tokenIndex, nodo.stop.tokenIndex)]
        if nodo.getChildCount():
            for hijo in nodo.getChildren():
                self.registrar_usos(hijo, bucles)

    def declarar(self, simbolo, inicializada):
        self.estados[simbolo] = EstadoVariable(inicializada)
        if self.declarados:
            self.declarados[-1].append(simbolo)

    def revisar_uso(self, simbolo, ctx):
        """¿Se puede leer la variable aquí? Reporta si no está inicializada o fue movida."""
        estado = self.estado(simbolo)
        if estado is None:                      # constante global
            return True
        if not estado.inicializada:
            self.error(ctx, f"La variable '{simbolo.nombre}' no ha sido inicializada")
            return False
        if estado.movida is not None:
            linea, _, detalle = estado.movida
            self.error(ctx, f"La variable '{simbolo.nombre}' fue movida en la línea {linea}"
                            f"{detalle} y ya no se puede usar")
            return False
        return True

    def revisar_lectura(self, simbolo, ctx):
        """Leer (copiar) la variable: además no puede estar prestada como mutable."""
        if not self.revisar_uso(simbolo, ctx):
            return False
        mutables = [p for p in self.activos(simbolo, ctx.start.tokenIndex) if p.mutable]
        if mutables:
            self.error(ctx, f"No se puede usar '{simbolo.nombre}' mientras está prestada "
                            f"{mutables[0].descripcion()}")
            return False
        return True

    def mover(self, simbolo, ctx, detalle=""):
        estado = self.estado(simbolo)
        if estado is None or simbolo.es_constante:
            return
        activos = self.activos(simbolo, ctx.start.tokenIndex)
        if activos:
            self.error(ctx, f"No se puede mover '{simbolo.nombre}' mientras está prestada "
                            f"{activos[0].descripcion()}")
            return
        linea, columna = posicion(ctx)
        estado.movida = (linea, columna, detalle)
        for bucle in reversed(self.bucles):
            if (simbolo.linea, simbolo.columna) < bucle.inicio:
                bucle.movidos.setdefault(simbolo, (linea, columna))
                break

    def usar_valor(self, simbolo, ctx, detalle=""):
        """
        La variable se usa como valor: se copia si es copiable, si no se mueve.
        Devuelve los préstamos que viajan con el valor (si es una referencia).
        """
        if not self.revisar_lectura(simbolo, ctx):
            return []
        estado = self.estado(simbolo)
        if not simbolo.tipo.es_copiable():
            self.mover(simbolo, ctx, detalle)
        return list(estado.presta) if estado is not None else []

    def vincular(self, simbolo, prestamos, ctx):
        """La variable guarda estos préstamos: viven hasta su último uso."""
        estado = self.estado(simbolo)
        if estado is None:
            return
        estado.presta = list(prestamos)
        ultimo = self.ultimo_uso(simbolo, ctx.start.tokenIndex)
        for p in prestamos:
            p.fin = max(p.fin, ultimo)
            p.titular = simbolo

    # ----- Estados en ramas -----

    def copiar_estados(self):
        return {s: e.copia() for s, e in self.estados.items()}

    def fusionar(self, ramas):
        """
        ramas: lista de (estados, diverge). Combina los estados al salir de un
        if/match: una variable queda movida si se movió en ALGUNA rama que
        continúa, e inicializada solo si lo está en TODAS.
        """
        vivas = [e for e, diverge in ramas if not diverge] or [ramas[0][0]]
        resultado = {}
        for simbolo in {s for estados in vivas for s in estados}:
            presentes = [estados[simbolo] for estados in vivas if simbolo in estados]
            nuevo = presentes[0].copia()
            nuevo.inicializada = all(e.inicializada for e in presentes)
            nuevo.asignada = any(e.asignada for e in presentes)
            nuevo.movida = next((e.movida for e in presentes if e.movida), None)
            for e in presentes[1:]:
                for p in e.prestamos:
                    if p not in nuevo.prestamos:
                        nuevo.prestamos.append(p)
                for p in e.presta:
                    if p not in nuevo.presta:
                        nuevo.presta.append(p)
            resultado[simbolo] = nuevo
        return resultado

    # =====================================================
    #  Programa y funciones
    # =====================================================

    def visitPrograma(self, ctx):
        for item in ctx.item():
            self.visit(item.getChild(0))
        return None

    def visitDeclStruct(self, ctx):
        return None

    def visitDeclEnum(self, ctx):
        return None

    def visitDeclConst(self, ctx):
        self.fin_sentencia = ctx.stop.tokenIndex
        self.visit(ctx.expresion())
        return None

    def visitDeclFuncion(self, ctx):
        self.funcion = ctx.simbolo
        self.estados = {}
        self.usos = {}
        self.sobrescrituras = {}
        self.bucles = []
        self.declarados = [[]]
        self.registrar_usos(ctx.bloque(), [])
        if ctx.listaParametros():
            for p in ctx.listaParametros().parametro():
                self.declarar(p.simbolo, True)
        prestamos, _ = self.visitar_bloque(ctx.bloque(), es_cuerpo=True)
        if ctx.bloque().expresion() is not None:
            self.revisar_retorno(ctx.bloque().expresion(), prestamos)
        self.declarados.pop()
        return None

    def revisar_retorno(self, ctx, prestamos):
        """Devolver una referencia a una variable local de la función es error."""
        if not es_referencia(self.funcion.retorno):
            return
        for p in prestamos:
            if not es_referencia(p.objetivo.tipo):
                self.error(ctx, f"La función '{self.funcion.nombre}' devuelve una referencia a "
                                f"'{p.objetivo.nombre}', que deja de existir al terminar la función")
                return

    # =====================================================
    #  Bloques y sentencias
    #  (las sentencias devuelven True si siempre salen con return/break/continue;
    #   las expresiones devuelven la lista de préstamos que viajan con su valor)
    # =====================================================

    def visitar_bloque(self, ctx, es_cuerpo=False):
        self.declarados.append([])
        diverge = False
        for s in ctx.sentencia():
            if self.visit(s):
                diverge = True
        prestamos = self.visit(ctx.expresion()) if ctx.expresion() else []
        # En el cuerpo de una función, lo que sale por el valor final lo revisa
        # revisar_retorno (con un mensaje más claro).
        self.cerrar_ambito(ctx.stop.tokenIndex, [] if es_cuerpo else prestamos)
        return prestamos, diverge

    def cerrar_ambito(self, fin_bloque, prestamos_salientes):
        """
        Al cerrar un bloque mueren sus variables: un préstamo sobre ellas que
        siga vivo después (lo guarda una variable de afuera, o sale como valor
        del bloque) es error.
        """
        declarados = self.declarados.pop()
        for simbolo in declarados:
            estado = self.estado(simbolo)
            if estado is None:
                continue
            for p in estado.prestamos:
                escapa = p in prestamos_salientes or \
                    (p.titular is not None and p.titular not in declarados and p.fin > fin_bloque)
                if escapa:
                    self.errores.agregar(FASE, p.linea, p.columna,
                                         f"'{simbolo.nombre}' no vive lo suficiente: se presta aquí "
                                         f"pero se usa después de que '{simbolo.nombre}' deja de existir")
                    break

    def visitBloque(self, ctx):
        _, diverge = self.visitar_bloque(ctx)
        return diverge

    def visitSentencia(self, ctx):
        anterior = self.fin_sentencia
        self.fin_sentencia = ctx.stop.tokenIndex
        resultado = self.visit(ctx.getChild(0))
        self.fin_sentencia = anterior
        return resultado is True

    def visitDeclLet(self, ctx):
        simbolo = ctx.simbolo
        prestamos = self.visit(ctx.expresion()) if ctx.expresion() else []
        self.declarar(simbolo, ctx.expresion() is not None)   # después: let x = x + 1;
        if prestamos:
            self.vincular(simbolo, prestamos, ctx)
        return False

    def visitDeclConstLocal(self, ctx):
        self.visit(ctx.expresion())
        self.declarar(ctx.simbolo, True)
        return False

    def visitAsignacion(self, ctx):
        lugar = ctx.lugar()
        simbolo = lugar.simbolo
        op = ctx.opAsignacion().getText()
        prestamos = self.visit(ctx.expresion())           # primero el lado derecho
        estado = self.estado(simbolo)
        if estado is None:                                # constante: ya lo reportó el semántico
            return False
        accesos = list(lugar.getChildren())[1:]
        for i, hijo in enumerate(accesos):
            if isinstance(hijo, P.ExpresionContext):      # índices: a[i] = ...
                self.visit(hijo)
        texto = lugar.getText()
        nombre = simbolo.nombre
        indice = lugar.start.tokenIndex

        if accesos:                                       # p.x = ...   a[i] += ...
            if not self.revisar_uso(simbolo, lugar):
                return False
            if es_referencia(simbolo.tipo):
                if not simbolo.tipo.mutable:
                    self.error(lugar, f"No se puede modificar '{texto}' a través de '{nombre}', "
                                      f"que es una referencia inmutable ({simbolo.tipo})")
            elif not simbolo.mutable:
                self.error(lugar, f"No se puede modificar '{texto}' porque '{nombre}' no es "
                                  f"mutable (declárela con 'let mut')")
        else:                                             # x = ...   x += ...
            if op != "=" and not self.revisar_uso(simbolo, lugar):
                return False
            if not simbolo.mutable and (estado.asignada or op != "="):
                self.error(lugar, f"No se puede asignar a '{nombre}' porque no es mutable "
                                  f"(declárela con 'let mut')")
            if op == "=":
                estado.inicializada = True
                estado.asignada = True
                estado.movida = None
                if es_referencia(simbolo.tipo):
                    self.vincular(simbolo, prestamos, ctx)

        activos = self.activos(simbolo, indice)
        if activos:
            self.error(lugar, f"No se puede modificar '{nombre}' mientras está prestada "
                              f"{activos[0].descripcion()}")
        return False

    def visitSentenciaReturn(self, ctx):
        if ctx.expresion():
            prestamos = self.visit(ctx.expresion())
            self.revisar_retorno(ctx.expresion(), prestamos)
        return True

    def visitSentenciaBreak(self, ctx):
        return True

    def visitSentenciaContinue(self, ctx):
        return True

    def visitSentenciaIf(self, ctx):
        self.visit(ctx.expresion())
        antes = self.copiar_estados()
        _, diverge_si = self.visitar_bloque(ctx.bloque(0))
        ramas = [(self.estados, diverge_si)]
        self.estados = antes
        diverge_no = False
        if ctx.ELSE():
            self.estados = self.copiar_estados()
            if ctx.sentenciaIf():
                diverge_no = self.visitSentenciaIf(ctx.sentenciaIf())
            else:
                _, diverge_no = self.visitar_bloque(ctx.bloque(1))
            ramas.append((self.estados, diverge_no))
        else:
            ramas.append((antes, False))
        self.estados = self.fusionar(ramas)
        return diverge_si and diverge_no

    def visitar_cuerpo_bucle(self, ctx_bucle, bloque):
        self.bucles.append(Bucle(posicion(ctx_bucle)))
        _, diverge = self.visitar_bloque(bloque)
        bucle = self.bucles.pop()
        if not diverge:
            for simbolo, (linea, columna) in bucle.movidos.items():
                estado = self.estado(simbolo)
                if estado is not None and estado.movida is not None:
                    self.errores.agregar(FASE, linea, columna,
                                         f"La variable '{simbolo.nombre}' se mueve dentro del bucle: "
                                         f"en la siguiente vuelta ya no tendría valor")
        return diverge

    def visitSentenciaWhile(self, ctx):
        self.visit(ctx.expresion())
        antes = self.copiar_estados()
        diverge = self.visitar_cuerpo_bucle(ctx, ctx.bloque())
        self.estados = self.fusionar([(antes, False), (self.estados, diverge)])
        return False

    def visitSentenciaLoop(self, ctx):
        self.visitar_cuerpo_bucle(ctx, ctx.bloque())
        # Sin break, el loop nunca termina: lo que sigue es inalcanzable.
        return not contiene_break(ctx.bloque())

    # =====================================================
    #  Expresiones
    # =====================================================

    def visitExpresion(self, ctx):
        return self.visit(ctx.disyuncion())

    def visitar_operandos(self, ctx):
        """Operadores binarios: cada operando se usa como valor; el resultado no presta nada."""
        for hijo in ctx.getChildren():
            if not isinstance(hijo, (P.OpRelacionalContext,)) and hijo.getChildCount():
                self.visit(hijo)
        return []

    def visitDisyuncion(self, ctx):
        if ctx.getChildCount() == 1:
            return self.visit(ctx.conjuncion(0))
        return self.visitar_operandos(ctx)

    def visitConjuncion(self, ctx):
        if ctx.getChildCount() == 1:
            return self.visit(ctx.comparacion(0))
        return self.visitar_operandos(ctx)

    def visitComparacion(self, ctx):
        if ctx.getChildCount() == 1:
            return self.visit(ctx.suma(0))
        return self.visitar_operandos(ctx)

    def visitSuma(self, ctx):
        if ctx.getChildCount() == 1:
            return self.visit(ctx.producto(0))
        return self.visitar_operandos(ctx)

    def visitProducto(self, ctx):
        if ctx.getChildCount() == 1:
            return self.visit(ctx.unario(0))
        return self.visitar_operandos(ctx)

    def visitUnarioNegativo(self, ctx):
        self.visit(ctx.unario())
        return []

    def visitUnarioNegacion(self, ctx):
        self.visit(ctx.unario())
        return []

    def visitUnarioDeref(self, ctx):
        lugar = lugar_de(ctx.unario())
        if lugar is None:
            return self.visit(ctx.unario())
        # *r lee a través de la referencia: no mueve a r.
        self.leer_lugar(lugar, mover_si_no_copiable=False)
        if not ctx.tipo.es_copiable():
            self.error(ctx, f"No se puede mover el valor de tipo {ctx.tipo} que está detrás de "
                            f"la referencia '{ctx.unario().getText()}'")
        return []

    def visitUnarioRef(self, ctx):
        return self.prestar(ctx, False)

    def visitUnarioRefMut(self, ctx):
        return self.prestar(ctx, True)

    def prestar(self, ctx, mutable):
        if isinstance(ctx.unario(), P.UnarioDerefContext):      # &*r, &mut *r: re-préstamo
            lugar = lugar_de(ctx.unario().unario())
            if lugar is not None:
                self.leer_lugar(lugar, mover_si_no_copiable=False)
                estado = self.estado(lugar[0].simbolo)
                return list(estado.presta) if estado else []
        lugar = lugar_de(ctx.unario())
        if lugar is None:                       # &5, &f(x): préstamo de un temporal
            return self.visit(ctx.unario())
        primario, sufijos = lugar
        simbolo = primario.simbolo
        nombre = simbolo.nombre
        texto = ctx.unario().getText()
        for sufijo in sufijos:
            if isinstance(sufijo, P.SufijoIndiceContext):
                self.visit(sufijo.expresion())
        if not self.revisar_uso(simbolo, primario):
            return []
        activos = self.activos(simbolo, ctx.start.tokenIndex)
        if mutable:
            if es_referencia(simbolo.tipo) and sufijos:
                if not simbolo.tipo.mutable:
                    self.error(ctx, f"No se puede pedir '&mut {texto}' a través de '{nombre}', "
                                    f"que es una referencia inmutable ({simbolo.tipo})")
            elif not simbolo.mutable:
                self.error(ctx, f"No se puede pedir '&mut {texto}' porque '{nombre}' no es "
                                f"mutable (declárela con 'let mut')")
            if activos:
                self.error(ctx, f"No se puede prestar '{nombre}' como mutable: ya está prestada "
                                f"{activos[0].descripcion()}")
        else:
            mutables = [p for p in activos if p.mutable]
            if mutables:
                self.error(ctx, f"No se puede prestar '{nombre}': ya está prestada "
                                f"{mutables[0].descripcion()}")
        estado = self.estado(simbolo)
        if estado is None:
            return []
        linea, columna = posicion(ctx)
        prestamo = Prestamo(simbolo, mutable, linea, columna, self.fin_sentencia)
        estado.prestamos.append(prestamo)
        return [prestamo]

    def visitUnarioPostfijo(self, ctx):
        return self.visit(ctx.postfijo())

    def visitPostfijo(self, ctx):
        primario, *sufijos = list(ctx.getChildren())

        if sufijos and isinstance(sufijos[0], P.SufijoLlamadaContext):
            prestamos = self.visitar_llamada(primario, sufijos[0])
            for sufijo in sufijos[1:]:
                if isinstance(sufijo, P.SufijoIndiceContext):
                    self.visit(sufijo.expresion())
            return prestamos

        if isinstance(primario, P.PrimIdentContext):
            return self.leer_lugar((primario, sufijos), mover_si_no_copiable=True,
                                   tipo_resultado=ctx.tipo)

        prestamos = self.visit(primario)
        for sufijo in sufijos:
            if isinstance(sufijo, P.SufijoIndiceContext):
                self.visit(sufijo.expresion())
        return prestamos

    def leer_lugar(self, lugar, mover_si_no_copiable, tipo_resultado=None):
        """Lee x, p.x o a[i] como valor. Mueve la variable si lo leído no es copiable."""
        primario, sufijos = lugar
        simbolo = primario.simbolo
        for sufijo in sufijos:
            if isinstance(sufijo, P.SufijoIndiceContext):
                self.visit(sufijo.expresion())
        if not sufijos:
            if not mover_si_no_copiable:
                self.revisar_lectura(simbolo, primario)
                return []
            return self.usar_valor(simbolo, primario)
        if not self.revisar_lectura(simbolo, primario):
            return []
        if mover_si_no_copiable and tipo_resultado is not None and not tipo_resultado.es_copiable():
            texto = primario.getText() + "".join(s.getText() for s in sufijos)
            if es_referencia(simbolo.tipo):
                self.error(primario, f"No se puede mover '{texto}' porque está detrás de la "
                                     f"referencia '{simbolo.nombre}' (use '&{texto}' para prestarlo)")
            else:
                self.mover(simbolo, primario, f" (se movió '{texto}')")
        return []

    def visitar_llamada(self, primario, sufijo):
        funcion = primario.funcion
        argumentos = sufijo.listaArgumentos().expresion() if sufijo.listaArgumentos() else []
        prestamos = []
        for argumento in argumentos:
            directo = primario_directo(argumento)
            if isinstance(directo, P.PrimIdentContext) and es_referencia(directo.simbolo.tipo) \
                    and directo.simbolo.tipo.mutable:
                # f(r) con r: &mut T se re-presta, no se mueve (como en Rust).
                if self.revisar_uso(directo.simbolo, directo):
                    estado = self.estado(directo.simbolo)
                    prestamos += list(estado.presta) if estado else []
            else:
                prestamos += self.visit(argumento)
        if es_referencia(funcion.retorno):
            return prestamos          # la referencia devuelta sale de alguno de los argumentos
        return []

    # ----- Primarios -----

    def visitPrimLiteral(self, ctx):
        return []

    def visitPrimParen(self, ctx):
        return self.visit(ctx.expresion())

    def visitPrimBloque(self, ctx):
        prestamos, _ = self.visitar_bloque(ctx.bloque())
        return prestamos

    def visitPrimIdent(self, ctx):
        return self.usar_valor(ctx.simbolo, ctx)

    def visitar_lista(self, expresiones):
        prestamos = []
        for e in expresiones:
            prestamos += self.visit(e)
        return prestamos

    def visitPrimTupla(self, ctx):
        return self.visitar_lista(ctx.literalTupla().expresion())

    def visitPrimArray(self, ctx):
        return self.visitar_lista(ctx.literalArray().expresion())

    def visitPrimStruct(self, ctx):
        return self.visitar_lista([i.expresion() for i in ctx.literalStruct().inicCampo()])

    def visitPrimEnum(self, ctx):
        valor = ctx.valorEnum()
        return self.visitar_lista(valor.listaArgumentos().expresion() if valor.listaArgumentos() else [])

    def visitPrimMatch(self, ctx):
        return self.visit(ctx.expresionMatch())

    # ----- Match -----

    def visitExpresionMatch(self, ctx):
        lugar = lugar_de(ctx.expresion())
        if lugar is None:
            self.visit(ctx.expresion())
        else:
            self.leer_lugar(lugar, mover_si_no_copiable=False)

        antes = self.estados
        ramas = []
        prestamos = []
        for brazo in ctx.brazoMatch():
            self.estados = {s: e.copia() for s, e in antes.items()}
            self.declarados.append([])
            mueve = self.atar_patron(brazo.patron())
            # Si el match es sobre una referencia (match r { ... } con r: &E),
            # los patrones ven el valor prestado y no mueven nada (como en Rust).
            if mueve is not None and lugar is not None and not es_referencia(ctx.expresion().tipo):
                self.mover(lugar[0].simbolo, mueve,
                           f" (el patrón '{mueve.getText()}' toma un valor no copiable)")
            del_brazo = self.visit(brazo.expresion())
            prestamos += del_brazo
            self.cerrar_ambito(brazo.stop.tokenIndex, del_brazo)
            ramas.append((self.estados, termina_expresion(brazo.expresion())))
        self.estados = self.fusionar(ramas)
        return prestamos

    def atar_patron(self, patron):
        """Declara las variables del patrón. Devuelve el PatIdent que ata un valor no copiable, si hay."""
        mueve = None
        if isinstance(patron, P.PatIdentContext):
            self.declarar(patron.simbolo, True)
            if not patron.simbolo.tipo.es_copiable():
                mueve = patron
        elif isinstance(patron, P.PatVarianteContext) and patron.listaPatrones():
            for sub in patron.listaPatrones().patron():
                mueve = self.atar_patron(sub) or mueve
        elif isinstance(patron, P.PatTuplaContext):
            for sub in patron.patron():
                mueve = self.atar_patron(sub) or mueve
        return mueve

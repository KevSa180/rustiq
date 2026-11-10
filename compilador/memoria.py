"""
[DEFENSA] Representación en memoria de los valores de RustiQ dentro de Wasm.
El enunciado pide definir y documentar este diseño; este archivo es esa respuesta.

Wasm solo tiene números (i32, f64) y una memoria lineal: un gran arreglo de
bytes. Las decisiones de este archivo son:

1. Escalares (i32, bool, char, f64) viajan como números en la pila de Wasm.
   bool y char se representan como i32 (char = código Unicode).

2. Valores compuestos (struct, tupla, array, enum, String) viven en la memoria
   y en la pila viaja un PUNTERO (i32) a su bloque.

3. Cada bloque se divide en "slots" de 8 bytes. Un slot guarda un escalar o un
   puntero a otro bloque. Así todos los offsets son índice * 8.

       struct Punto { x: f64, y: f64 }   ->  [ x ][ y ]               (2 slots)
       (i32, f64)                        ->  [ .0 ][ .1 ]             (2 slots)
       [i32; 3]                          ->  [ 0 ][ 1 ][ 2 ]          (3 slots)
       Estado::Completado(200)           ->  [ tag=1 ][ 200 ]         (1 + datos)
       Estado::Pendiente                 ->  [ tag=0 ]

4. String: [ largo en bytes (i32, 4 bytes) ][ bytes UTF-8 ... ]
   Los literales de texto se guardan en segmentos de datos al inicio de la
   memoria; el resto se reserva con un asignador simple ($__alloc) que avanza
   un puntero y nunca libera (suficiente para programas de prueba).

5. Referencias:
   - &T a un valor compuesto: es el mismo puntero (escribir p.x a través de
     &mut Punto modifica el original).
   - &T a un escalar: se representa con el valor. La gramática no permite
     asignar a través de *r, así que nunca hace falta su dirección.

6. Arrays y tuplas cuyos elementos son copiables son Copy (como en Rust): al
   usarlos como valor se copian (función $__copiar_N) para que modificar la
   copia no cambie el original. Structs, enums y String se MUEVEN: compartir
   el puntero es seguro porque el origen ya no se puede usar.
"""
import tipos as T

SLOT = 8                  # bytes por campo/elemento: cabe un f64 o un i32
INICIO_DATOS = 8          # la dirección 0 se deja libre (como un "null")


def es_compuesto(tipo):
    """¿Vive en memoria (y en la pila viaja su puntero)?"""
    return isinstance(tipo, (T.TipoStruct, T.TipoEnum, T.TipoArray, T.TipoTupla)) \
        or tipo == T.STRING


def sin_referencia(tipo):
    """&Punto -> Punto. Permite que p.x funcione igual si p es un Punto o un &Punto."""
    while isinstance(tipo, T.TipoReferencia):
        tipo = tipo.interno
    return tipo


def tipo_wasm(tipo):
    """
    [DEFENSA] Tipo de RustiQ -> tipo de Wasm (Wasm solo conoce números).
        f64                                    -> f64
        i32, bool, char                        -> i32
        struct, enum, array, tupla, String     -> i32 (un puntero)
        &T                                     -> lo mismo que T
        ()                                     -> None (no deja valor)
    """
    tipo = sin_referencia(tipo)
    if tipo == T.UNIT:
        return None
    if tipo == T.F64:
        return "f64"
    return "i32"          # i32, bool, char y punteros a valores compuestos


def cargar(tipo):
    """Instrucción para LEER un slot de memoria de ese tipo."""
    return "f64.load" if tipo_wasm(tipo) == "f64" else "i32.load"


def guardar(tipo):
    """Instrucción para ESCRIBIR un slot de memoria de ese tipo."""
    return "f64.store" if tipo_wasm(tipo) == "f64" else "i32.store"


def necesita_copia(tipo):
    """Arrays y tuplas copiables se copian al usarse como valor."""
    return isinstance(tipo, (T.TipoArray, T.TipoTupla)) and tipo.es_copiable()


def tipos_de_slots(tipo):
    """Tipo de cada slot del bloque de un array o una tupla."""
    if isinstance(tipo, T.TipoArray):
        return [tipo.elemento] * tipo.longitud
    return list(tipo.elementos)


def tamano_bloque(tipo):
    """Bytes que ocupa el bloque de un array o tupla: [i32; 3] -> 24."""
    return len(tipos_de_slots(tipo)) * SLOT


def offset_slot(indice):
    """El elemento i está i * 8 bytes después del inicio del bloque."""
    return indice * SLOT


def offset_campo(simbolo_struct, campo):
    """Punto { x, y }: x en offset 0, y en offset 8 (orden de la declaración)."""
    return list(simbolo_struct.campos).index(campo) * SLOT


def tag_de_variante(simbolo_enum, variante):
    """Número de la variante según su orden: Pendiente=0, Completado=1, Error=2."""
    return simbolo_enum.nombres_variantes().index(variante)


def offset_dato_variante(indice):
    """El slot 0 es el tag; los datos empiezan en el slot 1."""
    return (indice + 1) * SLOT


def bytes_wat(texto_bytes):
    """Bytes -> texto para un segmento (data ...) de WAT."""
    return "".join(f"\\{b:02x}" for b in texto_bytes)


# [DEFENSA] Asignador de memoria ("bump allocator"):
#   - $__heap apunta a la primera dirección libre.
#   - $__alloc(n) devuelve esa dirección y avanza $__heap n bytes (redondeado a 8).
#   - Si se pasa del tamaño actual, pide más con memory.grow (páginas de 64 KB).
#   - Nunca libera memoria: es simple y alcanza para programas de prueba.
FUNCION_ALLOC = """  (func $__alloc (param $n i32) (result i32)
    (local $p i32)
    global.get $__heap
    local.set $p
    global.get $__heap
    local.get $n
    i32.const 7
    i32.add
    i32.const -8
    i32.and
    i32.add
    global.set $__heap
    block $listo
      loop $crecer
        global.get $__heap
        memory.size
        i32.const 65536
        i32.mul
        i32.le_u
        br_if $listo
        i32.const 1
        memory.grow
        drop
        br $crecer
      end
    end
    local.get $p
  )"""

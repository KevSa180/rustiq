"""
Representación en memoria de los valores de RustiQ dentro de Wasm.

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

SLOT = 8
INICIO_DATOS = 8          # la dirección 0 se deja libre (como un "null")


def es_compuesto(tipo):
    return isinstance(tipo, (T.TipoStruct, T.TipoEnum, T.TipoArray, T.TipoTupla)) \
        or tipo == T.STRING


def sin_referencia(tipo):
    while isinstance(tipo, T.TipoReferencia):
        tipo = tipo.interno
    return tipo


def tipo_wasm(tipo):
    """Tipo de RustiQ -> tipo de Wasm. None si no ocupa valor (unit)."""
    tipo = sin_referencia(tipo)
    if tipo == T.UNIT:
        return None
    if tipo == T.F64:
        return "f64"
    return "i32"          # i32, bool, char y punteros a valores compuestos


def cargar(tipo):
    return "f64.load" if tipo_wasm(tipo) == "f64" else "i32.load"


def guardar(tipo):
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
    return len(tipos_de_slots(tipo)) * SLOT


def offset_slot(indice):
    return indice * SLOT


def offset_campo(simbolo_struct, campo):
    return list(simbolo_struct.campos).index(campo) * SLOT


def tag_de_variante(simbolo_enum, variante):
    return simbolo_enum.nombres_variantes().index(variante)


def offset_dato_variante(indice):
    """El slot 0 es el tag; los datos empiezan en el slot 1."""
    return (indice + 1) * SLOT


def bytes_wat(texto_bytes):
    """Bytes -> texto para un segmento (data ...) de WAT."""
    return "".join(f"\\{b:02x}" for b in texto_bytes)


# Asignador: devuelve el puntero actual y lo avanza n bytes (múltiplo de 8).
# Si se pasa del tamaño de la memoria, la hace crecer.
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

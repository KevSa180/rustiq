"""
Pruebas de las fases de análisis (recolector, verificador de tipos y ownership).

- tests/invalidos/semantico/*.rq  y  tests/invalidos/ownership/*.rq:
  cada archivo empieza con una o más líneas
      // Error esperado: <fase> <línea>:<columna> <fragmento del mensaje>
  El programa NO debe producir WAT y cada error esperado debe aparecer con esa
  fase, línea y columna, y con el fragmento dentro del mensaje.

- tests/validos/*.rq: casos límite que SÍ deben compilar (y, si traen
  "// Salida esperada:", producir esa salida al ejecutarse).
"""
import glob
import os
import re
import sys
import unittest

CARPETA = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, CARPETA)

from errores import ListaErrores                                # noqa: E402
from correr import compilar_a_wat, analizar                     # noqa: E402
from ejecutor_wasm import wat_a_wasm, validar, ejecutar         # noqa: E402

INVALIDOS = os.path.join(os.path.dirname(__file__), "invalidos")
VALIDOS = os.path.join(os.path.dirname(__file__), "validos")
PATRON_ESPERADO = re.compile(r"^// Error esperado: (\S+) (\d+):(\d+) ?(.*)$")


def leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return f.read()


def errores_esperados(codigo):
    esperados = []
    for linea in codigo.splitlines():
        m = PATRON_ESPERADO.match(linea.strip())
        if m:
            esperados.append((m.group(1), int(m.group(2)), int(m.group(3)), m.group(4)))
    return esperados


def salida_esperada(codigo):
    lineas = codigo.splitlines()
    for i, linea in enumerate(lineas):
        if linea.strip() == "// Salida esperada:":
            esperada = []
            for siguiente in lineas[i + 1:]:
                if not siguiente.startswith("// "):
                    break
                esperada.append(siguiente[3:])
            return esperada
    return None


def archivos(carpeta):
    return sorted(glob.glob(os.path.join(carpeta, "*.rq")))


class PruebasProgramasInvalidos(unittest.TestCase):
    def revisar_carpeta(self, carpeta, fase):
        rutas = archivos(os.path.join(INVALIDOS, carpeta))
        self.assertTrue(rutas, f"No hay pruebas en tests/invalidos/{carpeta}")
        for ruta in rutas:
            codigo = leer(ruta)
            esperados = errores_esperados(codigo)
            with self.subTest(archivo=os.path.basename(ruta)):
                self.assertTrue(esperados, "El archivo no declara '// Error esperado:'")
                errores = ListaErrores()
                wat = compilar_a_wat(codigo, errores)
                self.assertIsNone(wat, "Un programa con errores no debe producir código")
                reales = [(e.fase, e.linea, e.columna, e.mensaje) for e in errores.ordenados()]
                for fase_e, linea, columna, fragmento in esperados:
                    coincide = [r for r in reales
                                if r[:3] == (fase_e, linea, columna) and fragmento in r[3]]
                    self.assertTrue(coincide,
                                    f"Se esperaba [{fase_e}] {linea}:{columna} '{fragmento}'; "
                                    f"se obtuvo: {reales}")
                # Todos los errores reportados deben ser de la fase que se prueba:
                # una fase no corre si la anterior dejó errores.
                self.assertEqual({r[0] for r in reales}, {fase},
                                 f"Errores de otra fase mezclados: {reales}")

    def test_errores_semanticos(self):
        self.revisar_carpeta("semantico", "semántico")

    def test_errores_de_ownership(self):
        self.revisar_carpeta("ownership", "ownership")


class PruebasProgramasValidos(unittest.TestCase):
    def test_casos_limite_compilan_y_corren(self):
        rutas = archivos(VALIDOS)
        self.assertTrue(rutas, "No hay pruebas en tests/validos")
        for ruta in rutas:
            codigo = leer(ruta)
            with self.subTest(archivo=os.path.basename(ruta)):
                errores = ListaErrores()
                wat = compilar_a_wat(codigo, errores)
                self.assertIsNotNone(wat, "No compiló: " +
                                     "; ".join(str(e) for e in errores.ordenados()))
                esperada = salida_esperada(codigo)
                if esperada is not None:
                    bytes_wasm = wat_a_wasm(wat)
                    validar(bytes_wasm)
                    self.assertEqual(ejecutar(bytes_wasm), esperada)


class PruebasFases(unittest.TestCase):
    def test_fase_semantica_no_corre_si_hay_error_sintactico(self):
        errores = ListaErrores()
        arbol, _ = analizar("fn main() { let x = ; foo(); }", errores)
        self.assertIsNone(arbol)
        self.assertEqual({e.fase for e in errores.errores}, {"sintáctico"})

    def test_ownership_no_corre_si_hay_error_semantico(self):
        # 'x = 2' sin mut sería error de ownership, pero el error de tipos va primero.
        errores = ListaErrores()
        arbol, _ = analizar("fn main() { let x = 1; x = 2; let y: i32 = true; }", errores)
        self.assertIsNone(arbol)
        self.assertEqual({e.fase for e in errores.errores}, {"semántico"})

    def test_programa_valido_deja_la_tabla_llena(self):
        errores = ListaErrores()
        arbol, tabla = analizar("""
            struct P { x: i32 }
            enum E { A, B(i32) }
            fn f(p: &P) -> i32 { p.x }
            fn main() { let p = P { x: 1 }; print_i32(f(&p)); }
        """, errores)
        self.assertIsNotNone(arbol)
        self.assertEqual(list(tabla.buscar_struct("P").campos), ["x"])
        self.assertEqual(tabla.buscar_enum("E").nombres_variantes(), ["A", "B"])
        self.assertEqual(str(tabla.buscar_funcion("f").retorno), "i32")
        self.assertIsNotNone(tabla.buscar_funcion("print_str"))

    def test_errores_lexicos_y_sintacticos_del_ejemplo(self):
        errores = ListaErrores()
        compilar_a_wat(leer(os.path.join(CARPETA, "ejemplos", "error1.rq")), errores)
        fases = [e.fase for e in errores.ordenados()]
        self.assertIn("léxico", fases)
        self.assertIn("sintáctico", fases)


if __name__ == "__main__":
    unittest.main()

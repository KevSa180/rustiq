"""
Pruebas de punta a punta del backend Wasm.

Cada programa de ejemplos/wasm/ trae su salida esperada en comentarios:
    // Salida esperada:
    // 42
Se compila a WAT, se convierte a .wasm, se valida, se ejecuta y se compara.
"""
import glob
import os
import sys
import unittest

CARPETA = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, CARPETA)

from errores import ListaErrores
from correr import compilar_a_wat
from ejecutor_wasm import wat_a_wasm, validar, ejecutar, ErrorWasm

EJEMPLOS = os.path.join(CARPETA, "ejemplos", "wasm")


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


def compilar_y_ejecutar(codigo):
    errores = ListaErrores()
    wat = compilar_a_wat(codigo, errores)
    if wat is None:
        raise AssertionError("No compiló: " + "; ".join(str(e) for e in errores.ordenados()))
    bytes_wasm = wat_a_wasm(wat)
    validar(bytes_wasm)
    return ejecutar(bytes_wasm)


class PruebasEjemplos(unittest.TestCase):
    def test_ejemplos_con_salida_esperada(self):
        archivos = sorted(glob.glob(os.path.join(EJEMPLOS, "*.rq")))
        self.assertTrue(archivos, "No hay ejemplos en ejemplos/wasm")
        for ruta in archivos:
            with open(ruta, encoding="utf-8") as f:
                codigo = f.read()
            esperada = salida_esperada(codigo)
            if esperada is None:
                continue
            with self.subTest(ejemplo=os.path.basename(ruta)):
                self.assertEqual(compilar_y_ejecutar(codigo), esperada)

    def test_division_por_cero_falla_al_ejecutar(self):
        with open(os.path.join(EJEMPLOS, "error_division.rq"), encoding="utf-8") as f:
            codigo = f.read()
        with self.assertRaises(ErrorWasm) as e:
            compilar_y_ejecutar(codigo)
        self.assertIn("División entera por cero", str(e.exception))


class PruebasNoSoportado(unittest.TestCase):
    def test_string_se_reporta_con_linea_y_columna(self):
        errores = ListaErrores()
        wat = compilar_a_wat('fn main() {\n    let s = "hola";\n}', errores)
        self.assertIsNone(wat)
        e = errores.ordenados()[0]
        self.assertEqual((e.fase, e.linea, e.columna), ("generación", 2, 13))

    def test_error_sintactico_no_genera_wat(self):
        errores = ListaErrores()
        self.assertIsNone(compilar_a_wat("fn main() { let x = ; }", errores))
        self.assertEqual(errores.ordenados()[0].fase, "sintáctico")


if __name__ == "__main__":
    unittest.main()

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from errores import ListaErrores
from tipos import I32, F64, STRING, TipoStruct, TipoEnum
from tabla_simbolos import TablaSimbolos, SimboloVariable, SimboloFuncion


def var(nombre, tipo=I32, mutable=False, linea=1, columna=1, const=False):
    return SimboloVariable(nombre, tipo, mutable, linea, columna, es_constante=const)


class PruebasAmbitos(unittest.TestCase):
    def setUp(self):
        self.errores = ListaErrores()
        self.tabla = TablaSimbolos(self.errores)

    def test_variable_declarada_se_encuentra(self):
        self.tabla.insertar_variable(var("x"))
        self.assertEqual(self.tabla.buscar("x").tipo, I32)
        self.assertFalse(self.errores.hay_errores())

    def test_variable_no_declarada(self):
        self.assertIsNone(self.tabla.resolver_variable("y", 4, 9))
        self.assertEqual(len(self.errores.errores), 1)
        e = self.errores.errores[0]
        self.assertEqual((e.fase, e.linea, e.columna), ("semántico", 4, 9))
        self.assertIn("'y' no está declarada", e.mensaje)

    def test_duplicada_en_mismo_ambito(self):
        self.tabla.insertar_variable(var("x", linea=2))
        ok = self.tabla.insertar_variable(var("x", linea=3, columna=9))
        self.assertFalse(ok)
        e = self.errores.errores[0]
        self.assertEqual((e.linea, e.columna), (3, 9))
        self.assertIn("ya fue declarada en este ámbito (línea 2)", e.mensaje)

    def test_sombreado_en_ambito_interior(self):
        self.tabla.insertar_variable(var("x", tipo=I32))
        self.tabla.abrir_ambito()
        self.assertTrue(self.tabla.insertar_variable(var("x", tipo=F64)))
        self.assertEqual(self.tabla.buscar("x").tipo, F64)
        self.tabla.cerrar_ambito()
        self.assertEqual(self.tabla.buscar("x").tipo, I32)
        self.assertFalse(self.errores.hay_errores())

    def test_variable_muere_al_cerrar_ambito(self):
        self.tabla.abrir_ambito()
        self.tabla.insertar_variable(var("temp"))
        self.tabla.cerrar_ambito()
        self.assertIsNone(self.tabla.buscar("temp"))

    def test_variable_exterior_visible_dentro(self):
        self.tabla.insertar_variable(var("x"))
        self.tabla.abrir_ambito()
        self.tabla.abrir_ambito()
        self.assertIsNotNone(self.tabla.buscar("x"))
        self.assertIsNone(self.tabla.buscar_en_ambito_actual("x"))
        self.assertEqual(self.tabla.nivel(), 2)

    def test_no_se_cierra_el_global(self):
        with self.assertRaises(RuntimeError):
            self.tabla.cerrar_ambito()

    def test_constante_duplicada(self):
        self.tabla.insertar_variable(var("MAX", const=True))
        self.tabla.insertar_variable(var("MAX", const=True, linea=2))
        self.assertIn("La constante 'MAX'", self.errores.errores[0].mensaje)


class PruebasFunciones(unittest.TestCase):
    def setUp(self):
        self.errores = ListaErrores()
        self.tabla = TablaSimbolos(self.errores)

    def test_funcion_registrada(self):
        f = SimboloFuncion("doble", [var("x")], I32, 1, 1)
        self.tabla.insertar_funcion(f)
        self.assertEqual(self.tabla.buscar_funcion("doble").tipos_parametros(), [I32])
        self.assertFalse(self.errores.hay_errores())

    def test_funcion_duplicada(self):
        self.tabla.insertar_funcion(SimboloFuncion("f", [], None, 1, 1))
        ok = self.tabla.insertar_funcion(SimboloFuncion("f", [], None, 5, 1))
        self.assertFalse(ok)
        self.assertIn("La función 'f' ya fue declarada (línea 1)", self.errores.errores[0].mensaje)

    def test_parametro_repetido(self):
        f = SimboloFuncion("f", [var("a", columna=6), var("a", columna=14)], None, 1, 1)
        self.tabla.insertar_funcion(f)
        e = self.errores.errores[0]
        self.assertEqual(e.columna, 14)
        self.assertIn("parámetro 'a' está repetido", e.mensaje)

    def test_funcion_inexistente(self):
        self.assertIsNone(self.tabla.resolver_funcion("nada", 7, 5))
        self.assertIn("La función 'nada' no existe", self.errores.errores[0].mensaje)


class PruebasStructsYEnums(unittest.TestCase):
    def setUp(self):
        self.errores = ListaErrores()
        self.tabla = TablaSimbolos(self.errores)

    def test_struct_con_campos(self):
        s = self.tabla.declarar_struct("Punto", [("x", F64, 2, 5), ("y", F64, 3, 5)], 1, 8)
        self.assertEqual(s.tipo, TipoStruct("Punto"))
        self.assertEqual(s.tipo_campo("y"), F64)
        self.assertIsNone(s.tipo_campo("z"))
        self.assertEqual(list(s.campos), ["x", "y"])

    def test_campo_repetido(self):
        self.tabla.declarar_struct("P", [("x", F64, 2, 5), ("x", I32, 3, 5)], 1, 8)
        e = self.errores.errores[0]
        self.assertEqual(e.linea, 3)
        self.assertIn("campo 'x' está repetido en el struct 'P'", e.mensaje)

    def test_struct_duplicado(self):
        self.tabla.declarar_struct("P", [], 1, 8)
        self.assertIsNone(self.tabla.declarar_struct("P", [], 5, 8))
        self.assertIn("El tipo 'P' ya fue declarado (línea 1)", self.errores.errores[0].mensaje)

    def test_enum_con_variantes(self):
        e = self.tabla.declarar_enum("Estado", [
            ("Pendiente", [], 2, 5),
            ("Completado", [I32], 3, 5),
            ("Error", [STRING], 4, 5),
        ], 1, 6)
        self.assertEqual(e.tipo, TipoEnum("Estado"))
        self.assertEqual(e.nombres_variantes(), ["Pendiente", "Completado", "Error"])
        self.assertEqual(e.tipos_variante("Completado"), [I32])
        self.assertEqual(e.tipos_variante("Pendiente"), [])
        self.assertIsNone(e.tipos_variante("Otro"))

    def test_variante_repetida(self):
        self.tabla.declarar_enum("E", [("A", [], 2, 5), ("A", [I32], 3, 5)], 1, 6)
        self.assertIn("variante 'A' está repetida en el enum 'E'", self.errores.errores[0].mensaje)

    def test_struct_y_enum_con_mismo_nombre(self):
        self.tabla.declarar_struct("Dato", [], 1, 8)
        self.assertIsNone(self.tabla.declarar_enum("Dato", [("A", [], 3, 5)], 3, 6))
        self.assertTrue(self.errores.hay_errores())

    def test_tipo_por_nombre(self):
        self.tabla.declarar_struct("Punto", [], 1, 8)
        self.tabla.declarar_enum("Estado", [("A", [], 3, 5)], 3, 6)
        self.assertEqual(self.tabla.tipo_por_nombre("Punto", 9, 1), TipoStruct("Punto"))
        self.assertEqual(self.tabla.tipo_por_nombre("Estado", 9, 1), TipoEnum("Estado"))
        self.assertFalse(self.errores.hay_errores())
        self.assertIsNone(self.tabla.tipo_por_nombre("Pnto", 9, 12))
        self.assertIn("El tipo 'Pnto' no existe", self.errores.errores[0].mensaje)


if __name__ == "__main__":
    unittest.main()

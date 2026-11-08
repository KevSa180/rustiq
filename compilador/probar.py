import sys
from antlr4 import InputStream, CommonTokenStream
from generado.RustiQLexer import RustiQLexer
from generado.RustiQParser import RustiQParser
from errores import ListaErrores, ColectorErrores

with open(sys.argv[1], encoding="utf-8") as f:
    codigo = f.read()

errores = ListaErrores()

lexer = RustiQLexer(InputStream(codigo))
lexer.removeErrorListeners()
lexer.addErrorListener(ColectorErrores("léxico", errores))

tokens = CommonTokenStream(lexer)
parser = RustiQParser(tokens)
parser.removeErrorListeners()
parser.addErrorListener(ColectorErrores("sintáctico", errores))

arbol = parser.programa()

if errores.hay_errores():
    for e in errores.ordenados():
        print(e)
else:
    print("Sin errores")
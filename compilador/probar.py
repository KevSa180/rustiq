import sys
from antlr4 import InputStream, CommonTokenStream
from generado.RustiQLexer import RustiQLexer
from generado.RustiQParser import RustiQParser

with open(sys.argv[1], encoding="utf-8") as f:
    codigo = f.read()

lexer = RustiQLexer(InputStream(codigo))
tokens = CommonTokenStream(lexer)
parser = RustiQParser(tokens)
arbol = parser.programa()

print(arbol.toStringTree(recog=parser))
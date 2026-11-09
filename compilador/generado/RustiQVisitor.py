# Generated from RustiQ.g4 by ANTLR 4.13.2
from antlr4 import *
if "." in __name__:
    from .RustiQParser import RustiQParser
else:
    from RustiQParser import RustiQParser

# This class defines a complete generic visitor for a parse tree produced by RustiQParser.

class RustiQVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by RustiQParser#programa.
    def visitPrograma(self, ctx:RustiQParser.ProgramaContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#item.
    def visitItem(self, ctx:RustiQParser.ItemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#declFuncion.
    def visitDeclFuncion(self, ctx:RustiQParser.DeclFuncionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#listaParametros.
    def visitListaParametros(self, ctx:RustiQParser.ListaParametrosContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#parametro.
    def visitParametro(self, ctx:RustiQParser.ParametroContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#declConst.
    def visitDeclConst(self, ctx:RustiQParser.DeclConstContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#declStruct.
    def visitDeclStruct(self, ctx:RustiQParser.DeclStructContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#declCampo.
    def visitDeclCampo(self, ctx:RustiQParser.DeclCampoContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#declEnum.
    def visitDeclEnum(self, ctx:RustiQParser.DeclEnumContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#variante.
    def visitVariante(self, ctx:RustiQParser.VarianteContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#listaTipos.
    def visitListaTipos(self, ctx:RustiQParser.ListaTiposContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#TipoPrim.
    def visitTipoPrim(self, ctx:RustiQParser.TipoPrimContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#TipoString.
    def visitTipoString(self, ctx:RustiQParser.TipoStringContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#TipoArr.
    def visitTipoArr(self, ctx:RustiQParser.TipoArrContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#TipoTup.
    def visitTipoTup(self, ctx:RustiQParser.TipoTupContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#TipoRef.
    def visitTipoRef(self, ctx:RustiQParser.TipoRefContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#TipoNombre.
    def visitTipoNombre(self, ctx:RustiQParser.TipoNombreContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#tipoPrimitivo.
    def visitTipoPrimitivo(self, ctx:RustiQParser.TipoPrimitivoContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#tipoArray.
    def visitTipoArray(self, ctx:RustiQParser.TipoArrayContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#tipoTupla.
    def visitTipoTupla(self, ctx:RustiQParser.TipoTuplaContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#tipoReferencia.
    def visitTipoReferencia(self, ctx:RustiQParser.TipoReferenciaContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#bloque.
    def visitBloque(self, ctx:RustiQParser.BloqueContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#sentencia.
    def visitSentencia(self, ctx:RustiQParser.SentenciaContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#declLet.
    def visitDeclLet(self, ctx:RustiQParser.DeclLetContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#declConstLocal.
    def visitDeclConstLocal(self, ctx:RustiQParser.DeclConstLocalContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#asignacion.
    def visitAsignacion(self, ctx:RustiQParser.AsignacionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#opAsignacion.
    def visitOpAsignacion(self, ctx:RustiQParser.OpAsignacionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#lugar.
    def visitLugar(self, ctx:RustiQParser.LugarContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#sentenciaReturn.
    def visitSentenciaReturn(self, ctx:RustiQParser.SentenciaReturnContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#sentenciaBreak.
    def visitSentenciaBreak(self, ctx:RustiQParser.SentenciaBreakContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#sentenciaContinue.
    def visitSentenciaContinue(self, ctx:RustiQParser.SentenciaContinueContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#sentenciaWhile.
    def visitSentenciaWhile(self, ctx:RustiQParser.SentenciaWhileContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#sentenciaLoop.
    def visitSentenciaLoop(self, ctx:RustiQParser.SentenciaLoopContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#sentenciaIf.
    def visitSentenciaIf(self, ctx:RustiQParser.SentenciaIfContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#expresion.
    def visitExpresion(self, ctx:RustiQParser.ExpresionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#disyuncion.
    def visitDisyuncion(self, ctx:RustiQParser.DisyuncionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#conjuncion.
    def visitConjuncion(self, ctx:RustiQParser.ConjuncionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#comparacion.
    def visitComparacion(self, ctx:RustiQParser.ComparacionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#opRelacional.
    def visitOpRelacional(self, ctx:RustiQParser.OpRelacionalContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#suma.
    def visitSuma(self, ctx:RustiQParser.SumaContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#producto.
    def visitProducto(self, ctx:RustiQParser.ProductoContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#UnarioNegativo.
    def visitUnarioNegativo(self, ctx:RustiQParser.UnarioNegativoContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#UnarioNegacion.
    def visitUnarioNegacion(self, ctx:RustiQParser.UnarioNegacionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#UnarioRefMut.
    def visitUnarioRefMut(self, ctx:RustiQParser.UnarioRefMutContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#UnarioRef.
    def visitUnarioRef(self, ctx:RustiQParser.UnarioRefContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#UnarioDeref.
    def visitUnarioDeref(self, ctx:RustiQParser.UnarioDerefContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#UnarioPostfijo.
    def visitUnarioPostfijo(self, ctx:RustiQParser.UnarioPostfijoContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#postfijo.
    def visitPostfijo(self, ctx:RustiQParser.PostfijoContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#sufijoLlamada.
    def visitSufijoLlamada(self, ctx:RustiQParser.SufijoLlamadaContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#listaArgumentos.
    def visitListaArgumentos(self, ctx:RustiQParser.ListaArgumentosContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#sufijoCampo.
    def visitSufijoCampo(self, ctx:RustiQParser.SufijoCampoContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#sufijoIndice.
    def visitSufijoIndice(self, ctx:RustiQParser.SufijoIndiceContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#PrimLiteral.
    def visitPrimLiteral(self, ctx:RustiQParser.PrimLiteralContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#PrimIdent.
    def visitPrimIdent(self, ctx:RustiQParser.PrimIdentContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#PrimTupla.
    def visitPrimTupla(self, ctx:RustiQParser.PrimTuplaContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#PrimArray.
    def visitPrimArray(self, ctx:RustiQParser.PrimArrayContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#PrimStruct.
    def visitPrimStruct(self, ctx:RustiQParser.PrimStructContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#PrimEnum.
    def visitPrimEnum(self, ctx:RustiQParser.PrimEnumContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#PrimMatch.
    def visitPrimMatch(self, ctx:RustiQParser.PrimMatchContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#PrimParen.
    def visitPrimParen(self, ctx:RustiQParser.PrimParenContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#PrimBloque.
    def visitPrimBloque(self, ctx:RustiQParser.PrimBloqueContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#literalTupla.
    def visitLiteralTupla(self, ctx:RustiQParser.LiteralTuplaContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#literalArray.
    def visitLiteralArray(self, ctx:RustiQParser.LiteralArrayContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#literalStruct.
    def visitLiteralStruct(self, ctx:RustiQParser.LiteralStructContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#inicCampo.
    def visitInicCampo(self, ctx:RustiQParser.InicCampoContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#valorEnum.
    def visitValorEnum(self, ctx:RustiQParser.ValorEnumContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#LitEntero.
    def visitLitEntero(self, ctx:RustiQParser.LitEnteroContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#LitFlotante.
    def visitLitFlotante(self, ctx:RustiQParser.LitFlotanteContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#LitBooleano.
    def visitLitBooleano(self, ctx:RustiQParser.LitBooleanoContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#LitChar.
    def visitLitChar(self, ctx:RustiQParser.LitCharContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#LitTexto.
    def visitLitTexto(self, ctx:RustiQParser.LitTextoContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#expresionMatch.
    def visitExpresionMatch(self, ctx:RustiQParser.ExpresionMatchContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#brazoMatch.
    def visitBrazoMatch(self, ctx:RustiQParser.BrazoMatchContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#PatComodin.
    def visitPatComodin(self, ctx:RustiQParser.PatComodinContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#PatLiteral.
    def visitPatLiteral(self, ctx:RustiQParser.PatLiteralContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#PatIdent.
    def visitPatIdent(self, ctx:RustiQParser.PatIdentContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#PatVariante.
    def visitPatVariante(self, ctx:RustiQParser.PatVarianteContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#PatTupla.
    def visitPatTupla(self, ctx:RustiQParser.PatTuplaContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#listaPatrones.
    def visitListaPatrones(self, ctx:RustiQParser.ListaPatronesContext):
        return self.visitChildren(ctx)



del RustiQParser
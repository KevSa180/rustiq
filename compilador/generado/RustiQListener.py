# Generated from RustiQ.g4 by ANTLR 4.13.2
from antlr4 import *
if "." in __name__:
    from .RustiQParser import RustiQParser
else:
    from RustiQParser import RustiQParser

# This class defines a complete listener for a parse tree produced by RustiQParser.
class RustiQListener(ParseTreeListener):

    # Enter a parse tree produced by RustiQParser#programa.
    def enterPrograma(self, ctx:RustiQParser.ProgramaContext):
        pass

    # Exit a parse tree produced by RustiQParser#programa.
    def exitPrograma(self, ctx:RustiQParser.ProgramaContext):
        pass


    # Enter a parse tree produced by RustiQParser#item.
    def enterItem(self, ctx:RustiQParser.ItemContext):
        pass

    # Exit a parse tree produced by RustiQParser#item.
    def exitItem(self, ctx:RustiQParser.ItemContext):
        pass


    # Enter a parse tree produced by RustiQParser#declFuncion.
    def enterDeclFuncion(self, ctx:RustiQParser.DeclFuncionContext):
        pass

    # Exit a parse tree produced by RustiQParser#declFuncion.
    def exitDeclFuncion(self, ctx:RustiQParser.DeclFuncionContext):
        pass


    # Enter a parse tree produced by RustiQParser#listaParametros.
    def enterListaParametros(self, ctx:RustiQParser.ListaParametrosContext):
        pass

    # Exit a parse tree produced by RustiQParser#listaParametros.
    def exitListaParametros(self, ctx:RustiQParser.ListaParametrosContext):
        pass


    # Enter a parse tree produced by RustiQParser#parametro.
    def enterParametro(self, ctx:RustiQParser.ParametroContext):
        pass

    # Exit a parse tree produced by RustiQParser#parametro.
    def exitParametro(self, ctx:RustiQParser.ParametroContext):
        pass


    # Enter a parse tree produced by RustiQParser#declConst.
    def enterDeclConst(self, ctx:RustiQParser.DeclConstContext):
        pass

    # Exit a parse tree produced by RustiQParser#declConst.
    def exitDeclConst(self, ctx:RustiQParser.DeclConstContext):
        pass


    # Enter a parse tree produced by RustiQParser#declStruct.
    def enterDeclStruct(self, ctx:RustiQParser.DeclStructContext):
        pass

    # Exit a parse tree produced by RustiQParser#declStruct.
    def exitDeclStruct(self, ctx:RustiQParser.DeclStructContext):
        pass


    # Enter a parse tree produced by RustiQParser#declCampo.
    def enterDeclCampo(self, ctx:RustiQParser.DeclCampoContext):
        pass

    # Exit a parse tree produced by RustiQParser#declCampo.
    def exitDeclCampo(self, ctx:RustiQParser.DeclCampoContext):
        pass


    # Enter a parse tree produced by RustiQParser#declEnum.
    def enterDeclEnum(self, ctx:RustiQParser.DeclEnumContext):
        pass

    # Exit a parse tree produced by RustiQParser#declEnum.
    def exitDeclEnum(self, ctx:RustiQParser.DeclEnumContext):
        pass


    # Enter a parse tree produced by RustiQParser#variante.
    def enterVariante(self, ctx:RustiQParser.VarianteContext):
        pass

    # Exit a parse tree produced by RustiQParser#variante.
    def exitVariante(self, ctx:RustiQParser.VarianteContext):
        pass


    # Enter a parse tree produced by RustiQParser#listaTipos.
    def enterListaTipos(self, ctx:RustiQParser.ListaTiposContext):
        pass

    # Exit a parse tree produced by RustiQParser#listaTipos.
    def exitListaTipos(self, ctx:RustiQParser.ListaTiposContext):
        pass


    # Enter a parse tree produced by RustiQParser#tipo.
    def enterTipo(self, ctx:RustiQParser.TipoContext):
        pass

    # Exit a parse tree produced by RustiQParser#tipo.
    def exitTipo(self, ctx:RustiQParser.TipoContext):
        pass


    # Enter a parse tree produced by RustiQParser#tipoPrimitivo.
    def enterTipoPrimitivo(self, ctx:RustiQParser.TipoPrimitivoContext):
        pass

    # Exit a parse tree produced by RustiQParser#tipoPrimitivo.
    def exitTipoPrimitivo(self, ctx:RustiQParser.TipoPrimitivoContext):
        pass


    # Enter a parse tree produced by RustiQParser#tipoArray.
    def enterTipoArray(self, ctx:RustiQParser.TipoArrayContext):
        pass

    # Exit a parse tree produced by RustiQParser#tipoArray.
    def exitTipoArray(self, ctx:RustiQParser.TipoArrayContext):
        pass


    # Enter a parse tree produced by RustiQParser#tipoTupla.
    def enterTipoTupla(self, ctx:RustiQParser.TipoTuplaContext):
        pass

    # Exit a parse tree produced by RustiQParser#tipoTupla.
    def exitTipoTupla(self, ctx:RustiQParser.TipoTuplaContext):
        pass


    # Enter a parse tree produced by RustiQParser#tipoReferencia.
    def enterTipoReferencia(self, ctx:RustiQParser.TipoReferenciaContext):
        pass

    # Exit a parse tree produced by RustiQParser#tipoReferencia.
    def exitTipoReferencia(self, ctx:RustiQParser.TipoReferenciaContext):
        pass


    # Enter a parse tree produced by RustiQParser#bloque.
    def enterBloque(self, ctx:RustiQParser.BloqueContext):
        pass

    # Exit a parse tree produced by RustiQParser#bloque.
    def exitBloque(self, ctx:RustiQParser.BloqueContext):
        pass


    # Enter a parse tree produced by RustiQParser#sentencia.
    def enterSentencia(self, ctx:RustiQParser.SentenciaContext):
        pass

    # Exit a parse tree produced by RustiQParser#sentencia.
    def exitSentencia(self, ctx:RustiQParser.SentenciaContext):
        pass


    # Enter a parse tree produced by RustiQParser#declLet.
    def enterDeclLet(self, ctx:RustiQParser.DeclLetContext):
        pass

    # Exit a parse tree produced by RustiQParser#declLet.
    def exitDeclLet(self, ctx:RustiQParser.DeclLetContext):
        pass


    # Enter a parse tree produced by RustiQParser#declConstLocal.
    def enterDeclConstLocal(self, ctx:RustiQParser.DeclConstLocalContext):
        pass

    # Exit a parse tree produced by RustiQParser#declConstLocal.
    def exitDeclConstLocal(self, ctx:RustiQParser.DeclConstLocalContext):
        pass


    # Enter a parse tree produced by RustiQParser#asignacion.
    def enterAsignacion(self, ctx:RustiQParser.AsignacionContext):
        pass

    # Exit a parse tree produced by RustiQParser#asignacion.
    def exitAsignacion(self, ctx:RustiQParser.AsignacionContext):
        pass


    # Enter a parse tree produced by RustiQParser#opAsignacion.
    def enterOpAsignacion(self, ctx:RustiQParser.OpAsignacionContext):
        pass

    # Exit a parse tree produced by RustiQParser#opAsignacion.
    def exitOpAsignacion(self, ctx:RustiQParser.OpAsignacionContext):
        pass


    # Enter a parse tree produced by RustiQParser#lugar.
    def enterLugar(self, ctx:RustiQParser.LugarContext):
        pass

    # Exit a parse tree produced by RustiQParser#lugar.
    def exitLugar(self, ctx:RustiQParser.LugarContext):
        pass


    # Enter a parse tree produced by RustiQParser#sentenciaReturn.
    def enterSentenciaReturn(self, ctx:RustiQParser.SentenciaReturnContext):
        pass

    # Exit a parse tree produced by RustiQParser#sentenciaReturn.
    def exitSentenciaReturn(self, ctx:RustiQParser.SentenciaReturnContext):
        pass


    # Enter a parse tree produced by RustiQParser#sentenciaBreak.
    def enterSentenciaBreak(self, ctx:RustiQParser.SentenciaBreakContext):
        pass

    # Exit a parse tree produced by RustiQParser#sentenciaBreak.
    def exitSentenciaBreak(self, ctx:RustiQParser.SentenciaBreakContext):
        pass


    # Enter a parse tree produced by RustiQParser#sentenciaContinue.
    def enterSentenciaContinue(self, ctx:RustiQParser.SentenciaContinueContext):
        pass

    # Exit a parse tree produced by RustiQParser#sentenciaContinue.
    def exitSentenciaContinue(self, ctx:RustiQParser.SentenciaContinueContext):
        pass


    # Enter a parse tree produced by RustiQParser#sentenciaWhile.
    def enterSentenciaWhile(self, ctx:RustiQParser.SentenciaWhileContext):
        pass

    # Exit a parse tree produced by RustiQParser#sentenciaWhile.
    def exitSentenciaWhile(self, ctx:RustiQParser.SentenciaWhileContext):
        pass


    # Enter a parse tree produced by RustiQParser#sentenciaLoop.
    def enterSentenciaLoop(self, ctx:RustiQParser.SentenciaLoopContext):
        pass

    # Exit a parse tree produced by RustiQParser#sentenciaLoop.
    def exitSentenciaLoop(self, ctx:RustiQParser.SentenciaLoopContext):
        pass


    # Enter a parse tree produced by RustiQParser#sentenciaIf.
    def enterSentenciaIf(self, ctx:RustiQParser.SentenciaIfContext):
        pass

    # Exit a parse tree produced by RustiQParser#sentenciaIf.
    def exitSentenciaIf(self, ctx:RustiQParser.SentenciaIfContext):
        pass


    # Enter a parse tree produced by RustiQParser#expresion.
    def enterExpresion(self, ctx:RustiQParser.ExpresionContext):
        pass

    # Exit a parse tree produced by RustiQParser#expresion.
    def exitExpresion(self, ctx:RustiQParser.ExpresionContext):
        pass


    # Enter a parse tree produced by RustiQParser#disyuncion.
    def enterDisyuncion(self, ctx:RustiQParser.DisyuncionContext):
        pass

    # Exit a parse tree produced by RustiQParser#disyuncion.
    def exitDisyuncion(self, ctx:RustiQParser.DisyuncionContext):
        pass


    # Enter a parse tree produced by RustiQParser#conjuncion.
    def enterConjuncion(self, ctx:RustiQParser.ConjuncionContext):
        pass

    # Exit a parse tree produced by RustiQParser#conjuncion.
    def exitConjuncion(self, ctx:RustiQParser.ConjuncionContext):
        pass


    # Enter a parse tree produced by RustiQParser#comparacion.
    def enterComparacion(self, ctx:RustiQParser.ComparacionContext):
        pass

    # Exit a parse tree produced by RustiQParser#comparacion.
    def exitComparacion(self, ctx:RustiQParser.ComparacionContext):
        pass


    # Enter a parse tree produced by RustiQParser#opRelacional.
    def enterOpRelacional(self, ctx:RustiQParser.OpRelacionalContext):
        pass

    # Exit a parse tree produced by RustiQParser#opRelacional.
    def exitOpRelacional(self, ctx:RustiQParser.OpRelacionalContext):
        pass


    # Enter a parse tree produced by RustiQParser#suma.
    def enterSuma(self, ctx:RustiQParser.SumaContext):
        pass

    # Exit a parse tree produced by RustiQParser#suma.
    def exitSuma(self, ctx:RustiQParser.SumaContext):
        pass


    # Enter a parse tree produced by RustiQParser#producto.
    def enterProducto(self, ctx:RustiQParser.ProductoContext):
        pass

    # Exit a parse tree produced by RustiQParser#producto.
    def exitProducto(self, ctx:RustiQParser.ProductoContext):
        pass


    # Enter a parse tree produced by RustiQParser#unario.
    def enterUnario(self, ctx:RustiQParser.UnarioContext):
        pass

    # Exit a parse tree produced by RustiQParser#unario.
    def exitUnario(self, ctx:RustiQParser.UnarioContext):
        pass


    # Enter a parse tree produced by RustiQParser#postfijo.
    def enterPostfijo(self, ctx:RustiQParser.PostfijoContext):
        pass

    # Exit a parse tree produced by RustiQParser#postfijo.
    def exitPostfijo(self, ctx:RustiQParser.PostfijoContext):
        pass


    # Enter a parse tree produced by RustiQParser#sufijoLlamada.
    def enterSufijoLlamada(self, ctx:RustiQParser.SufijoLlamadaContext):
        pass

    # Exit a parse tree produced by RustiQParser#sufijoLlamada.
    def exitSufijoLlamada(self, ctx:RustiQParser.SufijoLlamadaContext):
        pass


    # Enter a parse tree produced by RustiQParser#listaArgumentos.
    def enterListaArgumentos(self, ctx:RustiQParser.ListaArgumentosContext):
        pass

    # Exit a parse tree produced by RustiQParser#listaArgumentos.
    def exitListaArgumentos(self, ctx:RustiQParser.ListaArgumentosContext):
        pass


    # Enter a parse tree produced by RustiQParser#sufijoCampo.
    def enterSufijoCampo(self, ctx:RustiQParser.SufijoCampoContext):
        pass

    # Exit a parse tree produced by RustiQParser#sufijoCampo.
    def exitSufijoCampo(self, ctx:RustiQParser.SufijoCampoContext):
        pass


    # Enter a parse tree produced by RustiQParser#sufijoIndice.
    def enterSufijoIndice(self, ctx:RustiQParser.SufijoIndiceContext):
        pass

    # Exit a parse tree produced by RustiQParser#sufijoIndice.
    def exitSufijoIndice(self, ctx:RustiQParser.SufijoIndiceContext):
        pass


    # Enter a parse tree produced by RustiQParser#primario.
    def enterPrimario(self, ctx:RustiQParser.PrimarioContext):
        pass

    # Exit a parse tree produced by RustiQParser#primario.
    def exitPrimario(self, ctx:RustiQParser.PrimarioContext):
        pass


    # Enter a parse tree produced by RustiQParser#literalTupla.
    def enterLiteralTupla(self, ctx:RustiQParser.LiteralTuplaContext):
        pass

    # Exit a parse tree produced by RustiQParser#literalTupla.
    def exitLiteralTupla(self, ctx:RustiQParser.LiteralTuplaContext):
        pass


    # Enter a parse tree produced by RustiQParser#literalArray.
    def enterLiteralArray(self, ctx:RustiQParser.LiteralArrayContext):
        pass

    # Exit a parse tree produced by RustiQParser#literalArray.
    def exitLiteralArray(self, ctx:RustiQParser.LiteralArrayContext):
        pass


    # Enter a parse tree produced by RustiQParser#literalStruct.
    def enterLiteralStruct(self, ctx:RustiQParser.LiteralStructContext):
        pass

    # Exit a parse tree produced by RustiQParser#literalStruct.
    def exitLiteralStruct(self, ctx:RustiQParser.LiteralStructContext):
        pass


    # Enter a parse tree produced by RustiQParser#inicCampo.
    def enterInicCampo(self, ctx:RustiQParser.InicCampoContext):
        pass

    # Exit a parse tree produced by RustiQParser#inicCampo.
    def exitInicCampo(self, ctx:RustiQParser.InicCampoContext):
        pass


    # Enter a parse tree produced by RustiQParser#valorEnum.
    def enterValorEnum(self, ctx:RustiQParser.ValorEnumContext):
        pass

    # Exit a parse tree produced by RustiQParser#valorEnum.
    def exitValorEnum(self, ctx:RustiQParser.ValorEnumContext):
        pass


    # Enter a parse tree produced by RustiQParser#literal.
    def enterLiteral(self, ctx:RustiQParser.LiteralContext):
        pass

    # Exit a parse tree produced by RustiQParser#literal.
    def exitLiteral(self, ctx:RustiQParser.LiteralContext):
        pass


    # Enter a parse tree produced by RustiQParser#expresionMatch.
    def enterExpresionMatch(self, ctx:RustiQParser.ExpresionMatchContext):
        pass

    # Exit a parse tree produced by RustiQParser#expresionMatch.
    def exitExpresionMatch(self, ctx:RustiQParser.ExpresionMatchContext):
        pass


    # Enter a parse tree produced by RustiQParser#brazoMatch.
    def enterBrazoMatch(self, ctx:RustiQParser.BrazoMatchContext):
        pass

    # Exit a parse tree produced by RustiQParser#brazoMatch.
    def exitBrazoMatch(self, ctx:RustiQParser.BrazoMatchContext):
        pass


    # Enter a parse tree produced by RustiQParser#patron.
    def enterPatron(self, ctx:RustiQParser.PatronContext):
        pass

    # Exit a parse tree produced by RustiQParser#patron.
    def exitPatron(self, ctx:RustiQParser.PatronContext):
        pass


    # Enter a parse tree produced by RustiQParser#listaPatrones.
    def enterListaPatrones(self, ctx:RustiQParser.ListaPatronesContext):
        pass

    # Exit a parse tree produced by RustiQParser#listaPatrones.
    def exitListaPatrones(self, ctx:RustiQParser.ListaPatronesContext):
        pass



del RustiQParser
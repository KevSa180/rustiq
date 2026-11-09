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


    # Enter a parse tree produced by RustiQParser#TipoPrim.
    def enterTipoPrim(self, ctx:RustiQParser.TipoPrimContext):
        pass

    # Exit a parse tree produced by RustiQParser#TipoPrim.
    def exitTipoPrim(self, ctx:RustiQParser.TipoPrimContext):
        pass


    # Enter a parse tree produced by RustiQParser#TipoString.
    def enterTipoString(self, ctx:RustiQParser.TipoStringContext):
        pass

    # Exit a parse tree produced by RustiQParser#TipoString.
    def exitTipoString(self, ctx:RustiQParser.TipoStringContext):
        pass


    # Enter a parse tree produced by RustiQParser#TipoArr.
    def enterTipoArr(self, ctx:RustiQParser.TipoArrContext):
        pass

    # Exit a parse tree produced by RustiQParser#TipoArr.
    def exitTipoArr(self, ctx:RustiQParser.TipoArrContext):
        pass


    # Enter a parse tree produced by RustiQParser#TipoTup.
    def enterTipoTup(self, ctx:RustiQParser.TipoTupContext):
        pass

    # Exit a parse tree produced by RustiQParser#TipoTup.
    def exitTipoTup(self, ctx:RustiQParser.TipoTupContext):
        pass


    # Enter a parse tree produced by RustiQParser#TipoRef.
    def enterTipoRef(self, ctx:RustiQParser.TipoRefContext):
        pass

    # Exit a parse tree produced by RustiQParser#TipoRef.
    def exitTipoRef(self, ctx:RustiQParser.TipoRefContext):
        pass


    # Enter a parse tree produced by RustiQParser#TipoNombre.
    def enterTipoNombre(self, ctx:RustiQParser.TipoNombreContext):
        pass

    # Exit a parse tree produced by RustiQParser#TipoNombre.
    def exitTipoNombre(self, ctx:RustiQParser.TipoNombreContext):
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


    # Enter a parse tree produced by RustiQParser#UnarioNegativo.
    def enterUnarioNegativo(self, ctx:RustiQParser.UnarioNegativoContext):
        pass

    # Exit a parse tree produced by RustiQParser#UnarioNegativo.
    def exitUnarioNegativo(self, ctx:RustiQParser.UnarioNegativoContext):
        pass


    # Enter a parse tree produced by RustiQParser#UnarioNegacion.
    def enterUnarioNegacion(self, ctx:RustiQParser.UnarioNegacionContext):
        pass

    # Exit a parse tree produced by RustiQParser#UnarioNegacion.
    def exitUnarioNegacion(self, ctx:RustiQParser.UnarioNegacionContext):
        pass


    # Enter a parse tree produced by RustiQParser#UnarioRefMut.
    def enterUnarioRefMut(self, ctx:RustiQParser.UnarioRefMutContext):
        pass

    # Exit a parse tree produced by RustiQParser#UnarioRefMut.
    def exitUnarioRefMut(self, ctx:RustiQParser.UnarioRefMutContext):
        pass


    # Enter a parse tree produced by RustiQParser#UnarioRef.
    def enterUnarioRef(self, ctx:RustiQParser.UnarioRefContext):
        pass

    # Exit a parse tree produced by RustiQParser#UnarioRef.
    def exitUnarioRef(self, ctx:RustiQParser.UnarioRefContext):
        pass


    # Enter a parse tree produced by RustiQParser#UnarioDeref.
    def enterUnarioDeref(self, ctx:RustiQParser.UnarioDerefContext):
        pass

    # Exit a parse tree produced by RustiQParser#UnarioDeref.
    def exitUnarioDeref(self, ctx:RustiQParser.UnarioDerefContext):
        pass


    # Enter a parse tree produced by RustiQParser#UnarioPostfijo.
    def enterUnarioPostfijo(self, ctx:RustiQParser.UnarioPostfijoContext):
        pass

    # Exit a parse tree produced by RustiQParser#UnarioPostfijo.
    def exitUnarioPostfijo(self, ctx:RustiQParser.UnarioPostfijoContext):
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


    # Enter a parse tree produced by RustiQParser#PrimLiteral.
    def enterPrimLiteral(self, ctx:RustiQParser.PrimLiteralContext):
        pass

    # Exit a parse tree produced by RustiQParser#PrimLiteral.
    def exitPrimLiteral(self, ctx:RustiQParser.PrimLiteralContext):
        pass


    # Enter a parse tree produced by RustiQParser#PrimIdent.
    def enterPrimIdent(self, ctx:RustiQParser.PrimIdentContext):
        pass

    # Exit a parse tree produced by RustiQParser#PrimIdent.
    def exitPrimIdent(self, ctx:RustiQParser.PrimIdentContext):
        pass


    # Enter a parse tree produced by RustiQParser#PrimTupla.
    def enterPrimTupla(self, ctx:RustiQParser.PrimTuplaContext):
        pass

    # Exit a parse tree produced by RustiQParser#PrimTupla.
    def exitPrimTupla(self, ctx:RustiQParser.PrimTuplaContext):
        pass


    # Enter a parse tree produced by RustiQParser#PrimArray.
    def enterPrimArray(self, ctx:RustiQParser.PrimArrayContext):
        pass

    # Exit a parse tree produced by RustiQParser#PrimArray.
    def exitPrimArray(self, ctx:RustiQParser.PrimArrayContext):
        pass


    # Enter a parse tree produced by RustiQParser#PrimStruct.
    def enterPrimStruct(self, ctx:RustiQParser.PrimStructContext):
        pass

    # Exit a parse tree produced by RustiQParser#PrimStruct.
    def exitPrimStruct(self, ctx:RustiQParser.PrimStructContext):
        pass


    # Enter a parse tree produced by RustiQParser#PrimEnum.
    def enterPrimEnum(self, ctx:RustiQParser.PrimEnumContext):
        pass

    # Exit a parse tree produced by RustiQParser#PrimEnum.
    def exitPrimEnum(self, ctx:RustiQParser.PrimEnumContext):
        pass


    # Enter a parse tree produced by RustiQParser#PrimMatch.
    def enterPrimMatch(self, ctx:RustiQParser.PrimMatchContext):
        pass

    # Exit a parse tree produced by RustiQParser#PrimMatch.
    def exitPrimMatch(self, ctx:RustiQParser.PrimMatchContext):
        pass


    # Enter a parse tree produced by RustiQParser#PrimParen.
    def enterPrimParen(self, ctx:RustiQParser.PrimParenContext):
        pass

    # Exit a parse tree produced by RustiQParser#PrimParen.
    def exitPrimParen(self, ctx:RustiQParser.PrimParenContext):
        pass


    # Enter a parse tree produced by RustiQParser#PrimBloque.
    def enterPrimBloque(self, ctx:RustiQParser.PrimBloqueContext):
        pass

    # Exit a parse tree produced by RustiQParser#PrimBloque.
    def exitPrimBloque(self, ctx:RustiQParser.PrimBloqueContext):
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


    # Enter a parse tree produced by RustiQParser#LitEntero.
    def enterLitEntero(self, ctx:RustiQParser.LitEnteroContext):
        pass

    # Exit a parse tree produced by RustiQParser#LitEntero.
    def exitLitEntero(self, ctx:RustiQParser.LitEnteroContext):
        pass


    # Enter a parse tree produced by RustiQParser#LitFlotante.
    def enterLitFlotante(self, ctx:RustiQParser.LitFlotanteContext):
        pass

    # Exit a parse tree produced by RustiQParser#LitFlotante.
    def exitLitFlotante(self, ctx:RustiQParser.LitFlotanteContext):
        pass


    # Enter a parse tree produced by RustiQParser#LitBooleano.
    def enterLitBooleano(self, ctx:RustiQParser.LitBooleanoContext):
        pass

    # Exit a parse tree produced by RustiQParser#LitBooleano.
    def exitLitBooleano(self, ctx:RustiQParser.LitBooleanoContext):
        pass


    # Enter a parse tree produced by RustiQParser#LitChar.
    def enterLitChar(self, ctx:RustiQParser.LitCharContext):
        pass

    # Exit a parse tree produced by RustiQParser#LitChar.
    def exitLitChar(self, ctx:RustiQParser.LitCharContext):
        pass


    # Enter a parse tree produced by RustiQParser#LitTexto.
    def enterLitTexto(self, ctx:RustiQParser.LitTextoContext):
        pass

    # Exit a parse tree produced by RustiQParser#LitTexto.
    def exitLitTexto(self, ctx:RustiQParser.LitTextoContext):
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


    # Enter a parse tree produced by RustiQParser#PatComodin.
    def enterPatComodin(self, ctx:RustiQParser.PatComodinContext):
        pass

    # Exit a parse tree produced by RustiQParser#PatComodin.
    def exitPatComodin(self, ctx:RustiQParser.PatComodinContext):
        pass


    # Enter a parse tree produced by RustiQParser#PatLiteral.
    def enterPatLiteral(self, ctx:RustiQParser.PatLiteralContext):
        pass

    # Exit a parse tree produced by RustiQParser#PatLiteral.
    def exitPatLiteral(self, ctx:RustiQParser.PatLiteralContext):
        pass


    # Enter a parse tree produced by RustiQParser#PatIdent.
    def enterPatIdent(self, ctx:RustiQParser.PatIdentContext):
        pass

    # Exit a parse tree produced by RustiQParser#PatIdent.
    def exitPatIdent(self, ctx:RustiQParser.PatIdentContext):
        pass


    # Enter a parse tree produced by RustiQParser#PatVariante.
    def enterPatVariante(self, ctx:RustiQParser.PatVarianteContext):
        pass

    # Exit a parse tree produced by RustiQParser#PatVariante.
    def exitPatVariante(self, ctx:RustiQParser.PatVarianteContext):
        pass


    # Enter a parse tree produced by RustiQParser#PatTupla.
    def enterPatTupla(self, ctx:RustiQParser.PatTuplaContext):
        pass

    # Exit a parse tree produced by RustiQParser#PatTupla.
    def exitPatTupla(self, ctx:RustiQParser.PatTuplaContext):
        pass


    # Enter a parse tree produced by RustiQParser#listaPatrones.
    def enterListaPatrones(self, ctx:RustiQParser.ListaPatronesContext):
        pass

    # Exit a parse tree produced by RustiQParser#listaPatrones.
    def exitListaPatrones(self, ctx:RustiQParser.ListaPatronesContext):
        pass



del RustiQParser
grammar RustiQ;

// =====================================================
//  PARTE 1: ESTRUCTURA DEL PROGRAMA (reglas del parser)
// =====================================================

programa : item* EOF ;

item : declFuncion
     | declStruct
     | declEnum
     | declConst
     ;

declFuncion : FN ID LPAREN listaParametros? RPAREN (ARROW tipo)? bloque ;
listaParametros : parametro (COMMA parametro)* COMMA? ;
parametro : MUT? ID COLON tipo ;

declConst : CONST ID COLON tipo ASSIGN expresion SEMI ;

declStruct : STRUCT ID LBRACE (declCampo (COMMA declCampo)* COMMA?)? RBRACE ;
declCampo  : ID COLON tipo ;

declEnum : ENUM ID LBRACE variante (COMMA variante)* COMMA? RBRACE ;
variante : ID (LPAREN listaTipos RPAREN)? ;
listaTipos : tipo (COMMA tipo)* COMMA? ;

// =====================================================
//  PARTE 2: TIPOS
// =====================================================

tipo : tipoPrimitivo
     | STRING_T
     | tipoArray
     | tipoTupla
     | tipoReferencia
     | ID
     ;

tipoPrimitivo  : I32 | F64 | BOOL | CHAR_T ;
tipoArray      : LBRACK tipo SEMI INT_LIT RBRACK ;
tipoTupla      : LPAREN tipo COMMA tipo (COMMA tipo)* COMMA? RPAREN ;
tipoReferencia : AMP MUT? tipo ;

// =====================================================
//  PARTE 3: BLOQUES Y SENTENCIAS
// =====================================================

bloque : LBRACE sentencia* expresion? RBRACE ;

sentencia : declLet
          | declConstLocal
          | asignacion SEMI
          | expresion SEMI
          | sentenciaReturn
          | sentenciaBreak
          | sentenciaContinue
          | sentenciaWhile
          | sentenciaLoop
          | sentenciaIf
          | bloque
          ;

declLet        : LET MUT? ID (COLON tipo)? (ASSIGN expresion)? SEMI ;
declConstLocal : CONST ID COLON tipo ASSIGN expresion SEMI ;

asignacion   : lugar opAsignacion expresion ;
opAsignacion : ASSIGN | PLUSEQ | MINUSEQ | STAREQ | SLASHEQ ;
lugar        : ID (DOT ID | LBRACK expresion RBRACK)* ;

sentenciaReturn   : RETURN expresion? SEMI ;
sentenciaBreak    : BREAK SEMI ;
sentenciaContinue : CONTINUE SEMI ;
sentenciaWhile    : WHILE expresion bloque ;
sentenciaLoop     : LOOP bloque ;
sentenciaIf       : IF expresion bloque (ELSE (bloque | sentenciaIf))? ;

// =====================================================
//  PARTE 4: EXPRESIONES (de menor a mayor precedencia)
// =====================================================

expresion      : disyuncion ;
disyuncion     : conjuncion (OROR conjuncion)* ;
conjuncion     : comparacion (ANDAND comparacion)* ;
comparacion    : suma (opRelacional suma)? ;
opRelacional   : EQEQ | NEQ | LT | LE | GT | GE ;
suma           : producto ((PLUS | MINUS) producto)* ;
producto       : unario ((STAR | SLASH | PERCENT) unario)* ;
unario         : (MINUS | NOT | AMP MUT? | STAR) unario
               | postfijo
               ;
postfijo       : primario (sufijoLlamada | sufijoCampo | sufijoIndice)* ;

sufijoLlamada  : LPAREN listaArgumentos? RPAREN ;
listaArgumentos: expresion (COMMA expresion)* COMMA? ;
sufijoCampo    : DOT ID ;
sufijoIndice   : LBRACK expresion RBRACK ;

primario : literal
         | ID
         | literalTupla
         | literalArray
         | literalStruct
         | valorEnum
         | expresionMatch
         | LPAREN expresion RPAREN
         | bloque
         ;

literalTupla  : LPAREN expresion COMMA expresion (COMMA expresion)* COMMA? RPAREN ;
literalArray  : LBRACK expresion (COMMA expresion)* COMMA? RBRACK ;
literalStruct : ID LBRACE (inicCampo (COMMA inicCampo)* COMMA?)? RBRACE ;
inicCampo     : ID COLON expresion ;
valorEnum     : ID COLONCOL ID (LPAREN listaArgumentos RPAREN)? ;

literal : INT_LIT | FLOAT_LIT | TRUE | FALSE | CHAR_LIT | STRING_LIT ;

// =====================================================
//  PARTE 5: MATCH Y PATRONES
// =====================================================

expresionMatch : MATCH expresion LBRACE brazoMatch (COMMA brazoMatch)* COMMA? RBRACE ;
brazoMatch     : patron FATARROW expresion ;

patron : UNDERSCORE
       | literal
       | ID
       | ID COLONCOL ID (LPAREN listaPatrones RPAREN)?
       | LPAREN patron COMMA patron (COMMA patron)* COMMA? RPAREN
       ;
listaPatrones : patron (COMMA patron)* COMMA? ;

// =====================================================
//  PARTE 6: TOKENS (piezas básicas)
// =====================================================

// ===== PALABRAS CLAVE =====
FN       : 'fn' ;
LET      : 'let' ;
MUT      : 'mut' ;
CONST    : 'const' ;
STRUCT   : 'struct' ;
ENUM     : 'enum' ;
IF       : 'if' ;
ELSE     : 'else' ;
WHILE    : 'while' ;
LOOP     : 'loop' ;
BREAK    : 'break' ;
CONTINUE : 'continue' ;
RETURN   : 'return' ;
MATCH    : 'match' ;
TRUE     : 'true' ;
FALSE    : 'false' ;

// ===== TIPOS =====
I32      : 'i32' ;
F64      : 'f64' ;
BOOL     : 'bool' ;
CHAR_T   : 'char' ;
STRING_T : 'String' ;

// ===== OPERADORES Y SÍMBOLOS =====
ARROW    : '->' ;
FATARROW : '=>' ;
COLONCOL : '::' ;
EQEQ     : '==' ;
NEQ      : '!=' ;
LE       : '<=' ;
GE       : '>=' ;
ANDAND   : '&&' ;
OROR     : '||' ;
PLUSEQ   : '+=' ;
MINUSEQ  : '-=' ;
STAREQ   : '*=' ;
SLASHEQ  : '/=' ;
ASSIGN   : '=' ;
LT       : '<' ;
GT       : '>' ;
PLUS     : '+' ;
MINUS    : '-' ;
STAR     : '*' ;
SLASH    : '/' ;
PERCENT  : '%' ;
NOT      : '!' ;
AMP      : '&' ;
DOT      : '.' ;
COMMA    : ',' ;
SEMI     : ';' ;
COLON    : ':' ;
LPAREN   : '(' ;
RPAREN   : ')' ;
LBRACE   : '{' ;
RBRACE   : '}' ;
LBRACK   : '[' ;
RBRACK   : ']' ;

// ===== LITERALES =====
FLOAT_LIT  : [0-9]+ '.' [0-9]+ ;
INT_LIT    : [0-9]+ ;
CHAR_LIT   : '\'' ( ~['\\\r\n] | ESCAPE ) '\'' ;
STRING_LIT : '"' ( ~["\\\r\n] | ESCAPE )* '"' ;
fragment ESCAPE : '\\' [\\nrt"'] ;

// ===== IDENTIFICADORES =====
UNDERSCORE : '_' ;
ID         : [a-zA-Z_] [a-zA-Z_0-9]* ;

// ===== COMENTARIOS Y ESPACIOS (se ignoran) =====
LINE_COMMENT  : '//' ~[\r\n]* -> skip ;
BLOCK_COMMENT : '/*' .*? '*/' -> skip ;
WS            : [ \t\r\n]+ -> skip ;

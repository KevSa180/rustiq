// Resaltado de sintaxis de RustiQ para CodeMirror (solo colores; no analiza nada).
import { StreamLanguage, HighlightStyle, syntaxHighlighting } from "@codemirror/language";
import { tags as t } from "@lezer/highlight";

const PALABRAS = new Set([
  "fn", "let", "mut", "const", "struct", "enum", "if", "else", "while",
  "loop", "break", "continue", "return", "match",
]);
const TIPOS = new Set(["i32", "f64", "bool", "char", "String"]);

const rustiq = StreamLanguage.define({
  name: "rustiq",
  startState: () => ({ enComentario: false }),
  token(stream, estado) {
    if (estado.enComentario) {
      if (stream.match(/^.*?\*\//)) estado.enComentario = false;
      else stream.skipToEnd();
      return "comment";
    }
    if (stream.eatSpace()) return null;
    if (stream.match("//")) {
      stream.skipToEnd();
      return "comment";
    }
    if (stream.match("/*")) {
      estado.enComentario = true;
      if (stream.match(/^.*?\*\//)) estado.enComentario = false;
      else stream.skipToEnd();
      return "comment";
    }
    if (stream.match(/^"(?:[^"\\]|\\.)*"?/)) return "string";
    if (stream.match(/^'(?:[^'\\]|\\.)'/)) return "string";
    if (stream.match(/^\d+\.\d+/) || stream.match(/^\d+/)) return "number";
    if (stream.match(/^[A-Za-z_]\w*/)) {
      const palabra = stream.current();
      if (PALABRAS.has(palabra)) return "keyword";
      if (palabra === "true" || palabra === "false") return "bool";
      if (TIPOS.has(palabra) || /^[A-Z]/.test(palabra)) return "typeName";
      if (stream.peek() === "(") return "def";
      return "variableName";
    }
    if (stream.match(/^(->|=>|::|==|!=|<=|>=|&&|\|\||[-+*/%=<>!&])/)) return "operator";
    stream.next();
    return null;
  },
  languageData: { commentTokens: { line: "//", block: { open: "/*", close: "*/" } } },
});

const colores = HighlightStyle.define([
  { tag: t.keyword, color: "#ff8f6b", fontWeight: "600" },
  { tag: t.typeName, color: "#7cc7ff" },
  { tag: t.number, color: "#d6b4ff" },
  { tag: t.bool, color: "#d6b4ff" },
  { tag: t.string, color: "#a8d98a" },
  { tag: t.comment, color: "#6f7c8f", fontStyle: "italic" },
  { tag: t.definition(t.variableName), color: "#f5d67a" },
  { tag: t.operator, color: "#c2cad6" },
  { tag: t.variableName, color: "#e6e9ef" },
]);

export const lenguajeRustiQ = [rustiq, syntaxHighlighting(colores)];

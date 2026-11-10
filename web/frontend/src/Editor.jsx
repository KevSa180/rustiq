// Editor de código: CodeMirror con números de línea, resaltado y marcas de error.
import { forwardRef, useEffect, useImperativeHandle, useRef } from "react";
import { EditorState } from "@codemirror/state";
import {
  EditorView, keymap, lineNumbers, highlightActiveLine, highlightActiveLineGutter, drawSelection,
} from "@codemirror/view";
import { defaultKeymap, history, historyKeymap, indentWithTab } from "@codemirror/commands";
import { bracketMatching, indentOnInput } from "@codemirror/language";
import { lintGutter, setDiagnostics } from "@codemirror/lint";
import { lenguajeRustiQ } from "./lenguaje.js";

const tema = EditorView.theme(
  {
    "&": { height: "100%", fontSize: "14px", backgroundColor: "var(--fondo-editor)" },
    ".cm-scroller": { fontFamily: "var(--mono)", lineHeight: "1.6" },
    ".cm-content": { caretColor: "#ff8f6b", padding: "12px 0" },
    ".cm-gutters": {
      backgroundColor: "var(--fondo-editor)", color: "#4f5b6b", border: "none",
      borderRight: "1px solid var(--borde)",
    },
    ".cm-activeLine": { backgroundColor: "rgba(255,255,255,0.035)" },
    ".cm-activeLineGutter": { backgroundColor: "transparent", color: "#9aa5b4" },
    ".cm-selectionBackground, &.cm-focused .cm-selectionBackground": {
      backgroundColor: "rgba(124,199,255,0.22) !important",
    },
    ".cm-cursor": { borderLeftColor: "#ff8f6b", borderLeftWidth: "2px" },
    ".cm-lintRange-error": {
      backgroundImage: "none", textDecoration: "underline wavy #ff5d5d", textUnderlineOffset: "4px",
    },
    ".cm-tooltip": { backgroundColor: "#1c2230", border: "1px solid var(--borde)", color: "#e6e9ef" },
  },
  { dark: true }
);

/** Convierte (línea, columna) que vienen del compilador (desde 1) a un rango del documento. */
function rangoDeError(doc, linea, columna) {
  const numero = Math.min(Math.max(linea, 1), doc.lines);
  const l = doc.line(numero);
  const desde = Math.min(l.from + Math.max(columna - 1, 0), l.to);
  const resto = doc.sliceString(desde, l.to);
  const palabra = resto.match(/^[A-Za-z_]\w*|^\d+(\.\d+)?|^"[^"]*"?|^\S/);
  const hasta = Math.min(desde + (palabra ? palabra[0].length : 0), l.to);
  return { desde, hasta: hasta > desde ? hasta : Math.min(desde + 1, l.to) };
}

const Editor = forwardRef(function Editor({ valorInicial, alCambiar, alAtajo }, ref) {
  const contenedor = useRef(null);
  const vista = useRef(null);
  const callbacks = useRef({ alCambiar, alAtajo });
  callbacks.current = { alCambiar, alAtajo };

  useEffect(() => {
    const estado = EditorState.create({
      doc: valorInicial,
      extensions: [
        lineNumbers(),
        highlightActiveLineGutter(),
        highlightActiveLine(),
        drawSelection(),
        history(),
        indentOnInput(),
        bracketMatching(),
        lintGutter(),
        lenguajeRustiQ,
        EditorState.tabSize.of(4),
        keymap.of([
          { key: "Mod-Enter", run: () => { callbacks.current.alAtajo?.(); return true; } },
          indentWithTab,
          ...defaultKeymap,
          ...historyKeymap,
        ]),
        EditorView.updateListener.of((u) => {
          if (u.docChanged) callbacks.current.alCambiar?.(u.state.doc.toString());
        }),
        tema,
      ],
    });
    vista.current = new EditorView({ state: estado, parent: contenedor.current });
    return () => vista.current.destroy();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useImperativeHandle(ref, () => ({
    obtenerCodigo: () => vista.current.state.doc.toString(),
    ponerCodigo(texto) {
      const v = vista.current;
      v.dispatch({ changes: { from: 0, to: v.state.doc.length, insert: texto } });
    },
    marcarErrores(errores) {
      const v = vista.current;
      const diagnosticos = errores.map((e) => {
        const { desde, hasta } = rangoDeError(v.state.doc, e.linea, e.columna);
        return { from: desde, to: hasta, severity: "error", message: `[${e.fase}] ${e.mensaje}` };
      });
      v.dispatch(setDiagnostics(v.state, diagnosticos));
    },
    irA(linea, columna) {
      const v = vista.current;
      const { desde } = rangoDeError(v.state.doc, linea, columna);
      v.dispatch({ selection: { anchor: desde }, scrollIntoView: true });
      v.focus();
    },
  }));

  return <div className="editor" ref={contenedor} />;
});

export default Editor;

import { useEffect, useRef, useState } from "react";
import Editor from "./Editor.jsx";

const LIMITE_MS = 5000;          // tiempo máximo de ejecución
const LIMITE_LINEAS = 5000;      // líneas de salida que se muestran

const CODIGO_INICIAL = `// Bienvenido a RustiQ: escribe tu programa y pulsa Compilar.
fn doble(x: i32) -> i32 {
    x * 2
}

fn main() {
    print_str("Hola desde WebAssembly");
    print_i32(doble(21));
}
`;

const NOMBRE_FASE = {
  léxico: "Léxico",
  sintáctico: "Sintáctico",
  semántico: "Semántico",
  generación: "Generación",
  wasm: "Wasm",
  interno: "Interno",
  servidor: "Servidor",
  conexión: "Conexión",
};

function base64ABytes(texto) {
  const binario = atob(texto);
  const bytes = new Uint8Array(binario.length);
  for (let i = 0; i < binario.length; i++) bytes[i] = binario.charCodeAt(i);
  return bytes;
}

export default function App() {
  const editor = useRef(null);
  const trabajador = useRef(null);
  const reloj = useRef(null);
  const entradaArchivo = useRef(null);

  const [ejemplos, setEjemplos] = useState([]);
  const [compilacion, setCompilacion] = useState(null);   // { ok, bytes, wat, tamano }
  const [vigente, setVigente] = useState(false);          // ¿el .wasm corresponde al código actual?
  const [mensajes, setMensajes] = useState([
    { tipo: "info", texto: "Escribe o carga un programa y pulsa Compilar (⌘/Ctrl + Enter compila y ejecuta)." },
  ]);
  const [salida, setSalida] = useState([]);
  const [estadoEjecucion, setEstadoEjecucion] = useState(null); // null | corriendo | {ok, texto}
  const [pestana, setPestana] = useState("salida");
  const [compilando, setCompilando] = useState(false);
  const [nombreArchivo, setNombreArchivo] = useState("programa.rq");

  useEffect(() => {
    fetch("/api/ejemplos")
      .then((r) => (r.ok ? r.json() : []))
      .then(setEjemplos)
      .catch(() => setEjemplos([]));
    return () => detenerEjecucion();
  }, []);

  function alCambiarCodigo() {
    setVigente(false);
  }

  function cargarCodigo(codigo, nombre) {
    editor.current.ponerCodigo(codigo);
    editor.current.marcarErrores([]);
    setNombreArchivo(nombre);
    setCompilacion(null);
    setSalida([]);
    setEstadoEjecucion(null);
    setMensajes([{ tipo: "info", texto: `Cargado ${nombre}. Pulsa Compilar.` }]);
  }

  function abrirArchivo(evento) {
    const archivo = evento.target.files[0];
    if (!archivo) return;
    const lector = new FileReader();
    lector.onload = () => cargarCodigo(String(lector.result), archivo.name);
    lector.readAsText(archivo);
    evento.target.value = "";
  }

  async function compilar() {
    const codigo = editor.current.obtenerCodigo();
    setCompilando(true);
    setCompilacion(null);
    setVigente(false);
    let respuesta;
    try {
      const r = await fetch("/api/compilar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ codigo }),
      });
      respuesta = await r.json();
    } catch {
      // Nunca se presenta como éxito una compilación que no llegó al servidor.
      setCompilando(false);
      editor.current.marcarErrores([]);
      setMensajes([{
        tipo: "error", fase: "conexión",
        texto: "No se pudo conectar con el compilador. ¿Está corriendo python web/server.py?",
      }]);
      return null;
    }
    setCompilando(false);

    if (!respuesta.ok) {
      const errores = respuesta.errores || [];
      editor.current.marcarErrores(errores);
      setMensajes(errores.map((e) => ({
        tipo: "error", fase: e.fase, linea: e.linea, columna: e.columna, texto: e.mensaje,
      })));
      if (respuesta.wat) setCompilacion({ ok: false, wat: respuesta.wat });
      return null;
    }

    const resultado = {
      ok: true, bytes: base64ABytes(respuesta.wasm), wat: respuesta.wat, tamano: respuesta.bytes,
    };
    editor.current.marcarErrores([]);
    setCompilacion(resultado);
    setVigente(true);
    setMensajes([{
      tipo: "ok",
      texto: `Compilación exitosa: módulo .wasm válido de ${resultado.tamano} bytes.`,
    }]);
    return resultado;
  }

  function detenerEjecucion() {
    clearTimeout(reloj.current);
    trabajador.current?.terminate();
    trabajador.current = null;
  }

  function ejecutar(resultado = compilacion) {
    if (!resultado?.ok) return;
    detenerEjecucion();
    setPestana("salida");
    setSalida([]);
    setEstadoEjecucion("corriendo");

    const w = new Worker(new URL("./ejecutor.worker.js", import.meta.url), { type: "module" });
    trabajador.current = w;
    w.onmessage = ({ data }) => {
      if (data.tipo === "salida") {
        setSalida((anterior) => [...anterior, ...data.lineas].slice(0, LIMITE_LINEAS));
      } else {
        detenerEjecucion();
        setEstadoEjecucion(data.tipo === "fin"
          ? { ok: true, texto: `Ejecución terminada en ${data.ms.toFixed(1)} ms` }
          : { ok: false, texto: `Error en ejecución: ${data.mensaje}` });
      }
    };
    reloj.current = setTimeout(() => {
      detenerEjecucion();
      setEstadoEjecucion({ ok: false, texto: `Se detuvo tras ${LIMITE_MS / 1000} s (¿un bucle infinito?)` });
    }, LIMITE_MS);
    // Se envía una copia de los bytes recién compilados.
    w.postMessage({ bytes: resultado.bytes.slice() });
  }

  async function compilarYEjecutar() {
    const resultado = await compilar();
    if (resultado) ejecutar(resultado);
  }

  function descargarWasm() {
    const url = URL.createObjectURL(new Blob([compilacion.bytes], { type: "application/wasm" }));
    const a = document.createElement("a");
    a.href = url;
    a.download = nombreArchivo.replace(/\.\w+$/, "") + ".wasm";
    a.click();
    URL.revokeObjectURL(url);
  }

  const puedeEjecutar = compilacion?.ok && vigente && estadoEjecucion !== "corriendo";
  let estadoBarra = "Sin compilar";
  if (compilando) estadoBarra = "Compilando…";
  else if (compilacion?.ok && vigente) estadoBarra = `✓ Compilado · ${compilacion.tamano} bytes`;
  else if (compilacion?.ok && !vigente) estadoBarra = "Código modificado: vuelve a compilar";
  else if (mensajes.some((m) => m.tipo === "error")) estadoBarra = `✗ ${mensajes.length} error(es)`;

  return (
    <div className="app">
      <header className="cabecera">
        <div className="marca">
          <span className="logo">R<span>Q</span></span>
          <div>
            <h1>RustiQ</h1>
            <p>Compilador a WebAssembly</p>
          </div>
        </div>

        <div className="acciones">
          <select
            className="selector"
            value=""
            onChange={(e) => {
              const ej = ejemplos.find((x) => x.nombre === e.target.value);
              if (ej) cargarCodigo(ej.codigo, ej.nombre);
            }}
          >
            <option value="" disabled>Ejemplos…</option>
            {ejemplos.map((ej) => (
              <option key={ej.nombre} value={ej.nombre}>{ej.nombre}</option>
            ))}
          </select>
          <button className="boton" onClick={() => entradaArchivo.current.click()}>Abrir archivo</button>
          <input ref={entradaArchivo} type="file" accept=".rq,.rs,.txt" hidden onChange={abrirArchivo} />
          <span className="separador" />
          <button className="boton primario" onClick={compilar} disabled={compilando}>
            {compilando ? "Compilando…" : "Compilar"}
          </button>
          <button
            className="boton ejecutar"
            onClick={() => ejecutar()}
            disabled={!puedeEjecutar}
            title={puedeEjecutar ? "Ejecutar el .wasm recién compilado" : "Primero compila el código actual"}
          >
            ▶ Ejecutar
          </button>
        </div>
      </header>

      <main className="cuerpo">
        <section className="panel panel-editor">
          <div className="titulo-panel">
            <span>{nombreArchivo}</span>
            <span className={`estado ${vigente && compilacion?.ok ? "bien" : ""}`}>{estadoBarra}</span>
          </div>
          <Editor
            ref={editor}
            valorInicial={CODIGO_INICIAL}
            alCambiar={alCambiarCodigo}
            alAtajo={compilarYEjecutar}
          />
        </section>

        <aside className="columna">
          <section className="panel panel-mensajes">
            <div className="titulo-panel"><span>Mensajes</span></div>
            <ul className="mensajes">
              {mensajes.map((m, i) => (
                <li
                  key={i}
                  className={`mensaje ${m.tipo} ${m.linea ? "clicable" : ""}`}
                  onClick={() => m.linea && editor.current.irA(m.linea, m.columna)}
                >
                  {m.fase && <span className="fase">{NOMBRE_FASE[m.fase] || m.fase}</span>}
                  {m.linea && <span className="posicion">línea {m.linea}, col {m.columna}</span>}
                  <span className="texto">{m.texto}</span>
                </li>
              ))}
            </ul>
          </section>

          <section className="panel panel-salida">
            <div className="titulo-panel pestanas">
              <button className={pestana === "salida" ? "activa" : ""} onClick={() => setPestana("salida")}>
                Salida
              </button>
              <button
                className={pestana === "wat" ? "activa" : ""}
                onClick={() => setPestana("wat")}
                disabled={!compilacion?.wat}
              >
                WAT generado
              </button>
              {compilacion?.ok && (
                <button className="enlace" onClick={descargarWasm}>Descargar .wasm</button>
              )}
            </div>
            {pestana === "salida" ? (
              <div className="salida">
                {salida.length === 0 && estadoEjecucion === null && (
                  <div className="vacio">La salida del programa aparecerá aquí.</div>
                )}
                {salida.map((linea, i) => <div key={i} className="linea">{linea || " "}</div>)}
                {salida.length >= LIMITE_LINEAS && (
                  <div className="aviso">… salida recortada a {LIMITE_LINEAS} líneas</div>
                )}
                {estadoEjecucion === "corriendo" && <div className="aviso">Ejecutando…</div>}
                {estadoEjecucion && estadoEjecucion !== "corriendo" && (
                  <div className={`fin ${estadoEjecucion.ok ? "bien" : "mal"}`}>{estadoEjecucion.texto}</div>
                )}
              </div>
            ) : (
              <pre className="wat">{compilacion?.wat}</pre>
            )}
          </section>
        </aside>
      </main>
    </div>
  );
}

// Ejecuta el módulo .wasm en un hilo aparte (Web Worker), para que un bucle
// infinito no congele la página: la página lo puede detener con terminate().
//
// Es el equivalente en el navegador de compilador/ejecutor_wasm.py: le presta
// al módulo las mismas funciones print_* y lee los String desde su memoria.

// Misma regla que formatear_f64 en Python: 4.0 se muestra como "4.0".
function formatearF64(v) {
  return Number.isInteger(v) ? v.toFixed(1) : String(v);
}

// Traduce los "traps" (errores en ejecución) del navegador al español.
function traducirError(e) {
  const m = String(e && e.message ? e.message : e);
  if (/divide by zero|division by zero/i.test(m)) return "División entera por cero";
  if (/unreachable/i.test(m)) return "Índice de array fuera de rango";
  if (/out of bounds/i.test(m)) return "Acceso fuera de la memoria";
  if (/call stack|too much recursion/i.test(m)) return "Recursión demasiado profunda";
  return m;
}

self.onmessage = async ({ data }) => {
  let memoria = null;
  let pendientes = [];
  const enviar = () => {
    if (pendientes.length) {
      self.postMessage({ tipo: "salida", lineas: pendientes });
      pendientes = [];
    }
  };
  // La salida se manda en grupos de 200 líneas para no saturar la página.
  const imprimir = (texto) => {
    pendientes.push(texto);
    if (pendientes.length >= 200) enviar();
  };

  // [DEFENSA] Las funciones que el módulo importa ("env"): igual que en ejecutor_wasm.py.
  const env = {
    print_i32: (v) => imprimir(String(v)),
    print_f64: (v) => imprimir(formatearF64(v)),
    print_bool: (v) => imprimir(v ? "true" : "false"),
    print_char: (v) => imprimir(String.fromCodePoint(v)),
    print_str: (p) => {
      // String en memoria: [ largo (4 bytes) ][ bytes UTF-8 ]
      const largo = new DataView(memoria.buffer).getUint32(p, true);
      imprimir(new TextDecoder().decode(new Uint8Array(memoria.buffer, p + 4, largo)));
    },
  };

  try {
    // [DEFENSA] API WebAssembly del navegador: carga el .wasm recién compilado y llama a main.
    const { instance } = await WebAssembly.instantiate(data.bytes, { env });
    memoria = instance.exports.memory;
    const inicio = performance.now();
    instance.exports.main();
    enviar();
    self.postMessage({ tipo: "fin", ms: performance.now() - inicio });
  } catch (e) {
    enviar();
    self.postMessage({ tipo: "error", mensaje: traducirError(e) });
  }
};

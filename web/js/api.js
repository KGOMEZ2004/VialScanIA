// Cliente de la API de VialScan: token de sesión, errores y utilidades de formato.
const Sesion = {
  clave: "vialscan_sesion",
  leer() {
    try { return JSON.parse(localStorage.getItem(this.clave)) || null; } catch { return null; }
  },
  guardar(datos) {
    try { localStorage.setItem(this.clave, JSON.stringify(datos)); } catch {}
  },
  borrar() {
    try { localStorage.removeItem(this.clave); } catch {}
  },
  get token() { return this.leer()?.token || ""; },
  get usuario() { return this.leer()?.usuario || null; },
  get esAdmin() { return this.usuario?.rol === "admin"; },
};

class ErrorApi extends Error {
  constructor(estado, mensaje) { super(mensaje); this.estado = estado; }
}

async function api(ruta, { metodo = "GET", datos, formulario } = {}) {
  const opciones = { method: metodo, headers: {} };
  if (Sesion.token) opciones.headers.Authorization = `Bearer ${Sesion.token}`;
  if (formulario) opciones.body = formulario;
  else if (datos !== undefined) {
    opciones.headers["Content-Type"] = "application/json";
    opciones.body = JSON.stringify(datos);
  }
  let r;
  try { r = await fetch(ruta, opciones); }
  catch { throw new ErrorApi(0, "No hay conexión con el servidor"); }
  const cuerpo = await r.json().catch(() => ({}));
  if (!r.ok) {
    let msg = cuerpo.detail;
    if (Array.isArray(msg)) msg = msg.map(e => e.msg).join(" · ");
    if (r.status === 401 && ruta !== "/api/auth/login") {
      Sesion.borrar();
      location.hash = "#/login";
    }
    throw new ErrorApi(r.status, msg || `Error ${r.status}`);
  }
  return cuerpo;
}

// ------------------------------------------------------------------ formato
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

const Fmt = {
  tipo: t => ({ bache: "Bache", grieta: "Grieta", hundimiento: "Hundimiento" }[t] || t),
  severidad: s => ({ baja: "Baja", media: "Media", alta: "Alta" }[s] || "Sin asignar"),
  estado: e => ({ pendiente: "Pendiente de validación", validado: "Validado", asignado: "Asignado", reparado: "Reparado" }[e] || e),
  /** Estado de un daño: lo detectado por la IA y aún no revisado se muestra como "Detectado por IA". */
  estadoDano: d => (d.estado === "pendiente" && d.origen === "ia" ? "Detectado por IA" : Fmt.estado(d.estado)),
  estadoRecorrido: e => ({ pendiente: "Pendiente", en_proceso: "En proceso", completado: "Completado" }[e] || e),
  coord(lat, lon) {
    if (lat == null || lon == null) return "—";
    return `${Math.abs(lat).toFixed(4)}° ${lat < 0 ? "S" : "N"}, ${Math.abs(lon).toFixed(4)}° ${lon < 0 ? "W" : "E"}`;
  },
  cm: v => (v == null || v === "" ? "—" : `${+v % 1 ? (+v).toFixed(1) : +v}`),
  pct: v => (v == null ? "" : `${Math.round(v * 100)}%`),
  fecha(iso) {
    if (!iso) return "—";
    const d = new Date(iso);
    return d.toLocaleDateString("es-EC", { day: "2-digit", month: "2-digit", year: "numeric" }) + " · " +
      d.toLocaleTimeString("es-EC", { hour: "2-digit", minute: "2-digit", hour12: false });
  },
  relativa(iso) {
    if (!iso) return "";
    const d = new Date(iso), min = (Date.now() - d) / 60000;
    if (min < 1) return "Ahora";
    if (min < 60) return `Hace ${Math.round(min)} min`;
    if (min < 60 * 24 && d.getDate() === new Date().getDate()) {
      const h = Math.round(min / 60);
      return `Hace ${h} hora${h > 1 ? "s" : ""}`;
    }
    const ayer = new Date(); ayer.setDate(ayer.getDate() - 1);
    if (d.toDateString() === ayer.toDateString()) return "Ayer";
    return d.toLocaleDateString("es-EC", { day: "numeric", month: "short", year: "numeric" }).replace(".", "");
  },
  iniciales: n => (n || "?").replace(/^(Ing|Dr|Arq|Lic)\.?\s+/i, "").split(/\s+/).slice(0, 2).map(p => p[0]).join("").toUpperCase(),
};

const COLOR_SEVERIDAD = { alta: "#e5484d", media: "#f2c230", baja: "#3fb950", null: "#8b8f97" };
const colorSev = s => COLOR_SEVERIDAD[s] || COLOR_SEVERIDAD.null;

// Enlaces de Google Maps (no requieren API key)
const GMaps = {
  coords: d => `${(+d.lat).toFixed(6)},${(+d.lon).toFixed(6)}`,
  abrir: d => `https://www.google.com/maps/search/?api=1&query=${GMaps.coords(d)}`,
  street: d => `https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=${GMaps.coords(d)}`,
  ruta: d => `https://www.google.com/maps/dir/?api=1&destination=${GMaps.coords(d)}`,
  embed: (d, satelite) => `https://www.google.com/maps/embed?origin=mfe&pb=!1m4!2m1!1s${GMaps.coords(d)}!5e${satelite ? 1 : 0}!6i18!3m1!1ses!5m1!1ses`,
};

// VialScan AI — panel de mantenimiento vial (SPA sin dependencias).
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];

const svg = d => `<svg class="ico" viewBox="0 0 24 24">${d}</svg>`;
const ICONO = {
  logo: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="4" y="4" width="16" height="16" rx="3"/><path d="M12 8v8M8 12h8"/></svg>`,
  recorridos: svg('<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>'),
  mapas: svg('<path d="M12 21s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11z"/><circle cx="12" cy="10" r="2.5"/>'),
  reportes: svg('<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5M9 13h6M9 17h6"/>'),
  config: svg('<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/>'),
  chevron: svg('<path d="m9 18 6-6-6-6"/>'),
  atras: svg('<path d="m15 18-6-6 6-6"/>'),
  cerrar: svg('<path d="M18 6 6 18M6 6l12 12"/>'),
  mas: svg('<path d="M12 5v14M5 12h14"/>'),
  doc: svg('<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5M9 13h6M9 17h4"/>'),
  descargar: svg('<path d="M12 4v11M7 10l5 5 5-5M5 20h14"/>'),
  alerta: svg('<path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/><path d="M12 9v4M12 17h.01"/>'),
  basura: svg('<path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6"/>'),
  salir: svg('<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9"/>'),
  subir: svg('<path d="M12 20V9M7 14l5-5 5 5M5 4h14"/>'),
  ia: svg('<rect x="4" y="4" width="16" height="16" rx="2"/><path d="M9 9h6v6H9zM9 1v3M15 1v3M9 20v3M15 20v3M20 9h3M20 14h3M1 9h3M1 14h3"/>'),
};
const MARCA = `<div class="marca"><span class="marca-logo">${ICONO.logo}</span>VialScan AI <span class="insignia">v2.4 PRO</span></div>`;

// ------------------------------------------------------------------ utilidades de interfaz
function avisar(texto, tipo = "info", alClic) {
  const el = document.createElement("div");
  el.className = `aviso ${tipo}`;
  el.innerHTML = texto;
  if (alClic) el.onclick = () => { alClic(); el.remove(); };
  $("#avisos").append(el);
  const todos = $$("#avisos .aviso");
  if (todos.length > 3) todos.slice(0, todos.length - 3).forEach(a => a.remove());
  setTimeout(() => el.remove(), tipo === "alerta" ? 8000 : 4500);
}

function confirmar({ titulo, texto, boton = "Sí, eliminar" }) {
  return new Promise(resolver => {
    const fondo = document.createElement("div");
    fondo.className = "fondo-modal";
    fondo.innerHTML = `<div class="modal confirmar" role="alertdialog" aria-modal="true">
      <div class="icono-alerta">${ICONO.alerta}</div><h3>${titulo}</h3><p>${texto}</p>
      <div class="botones"><button class="btn" data-r="0">Cancelar</button><button class="btn peligro" data-r="1">${boton}</button></div></div>`;
    const cerrar = v => { fondo.remove(); document.removeEventListener("keydown", tecla); resolver(v); };
    const tecla = e => { if (e.key === "Escape") cerrar(false); };
    fondo.addEventListener("click", e => {
      if (e.target === fondo) cerrar(false);
      const b = e.target.closest("[data-r]");
      if (b) cerrar(b.dataset.r === "1");
    });
    document.addEventListener("keydown", tecla);
    document.body.append(fondo);
    $(".btn.peligro", fondo).focus();
  });
}

function modal(html, alMontar) {
  const fondo = document.createElement("div");
  fondo.className = "fondo-modal";
  fondo.innerHTML = `<div class="modal ancho" role="dialog" aria-modal="true">${html}</div>`;
  const cerrar = () => { fondo.remove(); document.removeEventListener("keydown", tecla); };
  const tecla = e => { if (e.key === "Escape") cerrar(); };
  fondo.addEventListener("click", e => { if (e.target === fondo || e.target.closest("[data-cerrar]")) cerrar(); });
  document.addEventListener("keydown", tecla);
  document.body.append(fondo);
  alMontar?.(fondo, cerrar);
}

function distanciaKm(a, b) {
  const rad = x => x * Math.PI / 180, dLat = rad(b.lat - a.lat), dLon = rad(b.lon - a.lon);
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(rad(a.lat)) * Math.cos(rad(b.lat)) * Math.sin(dLon / 2) ** 2;
  return 12742 * Math.asin(Math.sqrt(h));
}

const nombreRecorridoCorto = r => `${esc(r.nombre)} <span class="meta">(${esc(r.codigo)})</span>`;

function subtituloFuente(f) {
  f = f || "";
  if (f === "demo") return "Cámara del vehículo · IA v1.0";
  if (f === "unity-simulado" || f === "unity-vivo") return "Simulador Unity · cámara del vehículo en vivo";
  if (f.startsWith("unity")) return "Simulador Unity · IA YOLO";
  if (f === "camara") return "Cámara del vehículo · IA YOLO";
  if (f === "importado") return "Registros importados de la versión anterior";
  if (f.startsWith("subido")) return `Fotos ${f} · IA YOLO`;
  return f;
}

// ------------------------------------------------------------------ aplicación y rutas
const App = {
  vista: null,
  ws: null,

  iniciar() {
    window.addEventListener("hashchange", () => this.navegar());
    this.navegar();
  },

  ruta() {
    const [camino, q] = (location.hash.slice(1) || "/recorridos").split("?");
    return { partes: camino.split("/").filter(Boolean), params: new URLSearchParams(q || "") };
  },

  navegar() {
    const { partes, params } = this.ruta();
    this.vista?.destruir?.();
    this.vista = null;
    if (!Sesion.token) {
      this.desconectar();
      if (partes[0] !== "login") { location.hash = "#/login"; return; }
      return pantallaLogin();
    }
    if (partes[0] === "login" || !partes[0]) { location.hash = "#/recorridos"; return; }
    this.montarEstructura();
    const seccion = { recorridos: "recorridos", mapas: "mapas", reportes: "reportes", configuracion: "configuracion" }[partes[0]] || "recorridos";
    $$(".nav a").forEach(a => a.classList.toggle("activo", a.dataset.seccion === seccion));
    const cont = $("#contenido");
    cont.innerHTML = "";
    cont.scrollTop = 0;
    if (seccion === "recorridos" && partes[1]) this.vista = new VistaAnalisis(cont, +partes[1], params);
    else if (seccion === "recorridos") this.vista = new VistaRecorridos(cont);
    else if (seccion === "mapas") this.vista = new VistaMapas(cont);
    else if (seccion === "reportes") this.vista = new VistaReportes(cont);
    else this.vista = new VistaConfiguracion(cont);
  },

  montarEstructura() {
    if ($("#contenido")) return;
    const u = Sesion.usuario;
    $("#raiz").innerHTML = `<div class="app">
      <header class="cabecera">${MARCA}
        <button class="usuario" id="btnUsuario" aria-haspopup="menu">
          <div><b>${esc(u.nombre)}</b><small>${esc(u.cargo || "")}</small></div><span class="avatar">${esc(Fmt.iniciales(u.nombre))}</span>
        </button>
      </header>
      <nav class="lateral">
        <div class="nav">
          <a href="#/recorridos" data-seccion="recorridos">${ICONO.recorridos}Recorridos</a>
          <a href="#/mapas" data-seccion="mapas">${ICONO.mapas}Mapas</a>
          <a href="#/reportes" data-seccion="reportes">${ICONO.reportes}Reportes</a>
          <a href="#/configuracion" data-seccion="configuracion">${ICONO.config}Configuración</a>
        </div>
        <div class="estado-servidor" id="estadoServidor"><span class="punto"></span><span>Servidor IA: comprobando…</span></div>
      </nav>
      <main class="contenido" id="contenido"></main>
    </div>`;
    $("#btnUsuario").onclick = e => {
      e.stopPropagation();
      if ($(".menu-usuario")) return $(".menu-usuario").remove();
      const m = document.createElement("div");
      m.className = "menu-usuario";
      m.innerHTML = `<button data-ir="configuracion">${ICONO.config}Mi cuenta</button><button data-salir>${ICONO.salir}Cerrar sesión</button>`;
      m.onclick = ev => {
        if (ev.target.closest("[data-salir]")) cerrarSesion();
        if (ev.target.closest("[data-ir]")) location.hash = "#/configuracion";
        m.remove();
      };
      $(".app").append(m);
      document.addEventListener("click", () => m.remove(), { once: true });
    };
    this.revisarServidor();
    clearInterval(this._intervalo);
    this._intervalo = setInterval(() => this.revisarServidor(), 60000);
    this.conectar();
  },

  async revisarServidor() {
    const el = $("#estadoServidor");
    if (!el) return;
    let clase = "rojo", texto = "Servidor IA: Offline";
    try {
      const e = await api("/api/estado");
      this.estadoIA = e;
      if (e.yolo && !e.modo_demo) [clase, texto] = ["verde", "Servidor IA: Online"];
      else if (e.yolo) [clase, texto] = ["amarillo", "Servidor IA: Online · sin modelo de baches"];
      else [clase, texto] = ["amarillo", "Servidor: Online · IA no instalada"];
    } catch {}
    el.innerHTML = `<span class="punto ${clase}"></span><span>${texto}</span>`;
  },

  conectar() {
    if (this.ws) return;
    const ws = new WebSocket(`${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws?token=${encodeURIComponent(Sesion.token)}`);
    this.ws = ws;
    ws.onmessage = e => this.alMensaje(JSON.parse(e.data));
    ws.onclose = () => {
      if (this.ws === ws) this.ws = null;
      if (Sesion.token) setTimeout(() => Sesion.token && this.conectar(), 3000);
    };
  },

  desconectar() {
    const ws = this.ws;
    this.ws = null;
    ws?.close();
    clearInterval(this._intervalo);
  },

  alMensaje(m) {
    this.vista?.alMensaje?.(m);
    const viendo = this.vista instanceof VistaAnalisis && this.vista.id === m.dano?.recorrido_id;
    if (m.tipo === "dano" && m.accion === "nuevo" && m.dano.origen === "ia" && !viendo) {
      const d = m.dano;
      avisar(`<b>¡${Fmt.tipo(d.tipo)} detectado!</b> ${d.codigo}<br>${esc(d.canton || "")}, ${esc(d.provincia || "")} · IP ${esc(d.ip_publica || "—")}`,
        "alerta", () => { location.hash = `#/recorridos/${d.recorrido_id}?dano=${d.id}`; });
    }
  },
};

async function cerrarSesion() {
  try { await api("/api/auth/logout", { metodo: "POST" }); } catch {}
  Sesion.borrar();
  App.desconectar();
  $("#raiz").innerHTML = "";
  location.hash = "#/login";
}

// ------------------------------------------------------------------ 00 · Inicio de sesión
function pantallaLogin() {
  const ayudaRol = {
    admin: "Puede validar daños, editar, eliminar, asignar cuadrillas y exportar reportes.",
    tecnico: "Puede revisar recorridos, marcar daños manualmente y registrarlos como reparados.",
  };
  let rol = "admin";
  $("#raiz").innerHTML = `<div class="login">
    <section class="login-arte" style="background-image:url('/api/escena.svg?v=0')">
      ${MARCA}
      <div class="login-lema">
        <h2>Del tablero del vehículo al mapa de reparaciones.</h2>
        <p>Los conductores capturan la vía con la cámara del vehículo; la IA detecta baches, grietas y hundimientos, y el equipo de mantenimiento valida y asigna las reparaciones.</p>
      </div>
    </section>
    <section class="login-form">
      <form id="formLogin" novalidate>
        <h1>Panel de mantenimiento vial</h1>
        <p class="sub">Acceso para el personal municipal: administradores y técnicos de mantenimiento.</p>
        <label class="campo"><span>Correo institucional o usuario</span>
          <input class="entrada" type="text" name="correo" autocomplete="username" placeholder="nombre@municipio.gob.ec" required></label>
        <label class="campo"><span>Contraseña</span>
          <input class="entrada" type="password" name="contrasena" autocomplete="current-password" required></label>
        <div class="campo"><span>Rol</span>
          <div class="segmentado" id="roles">
            <button type="button" data-rol="admin" class="activo">Administrador</button>
            <button type="button" data-rol="tecnico">Técnico de mantenimiento</button>
          </div></div>
        <p class="ayuda" id="ayudaRol">${ayudaRol.admin}</p>
        <div class="error-form" id="errorLogin" role="alert"></div>
        <button class="btn primario bloque" type="submit">Ingresar al panel</button>
        <p class="cambiar-form">¿No tienes cuenta? <a href="#" id="irRegistro">Crear una</a></p>
        <div class="login-pie">¿Eres conductor? La captura de recorridos se hace desde el vehículo: cámara con IA o el simulador de Unity.</div>
        <div class="credenciales-demo">Cuentas de prueba · Administrador: <b>admin</b> / admin123 · <b>c.ruiz@milagro.gob.ec</b> / vialscan2026 · Técnico: <b>m.torres@milagro.gob.ec</b> / tecnico2026</div>
      </form>
    </section>
  </div>`;
  $("#roles").onclick = e => {
    const b = e.target.closest("[data-rol]");
    if (!b) return;
    rol = b.dataset.rol;
    $$("#roles button").forEach(x => x.classList.toggle("activo", x === b));
    $("#ayudaRol").textContent = ayudaRol[rol];
  };
  $("#formLogin").onsubmit = async e => {
    e.preventDefault();
    const f = new FormData(e.target), boton = $("button[type=submit]", e.target);
    const correo = f.get("correo").trim(), contrasena = f.get("contrasena");
    if (!correo || !contrasena) return ($("#errorLogin").textContent = "Escribe tu correo y contraseña.");
    boton.disabled = true;
    try {
      const r = await api("/api/auth/login", { metodo: "POST", datos: { correo, contrasena, rol } });
      Sesion.guardar(r);
      $("#raiz").innerHTML = "";
      location.hash = "#/recorridos";
    } catch (err) {
      $("#errorLogin").textContent = err.message;
    } finally { boton.disabled = false; }
  };
  $("#irRegistro").onclick = e => { e.preventDefault(); pantallaRegistro(); };
  $("input[name=correo]").focus();
}

// ------------------------------------------------------------------ Crear cuenta
function pantallaRegistro() {
  let rol = "tecnico";
  const ayudaRol = {
    tecnico: "Revisa recorridos, marca daños manualmente y los registra como reparados.",
    admin: "Valida, edita, elimina, asigna cuadrillas y administra usuarios. Necesita el código de administrador.",
  };
  $(".login-form").innerHTML = `<form id="formRegistro" novalidate>
      <h1>Crear cuenta</h1>
      <p class="sub">Registro del personal municipal para el panel de mantenimiento vial.</p>
      <label class="campo"><span>Nombre completo</span><input class="entrada" name="nombre" autocomplete="name" placeholder="Ing. Ana Pérez" required></label>
      <label class="campo"><span>Correo institucional o usuario</span><input class="entrada" name="correo" autocomplete="username" placeholder="a.perez@milagro.gob.ec" required></label>
      <div class="dos-col">
        <label class="campo"><span>Contraseña</span><input class="entrada" type="password" name="contrasena" autocomplete="new-password" minlength="6" required></label>
        <label class="campo"><span>Repetir contraseña</span><input class="entrada" type="password" name="repetir" autocomplete="new-password" minlength="6" required></label>
      </div>
      <div class="campo"><span>Rol</span>
        <div class="segmentado" id="rolesRegistro">
          <button type="button" data-rol="admin">Administrador</button>
          <button type="button" data-rol="tecnico" class="activo">Técnico de mantenimiento</button>
        </div></div>
      <p class="ayuda" id="ayudaRolRegistro">${ayudaRol.tecnico}</p>
      <label class="campo oculto" id="campoCodigo"><span>Código de administrador</span>
        <input class="entrada" name="codigo_admin" inputmode="numeric" autocomplete="off" placeholder="6 dígitos">
        <small class="ayuda" style="margin:0">Lo ve un administrador en Configuración › Sistema, o en la consola del servidor.</small></label>
      <div class="error-form" id="errorRegistro" role="alert"></div>
      <button class="btn primario bloque" type="submit">Crear cuenta</button>
      <p class="cambiar-form">¿Ya tienes cuenta? <a href="#" id="irLogin">Inicia sesión</a></p>
    </form>`;
  $("#rolesRegistro").onclick = e => {
    const b = e.target.closest("[data-rol]");
    if (!b) return;
    rol = b.dataset.rol;
    $$("#rolesRegistro button").forEach(x => x.classList.toggle("activo", x === b));
    $("#ayudaRolRegistro").textContent = ayudaRol[rol];
    $("#campoCodigo").classList.toggle("oculto", rol !== "admin");
  };
  $("#irLogin").onclick = e => { e.preventDefault(); pantallaLogin(); };
  $("#formRegistro").onsubmit = async e => {
    e.preventDefault();
    const f = Object.fromEntries(new FormData(e.target)), error = $("#errorRegistro"), boton = $("button[type=submit]", e.target);
    if (f.nombre.trim().length < 3) return (error.textContent = "Escribe tu nombre completo.");
    if (!/^\S{3,}$/.test(f.correo.trim())) return (error.textContent = "El correo o usuario debe tener al menos 3 caracteres y sin espacios.");
    if (f.contrasena.length < 6) return (error.textContent = "La contraseña debe tener al menos 6 caracteres.");
    if (f.contrasena !== f.repetir) return (error.textContent = "Las contraseñas no coinciden.");
    if (rol === "admin" && !f.codigo_admin.trim()) return (error.textContent = "Escribe el código de administrador.");
    boton.disabled = true;
    try {
      const r = await api("/api/auth/registro", { metodo: "POST", datos: {
        nombre: f.nombre.trim(), correo: f.correo.trim(), contrasena: f.contrasena, rol, codigo_admin: f.codigo_admin.trim() || null } });
      Sesion.guardar(r);
      $("#raiz").innerHTML = "";
      location.hash = "#/recorridos";
      setTimeout(() => avisar(`Cuenta creada. Bienvenido/a, ${esc(r.usuario.nombre)}.`, "ok"), 300);
    } catch (err) {
      error.textContent = err.message;
    } finally { boton.disabled = false; }
  };
  $("input[name=nombre]").focus();
}

// ------------------------------------------------------------------ 01 · Recorridos recibidos
class VistaRecorridos {
  constructor(cont) {
    this.cont = cont;
    cont.innerHTML = `<div class="pagina">
      <div class="pagina-cab"><div><h1>Recorridos recibidos</h1>
        <p class="sub">Recorridos enviados por los conductores · valida daños y asigna reparaciones</p></div>
        <button class="btn" id="btnSubir">${ICONO.subir}Subir recorrido</button></div>
      <h2 class="seccion-titulo">Recorridos recientes</h2>
      <div class="lista-recorridos" id="listaRec"><div class="cargando">Cargando…</div></div></div>`;
    $("#btnSubir").onclick = () => subirRecorrido();
    this.cargar();
    this._reloj = setInterval(() => { if (this.vivos?.size) this.cargar(); }, 10000);
  }

  destruir() { clearInterval(this._reloj); clearTimeout(this._t); }

  async cargar() {
    try {
      const { recorridos } = await api("/api/recorridos");
      this.vivos = new Set(recorridos.filter(r => r.en_vivo).map(r => r.id));
      const lista = $("#listaRec", this.cont);
      if (!lista) return;
      lista.innerHTML = recorridos.length ? recorridos.map(r => {
        const chip = r.total_danos === 0 && r.sin_procesar ? "Sin procesar" : `${r.total_danos} Daño${r.total_danos === 1 ? "" : "s"}`;
        const color = { completado: "verde", en_proceso: "azul", pendiente: "amarillo" }[r.estado];
        return `<a class="tarjeta-recorrido" href="#/recorridos/${r.id}">
          <span class="icono-caja">${ICONO.mapas}</span>
          <div class="info"><b>${esc(r.nombre)}</b><div class="meta">${esc(r.codigo)}<span class="sep">•</span>${Fmt.relativa(r.actualizado || r.creado)}</div></div>
          ${r.en_vivo ? `<span class="chip vivo">● EN VIVO</span>` : ""}<span class="chip">${chip}</span>
          <span class="estado-rec"><span class="punto ${color}"></span>${Fmt.estadoRecorrido(r.estado)}</span>
          <span class="chevron">${ICONO.chevron}</span></a>`;
      }).join("") : `<div class="vacio">Aún no hay recorridos. Inicia el simulador de Unity o sube fotos de una vía.</div>`;
    } catch (e) { avisar(esc(e.message), "error"); }
  }

  alMensaje(m) {
    if (m.tipo === "vivo") {
      if (this.vivos?.has(m.recorrido_id)) return;
      (this.vivos ||= new Set()).add(m.recorrido_id);
    }
    clearTimeout(this._t);
    this._t = setTimeout(() => this.cargar(), 400);
  }
}

function subirRecorrido() {
  modal(`<h3>Subir recorrido</h3><p>Sube fotos de la vía tomadas desde el vehículo. Quedará como <b>Sin procesar</b> hasta analizarlo con la IA.</p>
    <form id="formSubir">
      <label class="campo"><span>Nombre de la vía</span><input class="entrada" name="nombre" required placeholder="Av. 17 de Septiembre – Centro"></label>
      <div class="dos-col">
        <label class="campo"><span>Latitud</span><input class="entrada" name="lat" type="number" step="any" required placeholder="-2.1326"></label>
        <label class="campo"><span>Longitud</span><input class="entrada" name="lon" type="number" step="any" required placeholder="-79.5832"></label>
      </div>
      <button type="button" class="btn chico" id="btnUbicacion" style="margin:-4px 0 14px">${ICONO.mapas}Usar mi ubicación actual</button>
      <label class="campo"><span>Fotos (JPG o PNG)</span><input class="entrada" name="imagenes" type="file" accept="image/jpeg,image/png,image/webp" multiple required style="padding-top:9px"></label>
      <div class="error-form" id="errSubir"></div>
      <div class="botones" style="display:flex;gap:12px"><button type="button" class="btn" data-cerrar style="flex:1">Cancelar</button>
        <button class="btn primario" style="flex:1">Subir</button></div>
    </form>`, (fondo, cerrar) => {
    $("#btnUbicacion", fondo).onclick = () => navigator.geolocation?.getCurrentPosition(
      p => { fondo.querySelector("[name=lat]").value = p.coords.latitude.toFixed(6); fondo.querySelector("[name=lon]").value = p.coords.longitude.toFixed(6); },
      () => ($("#errSubir", fondo).textContent = "No se pudo obtener la ubicación. Escríbela a mano."));
    $("#formSubir", fondo).onsubmit = async e => {
      e.preventDefault();
      const boton = $("button.primario", fondo);
      boton.disabled = true;
      try {
        const r = await api("/api/recorridos", { metodo: "POST", formulario: new FormData(e.target) });
        cerrar();
        avisar("Recorrido subido. Pulsa <b>Analizar con IA</b> para detectar los daños.", "ok");
        location.hash = `#/recorridos/${r.id}`;
      } catch (err) { $("#errSubir", fondo).textContent = err.message; }
      finally { boton.disabled = false; }
    };
  });
}

// ------------------------------------------------------------------ 05-08 · Resultados del análisis
class VistaAnalisis {
  constructor(cont, id, params) {
    this.cont = cont;
    this.id = id;
    this.rec = null;
    this.fotoIdx = 0;
    this.sel = +params.get("dano") || null;
    this.abrirDetalle = !!this.sel;
    this.modo = "camara";
    this.flot = null;          // null | "detalle" | "edicion" | "nuevo"
    this.borrador = null;
    this.asignando = false;
    this.dibujo = null;        // { activo, inicio, caja }
    this.vivo = null;          // último fotograma en vivo de Unity
    this.verVivo = true;       // en "Cámara": transmisión en vivo (true) o fotogramas guardados (false)
    this._reloj = setInterval(() => {
      if (this.vivo && Date.now() - this.vivo.recibido > 8000) { this.vivo = null; this.pintar(); }
    }, 2000);
    cont.innerHTML = `<div class="analisis">
      <section class="analisis-centro">
        <div class="barra-sup">
          <button class="volver" title="Volver a recorridos" id="btnVolver">${ICONO.atras}</button>
          <span>GPS: <b id="gps">—</b></span><span class="centro">Velocidad: <b id="vel">—</b></span>
          <span class="estado-analisis" id="estAnalisis"></span>
        </div>
        <div class="visor" id="visor">
          <div class="conmutador" role="tablist">
            <button data-modo="camara" class="activo">Cámara</button><button data-modo="mapa">Mapa GPS</button>
          </div>
          <div class="lienzo" id="lienzo"><img id="imgFoto" alt="Fotograma de la cámara del vehículo"><div id="cajas"></div></div>
          <div class="sin-imagen oculto" id="sinImagen"></div>
          <div class="mapa-gps oculto" id="mapaGps"></div>
          <div class="tarjeta-ruta oculto" id="tarjetaRuta"></div>
          <div class="navegador-fotos oculto" id="navFotos"></div>
          <div class="aviso-dibujo oculto" id="avisoDibujo">Arrastra sobre la imagen para marcar el daño (p. ej. una grieta) · Esc para cancelar</div>
          <div id="flot"></div>
        </div>
      </section>
      <aside class="panel-der" id="panel"><div class="cargando">Cargando…</div></aside>
    </div>`;
    this.enlazar();
    this.cargar();
  }

  get foto() { return this.rec?.lista_fotogramas[this.fotoIdx] || null; }
  get mostrandoVivo() { return this.modo === "camara" && !!this.vivo && this.verVivo; }
  get danoSel() { return this.rec?.danos.find(d => d.id === this.sel) || null; }
  get puedeAdmin() { return Sesion.esAdmin; }

  enlazar() {
    $("#btnVolver").onclick = () => { location.hash = "#/recorridos"; };
    $(".conmutador", this.cont).onclick = e => {
      const b = e.target.closest("[data-modo]");
      if (b) this.cambiarModo(b.dataset.modo);
    };
    $("#imgFoto").onload = () => this.ajustarLienzo();
    this.observador = new ResizeObserver(() => { this.ajustarLienzo(); this.mapa?.ajustar(); });
    this.observador.observe($("#visor"));
    $("#cajas").onclick = e => {
      const c = e.target.closest("[data-id]");
      if (c && c.dataset.id && !this.dibujo) this.seleccionar(+c.dataset.id, true);
    };
    const lienzo = $("#lienzo");
    lienzo.addEventListener("pointerdown", e => this.dibujoInicio(e));
    lienzo.addEventListener("pointermove", e => this.dibujoMover(e));
    lienzo.addEventListener("pointerup", e => this.dibujoFin(e));
    this.teclas = e => {
      if (e.target.matches("input, select, textarea")) return;
      if (e.key === "Escape") { if (this.dibujo) this.cancelarDibujo(); else this.cerrarFlot(); }
      if (e.key === "ArrowRight") this.irFoto(this.fotoIdx + 1);
      if (e.key === "ArrowLeft") this.irFoto(this.fotoIdx - 1);
    };
    document.addEventListener("keydown", this.teclas);
  }

  destruir() {
    document.removeEventListener("keydown", this.teclas);
    this.observador?.disconnect();
    this.mapa?.destruir();
    clearInterval(this._reloj);
    if (this.urlVivo) URL.revokeObjectURL(this.urlVivo);
  }

  async cargar() {
    try {
      this.rec = await api(`/api/recorridos/${this.id}`);
    } catch (e) {
      $("#panel").innerHTML = `<div class="vacio">${esc(e.message)}</div>`;
      return;
    }
    if (this.sel && !this.danoSel) { this.sel = null; if (this.flot === "detalle") this.flot = null; }
    if (this.fotoIdx >= this.rec.lista_fotogramas.length) this.fotoIdx = 0;
    if (this.rec.vivo && !this.vivo) { this.vivo = { ...this.rec.vivo, recibido: Date.now() }; this.cargarImagenVivo(); }
    if (this.abrirDetalle && this.danoSel) {
      this.abrirDetalle = false;
      this.seleccionar(this.sel, true);
      return;
    }
    this.pintar();
  }

  recargarLuego() {
    if (this.flot === "edicion" || this.flot === "nuevo" || this.dibujo) { this.pendiente = true; return; }
    clearTimeout(this._t);
    this._t = setTimeout(() => this.cargar(), 300);
  }

  alMensaje(m) {
    if (m.tipo === "vivo") { if (m.recorrido_id === this.id) this.actualizarVivo(m); return; }
    if (m.tipo === "recorrido" && m.id === this.id && m.accion === "eliminado") {
      avisar("Este recorrido fue eliminado.", "error");
      location.hash = "#/recorridos";
      return;
    }
    const afecta = (m.tipo === "recorrido" && m.id === this.id) || (m.tipo === "dano" && (m.dano?.recorrido_id === this.id || m.recorrido_id === this.id));
    if (afecta) this.recargarLuego();
  }

  // -------------------------------------------------- pintado
  pintar() {
    if (!this.rec) return;
    this.pintarBarra();
    this.pintarFoto();
    this.pintarCajas();
    this.pintarPanel();
    this.pintarFlot();
    if (this.modo === "mapa") this.pintarMapa();
  }

  pintarBarra() {
    const r = this.rec, f = this.foto, v = this.vivo;
    const fuente = v && (this.verVivo || this.modo === "mapa") ? v : f;
    $("#gps").textContent = Fmt.coord(fuente?.lat ?? r.lat, fuente?.lon ?? r.lon);
    $("#vel").textContent = fuente?.velocidad != null ? `${Math.round(fuente.velocidad)} km/h` : "—";
    const est = $("#estAnalisis");
    const pines = r.danos.filter(d => d.lat != null).length;
    const [txt, cls] = this.modo === "mapa" ? [`${pines} PIN${pines === 1 ? "" : "ES"} · ${v ? "GPS ACTIVO" : "GPS REGISTRADO"}`, "ok"]
      : v ? ["● EN VIVO · ANALIZANDO", "vivo"] : r.estado === "completado" ? ["ANÁLISIS COMPLETADO", "ok"]
      : r.estado === "en_proceso" ? ["RECIBIENDO DETECCIONES", "curso"] : ["SIN PROCESAR", "pend"];
    est.textContent = txt;
    est.className = `estado-analisis ${cls}`;
  }

  actualizarVivo(m) {
    const nuevo = !this.vivo;
    this.vivo = { ...m, recibido: Date.now() };
    this.cargarImagenVivo();
    if (!this.rec) return;
    if (m.lat != null) {
      const ult = this.rec.ruta[this.rec.ruta.length - 1];
      if (!ult || Math.abs(ult.lat - m.lat) + Math.abs(ult.lon - m.lon) > 0.00003) this.rec.ruta.push({ lat: m.lat, lon: m.lon });
    }
    if (nuevo) return this.pintar();
    this.pintarBarra();
    if (this.mostrandoVivo) { this.pintarCajas(); this.pintarNav(); }
    if (this.modo === "mapa" && this.mapa) {
      this.mapa.vehiculo(m.lat, m.lon, !this.sel);
      this.mapa.ruta(this.puntosRuta(), { fin: false });
      this.pintarTarjetaRuta();
    }
  }

  async cargarImagenVivo() {
    if (this._cargandoVivo) return;
    this._cargandoVivo = true;
    try {
      const r = await fetch(`/api/vivo/${this.id}.jpg?t=${Date.now()}`, { headers: { Authorization: `Bearer ${Sesion.token}` } });
      if (!r.ok) return;
      const url = URL.createObjectURL(await r.blob());
      if (this.urlVivo) URL.revokeObjectURL(this.urlVivo);
      this.urlVivo = url;
      if (this.mostrandoVivo) this.pintarFoto();
    } catch {} finally { this._cargandoVivo = false; }
  }

  puntosRuta() {
    const r = this.rec;
    return r.ruta?.length > 1 ? r.ruta : r.lista_fotogramas.filter(f => f.lat != null);
  }

  pintarFoto() {
    if (this.mostrandoVivo) {
      $("#lienzo").classList.remove("oculto");
      $("#sinImagen").classList.add("oculto");
      const img = $("#imgFoto");
      if (this.urlVivo && img.getAttribute("src") !== this.urlVivo) img.src = this.urlVivo;
      else this.ajustarLienzo();
      this.pintarNav();
      return;
    }
    const f = this.foto, img = $("#imgFoto"), camara = this.modo === "camara";
    const hay = !!f?.imagen;
    $("#lienzo").classList.toggle("oculto", !camara || !hay);
    const sin = $("#sinImagen");
    sin.classList.toggle("oculto", !camara || hay);
    sin.innerHTML = this.rec.lista_fotogramas.length ? "Este fotograma no tiene imagen." :
      `Este recorrido no tiene imágenes de cámara.<br><button class="btn chico" style="margin-top:12px" data-ver-mapa>Ver en Mapa GPS</button>`;
    $("[data-ver-mapa]", sin)?.addEventListener("click", () => this.cambiarModo("mapa"));
    if (hay && img.getAttribute("src") !== f.imagen) img.src = f.imagen;
    else this.ajustarLienzo();
    this.pintarNav();
  }

  pintarNav() {
    const nav = $("#navFotos"), n = this.rec.lista_fotogramas.length, camara = this.modo === "camara";
    if (this.mostrandoVivo) {
      nav.classList.remove("oculto");
      nav.innerHTML = `<span class="en-vivo">● EN VIVO</span><button class="texto" data-capturar>📸 Capturar y marcar</button>
        ${n ? `<button class="texto" data-vivo="0">Fotogramas guardados (${n})</button>` : ""}`;
    } else {
      nav.classList.toggle("oculto", !camara || (n < 2 && !this.vivo));
      nav.innerHTML = `${n ? `<button ${this.fotoIdx === 0 ? "disabled" : ""} data-paso="-1" aria-label="Anterior">‹</button>
        Fotograma ${this.fotoIdx + 1} de ${n}<button ${this.fotoIdx >= n - 1 ? "disabled" : ""} data-paso="1" aria-label="Siguiente">›</button>` : ""}
        ${this.vivo ? `<button class="texto" data-vivo="1"><span class="en-vivo">●</span> Volver a EN VIVO</button>` : ""}`;
    }
    nav.onclick = e => {
      const b = e.target.closest("[data-paso]"), v = e.target.closest("[data-vivo]");
      if (e.target.closest("[data-capturar]")) return this.iniciarDibujo();
      if (b) this.irFoto(this.fotoIdx + +b.dataset.paso);
      if (v) { this.verVivo = v.dataset.vivo === "1"; if (this.verVivo) { this.sel = null; this.flot = null; } this.pintar(); }
    };
  }

  ajustarLienzo() {
    const img = $("#imgFoto"), visor = $("#visor"), lienzo = $("#lienzo");
    if (!img?.naturalWidth || !visor) return;
    const ar = img.naturalWidth / img.naturalHeight;
    let w = visor.clientWidth, h = w / ar;
    if (h > visor.clientHeight) { h = visor.clientHeight; w = h * ar; }
    lienzo.style.width = `${w}px`;
    lienzo.style.height = `${h}px`;
    this.posicionarFlot();
  }

  irFoto(i) {
    if (!this.rec || i < 0 || i >= this.rec.lista_fotogramas.length || i === this.fotoIdx) return;
    if (this.flot === "edicion" || this.flot === "nuevo" || this.dibujo) return;
    this.fotoIdx = i;
    if (this.danoSel && this.danoSel.fotograma_id !== this.foto.id) { this.sel = null; if (this.flot === "detalle") this.flot = null; }
    this.pintar();
  }

  cajasVisibles() {
    if (this.mostrandoVivo) {
      const sev = { leve: "baja", moderado: "media", grave: "alta" };
      return (this.vivo.detecciones || []).map(d => ({ id: 0, codigo: "", origen: "ia", estado: "pendiente", tipo: d.tipo || "bache",
        confianza: d.confianza, severidad: sev[d.severidad] || d.severidad, caja: [d.x, d.y, d.w, d.h] }));
    }
    const f = this.foto;
    if (!f) return [];
    let lista = this.rec.danos.filter(d => d.fotograma_id === f.id && d.caja);
    if (this.borrador && this.flot === "edicion") lista = lista.map(d => d.id === this.borrador.id ? { ...d, ...this.borrador } : d);
    if (this.borrador && this.flot === "nuevo") lista = [...lista, { ...this.borrador, id: 0, codigo: "NUEVO", origen: "manual", estado: "pendiente" }];
    return lista;
  }

  pintarCajas() {
    const html = this.cajasVisibles().map(d => {
      const pct = v => `${(v * 100).toFixed(3)}%`;
      const [x, y, w, h] = d.caja;
      const etq = d.origen === "manual" ? `${Fmt.tipo(d.tipo)} · MANUAL` : `${Fmt.tipo(d.tipo)} (${Fmt.pct(d.confianza)})`;
      const clases = ["caja", d.origen === "manual" && "manual", !d.severidad && "sin-sev", d.estado === "reparado" && "reparado",
        d.id === this.sel && "sel"].filter(Boolean).join(" ");
      return `<div class="${clases}" data-id="${d.id || ""}" style="--c:${colorSev(d.severidad)};left:${pct(x)};top:${pct(y)};width:${pct(w)};height:${pct(h)}"
        title="${esc(d.codigo)}"><span class="etq">${esc(etq.toUpperCase())}${d.estado === "reparado" ? " ✓" : ""}</span></div>`;
    }).join("");
    const dib = this.dibujo?.caja;
    $("#cajas").classList.toggle("con-seleccion", !!this.sel && this.flot === "detalle" && !this.mostrandoVivo);
    $("#cajas").innerHTML = html + (dib ? `<div class="caja nueva" style="left:${dib[0] * 100}%;top:${dib[1] * 100}%;width:${dib[2] * 100}%;height:${dib[3] * 100}%"></div>` : "");
  }

  pintarPanel() {
    const r = this.rec, admin = this.puedeAdmin;
    const items = r.danos.map(d => {
      const c = colorSev(d.severidad);
      const estadoExtra = d.estado !== "pendiente" ? `<span class="sep">•</span>${Fmt.estado(d.estado)}` : "";
      return `<button class="item-dano ${d.id === this.sel ? "sel" : ""}" style="--c:${c}" data-id="${d.id}">
        <b>${Fmt.tipo(d.tipo)}</b>
        <span class="conf ${d.origen === "manual" ? "manual" : ""}">${d.origen === "manual" ? "Manual" : Fmt.pct(d.confianza)}</span>
        <span class="meta">${esc(d.codigo)}<span class="sep">•</span>Severidad <span class="sev-txt" style="color:${d.severidad ? c : "var(--texto)"}">${Fmt.severidad(d.severidad)}</span>${estadoExtra}</span>
      </button>`;
    }).join("");
    const pendiente = r.sin_procesar > 0;
    $("#panel").innerHTML = `
      <h2>Resultados del Análisis</h2>
      <p class="sub">${esc(subtituloFuente(r.fuente))}</p>
      <p class="sub" style="margin-top:6px">${nombreRecorridoCorto(r)}</p>
      <hr class="separador">
      <p class="rotulo">ANOMALÍAS DETECTADAS</p>
      <p class="ayuda-lista">${r.danos.length ? "Selecciona un daño en la lista o en la imagen para ver sus datos." : pendiente ? "Este recorrido aún no se ha analizado." : "No se detectaron daños en este recorrido."}</p>
      ${pendiente ? `<button class="btn primario bloque" id="btnProcesar" style="margin-bottom:14px">${ICONO.ia}Analizar con IA (${r.sin_procesar} foto${r.sin_procesar > 1 ? "s" : ""})</button>` : ""}
      <div class="lista-danos" id="listaDanos">${items}</div>
      <div class="acciones-panel">
        <button class="btn punteado" id="btnMarcar">${ICONO.mas}Marcar daño manualmente</button>
        <button class="btn primario" id="btnReporte">${ICONO.doc}Guardar Reporte</button>
        <button class="btn" id="btnPdf">${ICONO.descargar}Exportar PDF</button>
        ${admin ? `<button class="btn fantasma chico" id="btnEliminarRec" style="color:var(--tenue);margin-top:8px">${ICONO.basura}Eliminar recorrido</button>` : ""}
      </div>`;
    $("#listaDanos").onclick = e => { const b = e.target.closest("[data-id]"); if (b) this.seleccionar(+b.dataset.id, true); };
    $("#btnMarcar").onclick = () => this.iniciarDibujo();
    $("#btnReporte").onclick = () => this.guardarReporte();
    $("#btnPdf").onclick = () => window.open(`/reporte.html?recorrido=${this.id}&imprimir=1`, "_blank");
    $("#btnProcesar")?.addEventListener("click", e => this.procesar(e.target.closest("button")));
    $("#btnEliminarRec")?.addEventListener("click", () => this.eliminarRecorrido());
  }

  // -------------------------------------------------- selección y modos
  seleccionar(id, abrir) {
    this.sel = id;
    this.verVivo = false;
    this.asignando = false;
    const d = this.danoSel;
    if (d?.fotograma_id) {
      const i = this.rec.lista_fotogramas.findIndex(f => f.id === d.fotograma_id);
      if (i >= 0) this.fotoIdx = i;
    } else if (d && this.modo === "camara") this.modo = "mapa";
    if (abrir) { this.flot = "detalle"; this.borrador = null; }
    this.aplicarModo();
    this.pintar();
    if (this.modo === "mapa") this.mapa?.enfocar(d);
  }

  cambiarModo(modo) {
    if (this.dibujo) this.cancelarDibujo();
    this.modo = modo;
    this.aplicarModo();
    this.pintar();
  }

  aplicarModo() {
    $$(".conmutador button", this.cont).forEach(b => b.classList.toggle("activo", b.dataset.modo === this.modo));
    $("#mapaGps").classList.toggle("oculto", this.modo !== "mapa");
    $("#tarjetaRuta").classList.toggle("oculto", this.modo !== "mapa");
    $$(".nav a").forEach(a => a.classList.toggle("activo", a.dataset.seccion === (this.modo === "mapa" ? "mapas" : "recorridos")));
  }

  pintarTarjetaRuta() {
    const r = this.rec, puntos = this.puntosRuta();
    let km = 0;
    for (let i = 1; i < puntos.length; i++) km += distanciaKm(puntos[i - 1], puntos[i]);
    const fechas = [...(r.ruta || []), ...r.lista_fotogramas].map(p => p.fecha).filter(Boolean).sort();
    const hora = f => new Date(f).toLocaleTimeString("es-EC", { hour: "2-digit", minute: "2-digit", hour12: false });
    const vels = [...(r.ruta?.length ? r.ruta : r.lista_fotogramas)].map(p => p.velocidad).filter(v => v != null && v > 0);
    const prom = vels.length ? Math.round(vels.reduce((a, b) => a + b, 0) / vels.length) : null;
    const datos = [
      `${km < 10 ? km.toFixed(km < 1 ? 2 : 1) : Math.round(km)} km`,
      fechas.length ? `${hora(fechas[0])} – ${hora(fechas[fechas.length - 1])}` : null,
      prom != null ? `${prom} km/h prom.` : null,
      `${puntos.length} puntos GPS`,
    ].filter(Boolean).join(" · ");
    $("#tarjetaRuta").innerHTML = `<b>Recorrido · ${esc(r.nombre.split(" – ")[0])}</b>
      <p>${datos}</p>
      <div class="leyenda"><span><i style="background:${colorSev("alta")}"></i>Alta</span><span><i style="background:${colorSev("media")}"></i>Media</span>
        <span><i style="background:${colorSev("baja")}"></i>Baja</span><span><i style="background:${colorSev(null)}"></i>Sin asignar</span></div>`;
  }

  async pintarMapa() {
    if (!this.mapa) {
      if (this._creandoMapa) return;
      this._creandoMapa = true;
      this.mapa = await Mapas.crear($("#mapaGps"), { alClic: d => this.seleccionar(d.id, true), etiquetas: true });
      this._creandoMapa = false;
      this.mapa.ajustar();
      this._encuadrado = false;
    }
    this.mapa.marcar(this.rec.danos);
    this.mapa.ruta(this.puntosRuta(), { fin: !this.vivo });
    this.mapa.vehiculo(this.vivo?.lat, this.vivo?.lon, false);
    this.pintarTarjetaRuta();
    if (!this._encuadrado) {
      this.mapa.encuadrar([...this.rec.danos, ...this.puntosRuta(), ...(this.vivo ? [this.vivo] : [])]);
      this._encuadrado = true;
    }
  }

  // -------------------------------------------------- tarjeta flotante: detalle / edición
  cerrarFlot() {
    this.flot = null;
    this.borrador = null;
    this.asignando = false;
    this.pintar();
    if (this.pendiente) { this.pendiente = false; this.cargar(); }
  }

  pintarFlot() {
    const cont = $("#flot");
    if (!this.flot) { cont.innerHTML = ""; return; }
    if (this.flot === "detalle") return this.pintarDetalle(cont);
    return this.pintarEdicion(cont);
  }

  /** Coloca la ficha del daño al lado de su recuadro (a la derecha si cabe, si no a la izquierda). */
  posicionarFlot() {
    const flot = $("#flot .flotante");
    if (!flot) return;
    flot.style.left = flot.style.top = flot.style.transform = "";
    if (this.flot !== "detalle" || this.modo !== "camara") return;
    const caja = $(`#cajas .caja[data-id="${this.sel}"]`);
    if (!caja) return;
    const v = $("#visor").getBoundingClientRect(), c = caja.getBoundingClientRect(), f = flot.getBoundingClientRect();
    const margen = 16, sep = 18;
    let x = c.right - v.left + sep;
    if (x + f.width > v.width - margen) x = c.left - v.left - sep - f.width;
    if (x < margen) return;   // no cabe a ningún lado: queda centrada
    const y = Math.min(Math.max(margen, c.top - v.top + c.height / 2 - f.height / 2), v.height - f.height - margen);
    flot.style.transform = "none";
    flot.style.left = `${x}px`;
    flot.style.top = `${y}px`;
  }

  pintarDetalle(cont) {
    const d = this.danoSel;
    if (!d) { cont.innerHTML = ""; return; }
    const admin = this.puedeAdmin, c = colorSev(d.severidad);
    const tam = d.largo_cm == null && d.ancho_cm == null ? "— cm" : `${Fmt.cm(d.largo_cm)} × ${Fmt.cm(d.ancho_cm)} cm`;
    const zona = [d.canton, d.provincia].filter(Boolean).join(", ") || "—";
    const ip = d.ip_publica ? `${esc(d.ip_publica)}${d.ip_ciudad ? ` (${esc(d.ip_ciudad)})` : ""}` : "—";
    const reparado = d.estado === "reparado";
    cont.innerHTML = `<div class="flotante" role="dialog" aria-label="Detalle del daño ${esc(d.codigo)}">
      <div class="flot-cab"><h3><span class="punto" style="background:${c}"></span>${Fmt.tipo(d.tipo)} · ${esc(d.codigo)}</h3>
        <button class="cerrar" data-acc="cerrar" aria-label="Cerrar">${ICONO.cerrar}</button></div>
      <div class="etiquetas"><span class="etiqueta sev ${d.severidad || "ninguna"}">Severidad ${Fmt.severidad(d.severidad)}</span>
        <span class="etiqueta">${d.origen === "manual" ? "Manual" : `IA · ${Fmt.pct(d.confianza)}`}</span>
        ${d.reportes > 1 ? `<span class="etiqueta">${d.reportes} reportes</span>` : ""}</div>
      <dl class="datos">
        <dt>Tipo de daño</dt><dd>${Fmt.tipo(d.tipo)}</dd>
        <dt>Tamaño (largo × ancho)</dt><dd>${tam}</dd>
        <dt>Profundidad</dt><dd>${Fmt.cm(d.profundidad_cm)} cm</dd>
        <dt>Severidad</dt><dd style="color:${d.severidad ? c : "inherit"}">${Fmt.severidad(d.severidad)}</dd>
        <dt>Ubicación</dt><dd>${Fmt.coord(d.lat, d.lon)}</dd>
        <dt>Zona</dt><dd class="suave">${esc(zona)}</dd>
        <dt>IP de la zona</dt><dd class="suave">${ip}</dd>
        <dt>Registrado</dt><dd>${Fmt.fecha(d.creado)}</dd>
      </dl>
      ${d.lat != null ? `<div class="gmaps-links"><a href="${GMaps.abrir(d)}" target="_blank" rel="noopener">Ver en Google Maps ↗</a>
        <a href="${GMaps.street(d)}" target="_blank" rel="noopener">Street View ↗</a></div>` : ""}
      <div class="caja-estado">
        <div class="fila"><span>Estado</span><b class="estado-color ${d.estado}">${Fmt.estadoDano(d)}</b></div>
        <div class="fila"><span>Cuadrilla</span><b>${esc(d.cuadrilla || "Sin asignar")}</b></div>
        <div class="botones-estado">
          <button class="b-azul" data-acc="validar" ${!admin || d.estado !== "pendiente" ? "disabled" : ""}>Validar</button>
          <button class="b-amarillo" data-acc="asignar" ${!admin || reparado ? "disabled" : ""}>Asignar</button>
          ${reparado ? `<button class="b-azul" data-acc="reabrir" ${!admin ? "disabled" : ""}>Reabrir</button>`
                     : `<button class="b-verde" data-acc="reparar">Reparado</button>`}
        </div>
        <div id="filaAsignar"></div>
      </div>
      <div class="pie-flot">
        ${admin ? `<button class="btn primario" data-acc="editar">Editar</button><button class="btn borde-rojo" data-acc="eliminar">Eliminar</button>` : ""}
        <button class="btn" data-acc="cerrar">Cerrar</button>
      </div></div>`;
    cont.onclick = e => {
      const b = e.target.closest("[data-acc]");
      if (!b || b.disabled) return;
      const acc = b.dataset.acc;
      if (acc === "cerrar") this.cerrarFlot();
      else if (acc === "editar") this.abrirEdicion(d);
      else if (acc === "eliminar") this.eliminar(d);
      else if (acc === "asignar") this.mostrarAsignar(d);
      else if (acc === "confirmar-asignar") this.cambiarEstado(d, "asignar", $("#selCuadrilla").value);
      else this.cambiarEstado(d, acc);
    };
    if (this.asignando) this.mostrarAsignar(d);
    this.posicionarFlot();
  }

  async mostrarAsignar(d) {
    this.asignando = true;
    const fila = $("#filaAsignar");
    if (!fila) return;
    if (!this.cuadrillas) this.cuadrillas = (await api("/api/cuadrillas")).cuadrillas;
    fila.innerHTML = `<div class="asignar-fila"><select class="entrada" id="selCuadrilla" aria-label="Cuadrilla">
      ${this.cuadrillas.map(c => `<option ${c.nombre === d.cuadrilla ? "selected" : ""}>${esc(c.nombre)}</option>`).join("")}</select>
      <button class="btn primario chico" data-acc="confirmar-asignar">Asignar</button></div>`;
  }

  async cambiarEstado(d, accion, cuadrilla) {
    try {
      await api(`/api/danos/${d.id}/estado`, { metodo: "POST", datos: { accion, cuadrilla } });
      this.asignando = false;
      avisar({ validar: `${d.codigo} validado`, asignar: `${d.codigo} asignado a ${esc(cuadrilla)}`, reparar: `${d.codigo} marcado como reparado`,
        reabrir: `${d.codigo} reabierto` }[accion], "ok");
      await this.cargar();
    } catch (e) { avisar(esc(e.message), "error"); }
  }

  async eliminar(d) {
    const ok = await confirmar({
      titulo: `¿Eliminar el daño ${esc(d.codigo)}?`,
      texto: `El marcador ${d.tipo === "grieta" ? "de la grieta" : `del ${Fmt.tipo(d.tipo).toLowerCase()}`} se quitará del mapa y del reporte. Hazlo solo si fue un error de mapeo o si el daño ya fue reparado.`,
    });
    if (!ok) return;
    try {
      await api(`/api/danos/${d.id}`, { metodo: "DELETE" });
      avisar(`${d.codigo} eliminado`, "ok");
      this.sel = null;
      this.flot = null;
      await this.cargar();
    } catch (e) { avisar(esc(e.message), "error"); }
  }

  abrirEdicion(d) {
    this.flot = "edicion";
    this.borrador = { id: d.id, codigo: d.codigo, tipo: d.tipo, largo_cm: d.largo_cm, ancho_cm: d.ancho_cm,
      profundidad_cm: d.profundidad_cm, severidad: d.severidad };
    this.pintar();
  }

  pintarEdicion(cont) {
    const b = this.borrador, nuevo = this.flot === "nuevo";
    const val = v => (v == null ? "" : v);
    cont.innerHTML = `<div class="flotante edicion" role="dialog" aria-label="Editar daño">
      <div class="flot-cab"><h3>${nuevo ? "Nuevo daño" : `Editar daño · ${esc(b.codigo)}`}</h3>
        <span class="modo-edicion">${nuevo ? "Marcado manual" : "Modo edición"}</span></div>
      <div class="campo"><span>Tipo de daño</span><div class="segmentado" id="eTipo">
        ${["bache", "grieta", "hundimiento"].map(t => `<button type="button" data-tipo="${t}" class="${b.tipo === t ? "activo" : ""}">${Fmt.tipo(t)}</button>`).join("")}
      </div></div>
      <div class="campo"><span>Largo × ancho</span><div class="dos-col">
        <label class="con-sufijo"><input class="entrada" type="number" min="0" step="1" id="eLargo" value="${val(b.largo_cm)}" aria-label="Largo en cm"><em>cm</em></label>
        <label class="con-sufijo"><input class="entrada" type="number" min="0" step="1" id="eAncho" value="${val(b.ancho_cm)}" aria-label="Ancho en cm"><em>cm</em></label>
      </div></div>
      <div class="campo"><span>Profundidad</span><div class="stepper">
        <button type="button" data-prof="-1" aria-label="Menos">−</button>
        <label class="con-sufijo"><input class="entrada" type="number" min="0" step="1" id="eProf" value="${val(b.profundidad_cm)}" aria-label="Profundidad en cm"><em>cm</em></label>
        <button type="button" data-prof="1" aria-label="Más">+</button></div></div>
      <div class="campo"><span>Severidad</span><div class="sevs" id="eSev">
        ${["baja", "media", "alta"].map(s => `<button type="button" class="s-${s} ${b.severidad === s ? "activo" : ""}" data-sev="${s}">${Fmt.severidad(s)}</button>`).join("")}
      </div></div>
      <div class="color-marcador">Color del marcador: <b style="color:${b.severidad ? colorSev(b.severidad) : "var(--suave)"}">
        <span class="punto" style="background:${colorSev(b.severidad)}"></span>${Fmt.severidad(b.severidad)}</b></div>
      <div class="error-form" id="eError"></div>
      <div class="pie-flot" style="border:0;padding:0">
        <button class="btn" data-acc="cancelar">Cancelar</button><button class="btn primario" data-acc="guardar">${nuevo ? "Guardar daño" : "Guardar cambios"}</button></div>
    </div>`;
    const num = id => { const v = $(id).value; return v === "" ? null : Math.max(0, +v); };
    const leer = () => { b.largo_cm = num("#eLargo"); b.ancho_cm = num("#eAncho"); b.profundidad_cm = num("#eProf"); };
    cont.oninput = leer;
    cont.onclick = e => {
      const t = e.target.closest("[data-tipo]"), s = e.target.closest("[data-sev]"), p = e.target.closest("[data-prof]"), a = e.target.closest("[data-acc]");
      if (t) { leer(); b.tipo = t.dataset.tipo; this.pintarCajas(); this.pintarEdicion(cont); }
      if (s) { leer(); b.severidad = b.severidad === s.dataset.sev ? null : s.dataset.sev; this.pintarCajas(); this.pintarEdicion(cont); }
      if (p) { leer(); b.profundidad_cm = Math.max(0, (b.profundidad_cm || 0) + +p.dataset.prof); $("#eProf").value = b.profundidad_cm; }
      if (a?.dataset.acc === "cancelar") { this.flot = nuevo ? null : "detalle"; this.borrador = null; this.pintar(); }
      if (a?.dataset.acc === "guardar") { leer(); this.guardarEdicion(a); }
    };
  }

  async guardarEdicion(boton) {
    const b = this.borrador, nuevo = this.flot === "nuevo";
    const datos = { tipo: b.tipo, largo_cm: b.largo_cm, ancho_cm: b.ancho_cm, profundidad_cm: b.profundidad_cm, severidad: b.severidad };
    boton.disabled = true;
    try {
      const d = nuevo
        ? await api(`/api/recorridos/${this.id}/danos`, { metodo: "POST", datos: { ...datos, fotograma_id: this.foto?.id, caja: b.caja } })
        : await api(`/api/danos/${b.id}`, { metodo: "PUT", datos });
      avisar(nuevo ? `Daño ${d.codigo} registrado` : `Cambios de ${d.codigo} guardados`, "ok");
      this.sel = d.id;
      this.flot = "detalle";
      this.borrador = null;
      this.pendiente = false;
      await this.cargar();
    } catch (e) {
      $("#eError").textContent = e.message;
      boton.disabled = false;
    }
  }

  // -------------------------------------------------- marcado manual (arrastrar un recuadro)
  async iniciarDibujo() {
    if (this.modo !== "camara") this.cambiarModo("camara");
    if (this.mostrandoVivo) {
      // Congela el fotograma en vivo actual y marca sobre él
      try {
        const { fotograma_id } = await api(`/api/recorridos/${this.id}/capturar`, { metodo: "POST" });
        await this.cargar();
        this.fotoIdx = Math.max(0, this.rec.lista_fotogramas.findIndex(f => f.id === fotograma_id));
      } catch (e) { return avisar(esc(e.message), "error"); }
      this.verVivo = false;
      this.pintar();
    }
    if (!this.foto?.imagen) return avisar("Este recorrido no tiene una imagen donde marcar.", "error");
    this.flot = null;
    this.dibujo = { activo: false };
    $("#lienzo").classList.add("dibujando");
    $("#avisoDibujo").classList.remove("oculto");
    this.pintar();
  }

  cancelarDibujo() {
    this.dibujo = null;
    $("#lienzo").classList.remove("dibujando");
    $("#avisoDibujo").classList.add("oculto");
    this.pintarCajas();
    if (this.pendiente) { this.pendiente = false; this.cargar(); }
  }

  puntoRelativo(e) {
    const r = $("#lienzo").getBoundingClientRect();
    return [Math.min(1, Math.max(0, (e.clientX - r.left) / r.width)), Math.min(1, Math.max(0, (e.clientY - r.top) / r.height))];
  }

  dibujoInicio(e) {
    if (!this.dibujo) return;
    e.preventDefault();
    try { $("#lienzo").setPointerCapture(e.pointerId); } catch {}
    this.dibujo = { activo: true, inicio: this.puntoRelativo(e), caja: null };
  }

  dibujoMover(e) {
    if (!this.dibujo?.activo) return;
    const [x0, y0] = this.dibujo.inicio, [x1, y1] = this.puntoRelativo(e);
    this.dibujo.caja = [Math.min(x0, x1), Math.min(y0, y1), Math.abs(x1 - x0), Math.abs(y1 - y0)];
    this.pintarCajas();
  }

  dibujoFin() {
    if (!this.dibujo?.activo) return;
    const caja = this.dibujo.caja;
    if (!caja || caja[2] < 0.01 || caja[3] < 0.01) { this.dibujo.activo = false; return; }
    this.cancelarDibujo();
    this.flot = "nuevo";
    this.sel = null;
    this.borrador = { tipo: "grieta", largo_cm: null, ancho_cm: null, profundidad_cm: null, severidad: null,
      caja: caja.map(v => +v.toFixed(4)) };
    this.pintar();
  }

  // -------------------------------------------------- acciones del recorrido
  async guardarReporte() {
    try {
      const r = await api(`/api/recorridos/${this.id}/reportes`, { metodo: "POST" });
      avisar(`Reporte #${r.id} guardado. <u>Ver reportes</u>`, "ok", () => { location.hash = "#/reportes"; });
    } catch (e) { avisar(esc(e.message), "error"); }
  }

  async procesar(boton) {
    boton.disabled = true;
    boton.textContent = "Analizando…";
    try {
      const r = await api(`/api/recorridos/${this.id}/procesar`, { metodo: "POST" });
      avisar(`Análisis completado: ${r.danos} daño${r.danos === 1 ? "" : "s"} detectado${r.danos === 1 ? "" : "s"}.`, "ok");
      await this.cargar();
    } catch (e) {
      avisar(esc(e.message), "error");
      boton.disabled = false;
      boton.innerHTML = `${ICONO.ia}Analizar con IA`;
    }
  }

  async eliminarRecorrido() {
    const r = this.rec;
    const ok = await confirmar({ titulo: `¿Eliminar el recorrido ${esc(r.codigo)}?`,
      texto: `Se borrarán sus ${r.lista_fotogramas.length} fotogramas y ${r.danos.length} daños. Esta acción no se puede deshacer.` });
    if (!ok) return;
    try {
      await api(`/api/recorridos/${this.id}`, { metodo: "DELETE" });
      avisar(`Recorrido ${esc(r.codigo)} eliminado`, "ok");
      location.hash = "#/recorridos";
    } catch (e) { avisar(esc(e.message), "error"); }
  }
}

// ------------------------------------------------------------------ Mapas
class VistaMapas {
  constructor(cont) {
    this.cont = cont;
    this.filtros = { tipo: "", severidad: "", estado: "", recorrido: "" };
    this.danos = [];
    this.sel = null;
    this.satelite = false;
    cont.innerHTML = `<div class="mapas">
      <section class="mapas-centro">
        <div class="filtros" id="filtros">
          <select class="entrada" data-f="tipo" aria-label="Tipo"><option value="">Todos los tipos</option><option value="bache">Baches</option><option value="grieta">Grietas</option><option value="hundimiento">Hundimientos</option></select>
          <select class="entrada" data-f="severidad" aria-label="Severidad"><option value="">Toda severidad</option><option value="alta">Alta</option><option value="media">Media</option><option value="baja">Baja</option></select>
          <select class="entrada" data-f="estado" aria-label="Estado"><option value="">Todos los estados</option><option value="pendiente">Pendiente</option><option value="validado">Validado</option><option value="asignado">Asignado</option><option value="reparado">Reparado</option></select>
          <select class="entrada" data-f="recorrido" aria-label="Recorrido" id="fRecorrido"><option value="">Todos los recorridos</option></select>
          <span class="total" id="totalMapa"></span>
        </div>
        <div class="mapa-grande"><div id="mapaGrande"></div><span class="motor-mapa" id="motorMapa"></span></div>
      </section>
      <aside class="panel-der" id="panelMapa"></aside>
    </div>`;
    $("#filtros").onchange = e => { const s = e.target.closest("[data-f]"); if (s) { this.filtros[s.dataset.f] = s.value; this.cargar(true); } };
    this.iniciar();
  }

  async iniciar() {
    api("/api/recorridos").then(({ recorridos }) => {
      $("#fRecorrido").innerHTML += recorridos.map(r => `<option value="${r.id}">${esc(r.codigo)} · ${esc(r.nombre)}</option>`).join("");
    }).catch(() => {});
    this.mapa = await Mapas.crear($("#mapaGrande"), { alClic: d => this.seleccionar(d.id) });
    $("#motorMapa").textContent = `Mapa: ${this.mapa.motor}`;
    this.cargar(true);
  }

  destruir() { this.mapa?.destruir(); }

  async cargar(encuadrar) {
    const q = new URLSearchParams(Object.entries(this.filtros).filter(([, v]) => v));
    try { this.danos = (await api(`/api/danos?${q}`)).danos; }
    catch (e) { return avisar(esc(e.message), "error"); }
    if (!this.mapa) return;
    this.mapa.marcar(this.danos);
    if (encuadrar) this.mapa.encuadrar(this.danos);
    $("#totalMapa").textContent = `${this.danos.length} daño${this.danos.length === 1 ? "" : "s"}`;
    if (this.sel && !this.danos.some(d => d.id === this.sel)) this.sel = null;
    this.pintarPanel();
  }

  alMensaje(m) {
    if (m.tipo === "vivo") { this.mapa?.vehiculo(m.lat, m.lon, false); return; }
    if (m.tipo !== "dano") return;
    clearTimeout(this._t);
    this._t = setTimeout(() => this.cargar(false), 400);
  }

  seleccionar(id) {
    this.sel = id;
    this.pintarPanel();
    this.mapa.enfocar(this.danos.find(d => d.id === id));
  }

  pintarPanel() {
    const panel = $("#panelMapa");
    const d = this.danos.find(x => x.id === this.sel);
    if (!d) {
      panel.innerHTML = `<h2>Mapa de daños</h2><p class="sub">Haz clic en un marcador o en la lista para ver su ubicación en Google Maps.</p>
        <hr class="separador"><div class="lista-danos" id="listaMapa">${this.danos.map(x => {
          const c = colorSev(x.severidad);
          return `<button class="item-dano" style="--c:${c}" data-id="${x.id}"><b>${Fmt.tipo(x.tipo)} · ${esc(x.codigo)}</b>
            <span class="conf ${x.origen === "manual" ? "manual" : ""}">${x.origen === "manual" ? "Manual" : Fmt.pct(x.confianza)}</span>
            <span class="meta">${esc(x.recorrido_nombre)}<span class="sep">•</span>${Fmt.estadoDano(x)}</span></button>`;
        }).join("") || `<div class="vacio">No hay daños con estos filtros.</div>`}</div>`;
      $("#listaMapa").onclick = e => { const b = e.target.closest("[data-id]"); if (b) this.seleccionar(+b.dataset.id); };
      return;
    }
    const c = colorSev(d.severidad);
    const mini = d.imagen && d.caja ? `<div style="position:relative;margin-bottom:14px;border-radius:10px;overflow:hidden">
        <img src="${esc(d.imagen)}" alt="Fotograma" style="width:100%;display:block">
        <div class="caja" style="--c:${c};left:${d.caja[0] * 100}%;top:${d.caja[1] * 100}%;width:${d.caja[2] * 100}%;height:${d.caja[3] * 100}%;pointer-events:none"></div></div>` : "";
    panel.innerHTML = `<button class="btn fantasma chico" id="volverLista" style="align-self:flex-start;margin:-6px 0 10px -10px">${ICONO.atras}Volver a la lista</button>
      <h2 style="display:flex;gap:10px;align-items:center"><span class="punto" style="background:${c};width:10px;height:10px"></span>${Fmt.tipo(d.tipo)} · ${esc(d.codigo)}</h2>
      <p class="sub" style="margin-bottom:14px">${esc(d.recorrido_nombre)} · ${esc(d.recorrido_codigo)}</p>
      <iframe class="gmap-embed" src="${GMaps.embed(d, this.satelite)}" loading="lazy" referrerpolicy="no-referrer-when-downgrade" title="Ubicación en Google Maps"></iframe>
      <div class="segmentado" id="tipoMapa" style="margin-bottom:10px"><button data-sat="0" class="${this.satelite ? "" : "activo"}">Mapa</button><button data-sat="1" class="${this.satelite ? "activo" : ""}">Satélite</button></div>
      <div class="botones-mapa">
        <a class="btn primario ancho" href="${GMaps.abrir(d)}" target="_blank" rel="noopener">${ICONO.mapas}Abrir en Google Maps</a>
        <a class="btn" href="${GMaps.street(d)}" target="_blank" rel="noopener">Street View</a>
        <a class="btn" href="${GMaps.ruta(d)}" target="_blank" rel="noopener">Cómo llegar</a>
      </div>
      ${mini}
      <dl class="datos">
        <dt>Severidad</dt><dd style="color:${d.severidad ? c : "inherit"}">${Fmt.severidad(d.severidad)}</dd>
        <dt>Estado</dt><dd><span class="estado-color ${d.estado}">${Fmt.estadoDano(d)}</span></dd>
        <dt>Cuadrilla</dt><dd>${esc(d.cuadrilla || "Sin asignar")}</dd>
        <dt>Ubicación</dt><dd>${Fmt.coord(d.lat, d.lon)}</dd>
        <dt>Zona</dt><dd class="suave">${esc([d.canton, d.provincia].filter(Boolean).join(", ") || "—")}</dd>
        <dt>IP de la zona</dt><dd class="suave">${esc(d.ip_publica || "—")}${d.ip_ciudad ? ` (${esc(d.ip_ciudad)})` : ""}</dd>
        <dt>Registrado</dt><dd>${Fmt.fecha(d.creado)}</dd>
      </dl>
      <a class="btn bloque" href="#/recorridos/${d.recorrido_id}?dano=${d.id}">Abrir en el recorrido</a>`;
    $("#volverLista").onclick = () => { this.sel = null; this.pintarPanel(); };
    $("#tipoMapa").onclick = e => { const b = e.target.closest("[data-sat]"); if (b) { this.satelite = b.dataset.sat === "1"; this.pintarPanel(); } };
  }
}

// ------------------------------------------------------------------ Reportes
class VistaReportes {
  constructor(cont) {
    this.cont = cont;
    cont.innerHTML = `<div class="pagina"><div class="pagina-cab"><div><h1>Reportes</h1>
      <p class="sub">Reportes guardados desde los resultados de cada recorrido · expórtalos a PDF para enviarlos</p></div></div>
      <div class="tabla-reportes" id="listaReportes"><div class="cargando">Cargando…</div></div></div>`;
    this.cargar();
  }

  async cargar() {
    try {
      const { reportes } = await api("/api/reportes");
      const cont = $("#listaReportes");
      cont.innerHTML = reportes.length ? reportes.map(r => `<div class="tarjeta tarjeta-reporte">
        <span class="icono-caja">${ICONO.doc}</span>
        <div class="info"><b>Reporte #${r.id} · ${esc(r.recorrido_nombre || "Recorrido eliminado")}</b>
          <div class="meta">${esc(r.recorrido_codigo || "")}<span class="sep">•</span>Guardado por ${esc(r.autor)}<span class="sep">•</span>${Fmt.fecha(r.creado)}</div>
          <div class="chips"><span class="chip">${r.total} daños</span><span class="chip" style="color:var(--rojo)">${r.altas} severidad alta</span>
            <span class="chip" style="color:var(--verde)">${r.reparados} reparados</span></div></div>
        <button class="btn chico" data-pdf="${r.id}">${ICONO.descargar}Exportar PDF</button>
        ${r.recorrido_id ? `<a class="btn chico fantasma" href="#/recorridos/${r.recorrido_id}">Abrir recorrido</a>` : ""}
        ${Sesion.esAdmin ? `<button class="icono-btn" data-borrar="${r.id}" title="Eliminar reporte" aria-label="Eliminar reporte">${ICONO.basura}</button>` : ""}
      </div>`).join("") : `<div class="vacio">Aún no hay reportes. Abre un recorrido y pulsa <b>Guardar Reporte</b>.</div>`;
      cont.onclick = async e => {
        const pdf = e.target.closest("[data-pdf]"), borrar = e.target.closest("[data-borrar]");
        if (pdf) window.open(`/reporte.html?id=${pdf.dataset.pdf}&imprimir=1`, "_blank");
        if (borrar && await confirmar({ titulo: `¿Eliminar el reporte #${borrar.dataset.borrar}?`, texto: "Los daños y el recorrido no se borran, solo este reporte guardado." })) {
          await api(`/api/reportes/${borrar.dataset.borrar}`, { metodo: "DELETE" });
          this.cargar();
        }
      };
    } catch (e) { avisar(esc(e.message), "error"); }
  }
}

// ------------------------------------------------------------------ Configuración
class VistaConfiguracion {
  constructor(cont) {
    this.cont = cont;
    const u = Sesion.usuario, admin = Sesion.esAdmin;
    cont.innerHTML = `<div class="pagina" style="max-width:1200px"><div class="pagina-cab"><div><h1>Configuración</h1>
      <p class="sub">Cuenta, cuadrillas de reparación, usuarios y estado del sistema</p></div></div>
      <div class="config">
        <section class="tarjeta"><h3>Mi cuenta</h3><p class="sub">Datos de acceso al panel</p>
          <div style="display:flex;gap:14px;align-items:center;margin-bottom:18px"><span class="avatar" style="width:48px;height:48px;font-size:16px">${esc(Fmt.iniciales(u.nombre))}</span>
            <div><b>${esc(u.nombre)}</b><div class="meta">${esc(u.correo)} · ${u.rol === "admin" ? "Administrador" : "Técnico de mantenimiento"}</div></div></div>
          <form id="formClave">
            <label class="campo"><span>Contraseña actual</span><input class="entrada" type="password" name="actual" required autocomplete="current-password"></label>
            <div class="dos-col"><label class="campo"><span>Nueva contraseña</span><input class="entrada" type="password" name="nueva" minlength="6" required autocomplete="new-password"></label>
              <label class="campo"><span>Repetir</span><input class="entrada" type="password" name="repetir" minlength="6" required autocomplete="new-password"></label></div>
            <div class="error-form" id="errClave"></div><button class="btn primario">Cambiar contraseña</button></form>
        </section>
        <section class="tarjeta"><h3>Cuadrillas</h3><p class="sub">Equipos a los que se asignan las reparaciones</p>
          <div class="lista-simple" id="listaCuadrillas"></div>
          ${admin ? `<form class="fila-form" id="formCuadrilla"><input class="entrada" name="nombre" placeholder="Nombre de la cuadrilla" required minlength="2"><button class="btn primario">${ICONO.mas}Agregar</button></form>` : ""}
        </section>
        ${admin ? `<section class="tarjeta"><h3>Usuarios</h3><p class="sub">Personal con acceso al panel</p>
          <div class="lista-simple" id="listaUsuarios"></div>
          <form id="formUsuario">
            <div class="dos-col"><label class="campo"><span>Nombre</span><input class="entrada" name="nombre" required minlength="3"></label>
              <label class="campo"><span>Correo o usuario</span><input class="entrada" name="correo" required></label></div>
            <div class="dos-col"><label class="campo"><span>Rol</span><select class="entrada" name="rol"><option value="tecnico">Técnico de mantenimiento</option><option value="admin">Administrador</option></select></label>
              <label class="campo"><span>Contraseña inicial</span><input class="entrada" name="contrasena" type="password" minlength="6" required autocomplete="new-password"></label></div>
            <div class="error-form" id="errUsuario"></div><button class="btn primario">${ICONO.mas}Crear usuario</button></form>
        </section>` : ""}
        <section class="tarjeta"><h3>Sistema</h3><p class="sub">Estado de la IA, mapas y conexión de los vehículos</p>
          <div class="estado-sistema" id="estadoSistema"><div class="cargando" style="padding:10px">Comprobando…</div></div></section>
      </div></div>`;
    this.enlazar();
    this.cargarCuadrillas();
    if (admin) this.cargarUsuarios();
    this.cargarSistema();
  }

  enlazar() {
    $("#formClave").onsubmit = async e => {
      e.preventDefault();
      const f = new FormData(e.target);
      if (f.get("nueva") !== f.get("repetir")) return ($("#errClave").textContent = "Las contraseñas nuevas no coinciden.");
      try {
        await api("/api/auth/contrasena", { metodo: "PUT", datos: { actual: f.get("actual"), nueva: f.get("nueva") } });
        e.target.reset();
        $("#errClave").textContent = "";
        avisar("Contraseña actualizada", "ok");
      } catch (err) { $("#errClave").textContent = err.message; }
    };
    $("#formCuadrilla")?.addEventListener("submit", async e => {
      e.preventDefault();
      try {
        await api("/api/cuadrillas", { metodo: "POST", datos: { nombre: new FormData(e.target).get("nombre") } });
        e.target.reset();
        this.cargarCuadrillas();
      } catch (err) { avisar(esc(err.message), "error"); }
    });
    $("#formUsuario")?.addEventListener("submit", async e => {
      e.preventDefault();
      try {
        await api("/api/usuarios", { metodo: "POST", datos: Object.fromEntries(new FormData(e.target)) });
        e.target.reset();
        $("#errUsuario").textContent = "";
        avisar("Usuario creado", "ok");
        this.cargarUsuarios();
      } catch (err) { $("#errUsuario").textContent = err.message; }
    });
  }

  async cargarCuadrillas() {
    const { cuadrillas } = await api("/api/cuadrillas");
    const cont = $("#listaCuadrillas");
    cont.innerHTML = cuadrillas.map(c => `<div><span class="punto amarillo"></span><span class="grow">${esc(c.nombre)}</span>
      <span class="meta">${c.pendientes} asignado${c.pendientes === 1 ? "" : "s"}</span>
      ${Sesion.esAdmin ? `<button class="icono-btn" data-borrar="${c.id}" aria-label="Eliminar ${esc(c.nombre)}">${ICONO.basura}</button>` : ""}</div>`).join("")
      || `<div class="meta">No hay cuadrillas.</div>`;
    cont.onclick = async e => {
      const b = e.target.closest("[data-borrar]");
      if (b && await confirmar({ titulo: "¿Eliminar la cuadrilla?", texto: "Los daños ya asignados conservan el nombre de la cuadrilla." })) {
        await api(`/api/cuadrillas/${b.dataset.borrar}`, { metodo: "DELETE" });
        this.cargarCuadrillas();
      }
    };
  }

  async cargarUsuarios() {
    const { usuarios } = await api("/api/usuarios");
    const cont = $("#listaUsuarios");
    cont.innerHTML = usuarios.map(u => `<div><span class="avatar" style="width:30px;height:30px;font-size:11px">${esc(Fmt.iniciales(u.nombre))}</span>
      <span class="grow"><b>${esc(u.nombre)}</b><div class="meta">${esc(u.correo)}</div></span>
      <span class="chip">${u.rol === "admin" ? "Administrador" : "Técnico"}</span>
      ${u.id !== Sesion.usuario.id ? `<button class="icono-btn" data-borrar="${u.id}" aria-label="Eliminar ${esc(u.nombre)}">${ICONO.basura}</button>` : ""}</div>`).join("");
    cont.onclick = async e => {
      const b = e.target.closest("[data-borrar]");
      if (b && await confirmar({ titulo: "¿Eliminar este usuario?", texto: "Ya no podrá ingresar al panel." })) {
        await api(`/api/usuarios/${b.dataset.borrar}`, { metodo: "DELETE" });
        this.cargarUsuarios();
      }
    };
  }

  async cargarSistema() {
    const [estado, config, motor] = await Promise.all([
      api("/api/estado").catch(() => null), api("/api/config").catch(() => ({})), Mapas.motor()]);
    const ia = !estado ? ["rojo", "Servidor no disponible"]
      : estado.yolo && !estado.modo_demo ? ["verde", `YOLO listo con modelo de baches (${esc(estado.clases.join(", "))})`]
      : estado.yolo ? ["amarillo", "YOLO instalado, pero sin modelo de baches: entrena <code>models/baches.pt</code> con <code>entrenar.py</code>"]
      : ["amarillo", "YOLO no instalado: Unity usa el modo simulado. Instala <code>ultralytics</code> y <code>opencv-python</code> para detección real."];
    const mapa = config.google_maps_key && motor === "google" ? ["verde", "Google Maps activo (API key configurada)"]
      : ["amarillo", "OpenStreetMap en los mapas grandes · Google Maps en el detalle de cada daño (sin API key)"];
    $("#estadoSistema").innerHTML = `
      <div><span class="punto ${ia[0]}" style="margin-top:6px"></span><span><b>Inteligencia artificial</b><br>${ia[1]}</span></div>
      <div><span class="punto ${mapa[0]}" style="margin-top:6px"></span><span><b>Mapas</b><br>${mapa[1]}</span></div>
      <div><span class="punto ${App.ws?.readyState === 1 ? "verde" : "amarillo"}" style="margin-top:6px"></span><span><b>Tiempo real</b><br>${App.ws?.readyState === 1 ? "Conectado: los daños nuevos aparecen al instante" : "Reconectando…"}</span></div>
      ${Sesion.esAdmin ? `<div><span class="punto azul" style="margin-top:6px"></span><span><b>Código de administrador</b><br>
        Para registrar nuevas cuentas de administrador: <code id="codigoAdmin">······</code>
        <button class="btn chico fantasma" id="btnCodigo" style="margin-left:6px">Generar otro</button></span></div>` : ""}
      <div><span class="punto azul" style="margin-top:6px"></span><span><b>Vehículos</b><br>Unity y <code>detectar_camara.py</code> envían sus detecciones a <code>http://${esc(location.host)}/api/baches</code> y <code>/api/detectar</code>.
        ${Sesion.esAdmin ? `<br>Token de dispositivo (campo <i>Token Dispositivo</i> en Unity, <code>--token</code> en los scripts): <code id="tokenDispositivo">······</code>
        <button class="btn chico fantasma" id="btnToken" style="margin-left:6px">Generar otro</button>` : ""}</span></div>`;
    if (Sesion.esAdmin) {
      const mostrar = async regenerar => { $("#codigoAdmin").textContent = (await api(`/api/admin/codigo${regenerar ? "?regenerar=true" : ""}`)).codigo; };
      mostrar(false);
      $("#btnCodigo").onclick = async () => {
        if (await confirmar({ titulo: "¿Generar un código nuevo?", texto: "El código anterior dejará de servir para registrar administradores.", boton: "Generar" })) mostrar(true);
      };
      const mostrarToken = async regenerar => { $("#tokenDispositivo").textContent = (await api(`/api/admin/token-dispositivo${regenerar ? "?regenerar=true" : ""}`)).token; };
      mostrarToken(false);
      $("#btnToken").onclick = async () => {
        if (await confirmar({ titulo: "¿Generar un token nuevo?", texto: "Unity y las cámaras dejarán de poder enviar datos hasta que les pongas el token nuevo.", boton: "Generar" })) mostrarToken(true);
      };
    }
  }
}

App.iniciar();

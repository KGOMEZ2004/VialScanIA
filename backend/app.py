"""
VialScan AI — servidor del panel de mantenimiento vial.

- Login con roles (admin / técnico) y sesiones.
- Recorridos -> fotogramas -> daños (bache, grieta, hundimiento) con recuadro, severidad, estado y cuadrilla.
- Recibe detecciones de Unity / cámara (YOLO) y las agrupa en recorridos, con provincia, cantón e IP.
- Reportes guardados y exportación a PDF (vista imprimible).
- Tiempo real por WebSocket.

Ejecutar:  uvicorn app:app --host 0.0.0.0 --port 8000
"""
import asyncio
import base64
import json
import os
import re
import secrets
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Literal

from fastapi import (Depends, FastAPI, File, Form, Header, HTTPException, Query, Request, UploadFile, WebSocket,
                     WebSocketDisconnect)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import db
import escena_demo
import geo_ecuador as geo

RAIZ = Path(__file__).resolve().parent
WEB = RAIZ.parent / "web"
RADIO_DUPLICADO_M = 8          # un mismo daño no se registra dos veces dentro de este radio
MINUTOS_RECORRIDO_ACTIVO = 10  # tras este tiempo sin detecciones, el recorrido del vehículo se da por completado
DURACION_SESION = timedelta(hours=12)

TIPOS_SOLO_MANUAL = {"grieta"}   # la IA no los registra: los marca una persona en el panel
SEVERIDADES = {"leve": "baja", "moderado": "media", "grave": "alta", "baja": "baja", "media": "media", "alta": "alta"}


def clave_google_maps() -> str:
    """API key de Google Maps: variable GOOGLE_MAPS_API_KEY o archivo backend/google_maps_key.txt (opcional)."""
    archivo = RAIZ / "google_maps_key.txt"
    clave = os.getenv("GOOGLE_MAPS_API_KEY", "").strip()
    if not clave and archivo.exists():
        lineas = [l.strip() for l in archivo.read_text(encoding="utf-8-sig").splitlines()]
        clave = next((l for l in lineas if l and not l.startswith("#") and l != "PEGA_AQUI_TU_API_KEY"), "")
    return clave


app = FastAPI(title="VialScan AI")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
db.iniciar()


@app.middleware("http")
async def sin_cache_para_la_web(request: Request, call_next):
    """El navegador revalida HTML/JS/CSS en cada carga: tras actualizar el proyecto no se queda con la versión vieja."""
    respuesta = await call_next(request)
    if not request.url.path.startswith(("/api/", "/capturas/")):
        respuesta.headers["Cache-Control"] = "no-cache"
    return respuesta


# ================================================================ sesiones y permisos
def usuario_actual(authorization: str | None = Header(None)) -> dict:
    token = (authorization or "").removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(401, "Inicia sesión")
    with db.conectar() as con:
        u = con.execute(
            "SELECT u.id, u.nombre, u.correo, u.cargo, u.rol FROM sesiones s JOIN usuarios u ON u.id = s.usuario_id "
            "WHERE s.token=? AND s.expira > ?", (token, db.ahora())).fetchone()
    if not u:
        raise HTTPException(401, "Sesión expirada")
    return dict(u)


def solo_admin(u: dict = Depends(usuario_actual)) -> dict:
    if u["rol"] != "admin":
        raise HTTPException(403, "Solo un administrador puede hacer esto")
    return u


def dispositivo_autorizado(x_token_dispositivo: str | None = Header(None)) -> None:
    """Unity y las cámaras no inician sesión: se identifican con el token de dispositivo (Configuración > Sistema)."""
    if not x_token_dispositivo:
        raise HTTPException(401, "Falta la cabecera X-Token-Dispositivo")
    with db.conectar() as con:
        valido = secrets.compare_digest(x_token_dispositivo.strip(), db.token_dispositivo(con))
    if not valido:
        raise HTTPException(401, "Token de dispositivo incorrecto")


USUARIO_VALIDO = r"^[^\s]{3,80}$"   # correo institucional o nombre de usuario (sin espacios)


class Login(BaseModel):
    correo: str
    contrasena: str
    rol: Literal["admin", "tecnico"]


class Registro(BaseModel):
    nombre: str = Field(min_length=3, max_length=80)
    correo: str = Field(pattern=USUARIO_VALIDO)
    contrasena: str = Field(min_length=6)
    rol: Literal["admin", "tecnico"] = "tecnico"
    codigo_admin: str | None = None


def abrir_sesion(con, u) -> dict:
    token = secrets.token_urlsafe(32)
    con.execute("INSERT INTO sesiones (token, usuario_id, expira) VALUES (?,?,?)",
                (token, u["id"], db.ahora(DURACION_SESION)))
    return {"token": token, "usuario": {k: u[k] for k in ("id", "nombre", "correo", "cargo", "rol")}}


@app.post("/api/auth/registro")
def registro(datos: Registro):
    """Crear cuenta desde el login. Administrador solo con el código de administrador."""
    with db.conectar() as con:
        if datos.rol == "admin" and (datos.codigo_admin or "").strip() != db.codigo_admin(con):
            raise HTTPException(403, "El código de administrador no es correcto. Pídeselo a un administrador.")
        if con.execute("SELECT 1 FROM usuarios WHERE correo=?", (datos.correo.strip().lower(),)).fetchone():
            raise HTTPException(400, "Ya existe una cuenta con ese correo o usuario")
        uid = db.crear_usuario(con, datos.nombre.strip(), datos.correo, datos.rol, datos.contrasena)
        return abrir_sesion(con, con.execute("SELECT * FROM usuarios WHERE id=?", (uid,)).fetchone())


@app.post("/api/auth/login")
def login(datos: Login):
    with db.conectar() as con:
        u = con.execute("SELECT * FROM usuarios WHERE correo=?", (datos.correo.strip().lower(),)).fetchone()
        if not u or not db.verificar_contrasena(datos.contrasena, u["sal"], u["hash"]):
            raise HTTPException(401, "Correo o contraseña incorrectos")
        if u["rol"] != datos.rol:
            nombre_rol = "Administrador" if u["rol"] == "admin" else "Técnico de mantenimiento"
            raise HTTPException(403, f"Esta cuenta tiene el rol «{nombre_rol}». Selecciónalo para ingresar.")
        return abrir_sesion(con, u)


@app.post("/api/auth/logout")
def logout(authorization: str | None = Header(None)):
    with db.conectar() as con:
        con.execute("DELETE FROM sesiones WHERE token=?", ((authorization or "").removeprefix("Bearer ").strip(),))
    return {"ok": True}


@app.get("/api/auth/yo")
def yo(u: dict = Depends(usuario_actual)):
    return u


class CambioContrasena(BaseModel):
    actual: str
    nueva: str = Field(min_length=6)


@app.put("/api/auth/contrasena")
def cambiar_contrasena(datos: CambioContrasena, u: dict = Depends(usuario_actual)):
    with db.conectar() as con:
        fila = con.execute("SELECT sal, hash FROM usuarios WHERE id=?", (u["id"],)).fetchone()
        if not db.verificar_contrasena(datos.actual, fila["sal"], fila["hash"]):
            raise HTTPException(400, "La contraseña actual no es correcta")
        sal, h = db.hash_contrasena(datos.nueva)
        con.execute("UPDATE usuarios SET sal=?, hash=? WHERE id=?", (sal, h, u["id"]))
    return {"ok": True}


# ================================================================ tiempo real
class Conexiones:
    def __init__(self):
        self.activas: set[WebSocket] = set()

    async def emitir(self, mensaje: dict):
        for ws in list(self.activas):
            try:
                await ws.send_json(mensaje)
            except Exception:
                self.activas.discard(ws)


conexiones = Conexiones()


@app.websocket("/ws")
async def ws_tiempo_real(ws: WebSocket, token: str = ""):
    with db.conectar() as con:
        valido = con.execute("SELECT 1 FROM sesiones WHERE token=? AND expira > ?", (token, db.ahora())).fetchone()
    if not valido:
        await ws.close(code=4401)
        return
    await ws.accept()
    conexiones.activas.add(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        conexiones.activas.discard(ws)


# ================================================================ YOLO (carga perezosa)
_detector = None


def detector():
    global _detector
    if _detector is None:
        from yolo_detector import DetectorBaches
        _detector = DetectorBaches()
    return _detector


@app.get("/api/estado")
async def estado():
    """Indica si YOLO está listo y si tiene un modelo de baches real (o está en modo demo)."""
    try:
        d = await asyncio.to_thread(detector)
        return {"yolo": True, "modo_demo": d.modo_demo, "clases": list(d.modelo.names.values())}
    except Exception as e:
        return {"yolo": False, "modo_demo": True, "error": f"{type(e).__name__}: {e}"}


@app.get("/api/config")
def config():
    return {"google_maps_key": clave_google_maps()}


@app.get("/api/escena.svg")
def escena(v: int = 0):
    """Ilustración de la calle (login y fotogramas de ejemplo)."""
    return Response(escena_demo.escena_svg(v), media_type="image/svg+xml",
                    headers={"Cache-Control": "public, max-age=86400"})


# ================================================================ utilidades de registro
def ip_de(request: Request) -> str:
    reenviada = request.headers.get("x-forwarded-for")
    return reenviada.split(",")[0].strip() if reenviada else request.client.host


def guardar_imagen(datos: bytes, ext: str = "jpg") -> str:
    nombre = f"{datetime.now():%Y%m%d_%H%M%S}_{uuid.uuid4().hex[:6]}.{ext}"
    (db.CAPTURAS / nombre).write_bytes(datos)
    return f"/capturas/{nombre}"


def tipo_desde_clase(clase: str | None) -> str:
    c = (clase or "").lower()
    if any(p in c for p in ("crack", "grieta")):
        return "grieta"
    if any(p in c for p in ("hundimiento", "depression", "sink", "subsid")):
        return "hundimiento"
    return "bache"


def nombre_recorrido(zona: dict, fuente: str) -> str:
    if zona.get("via"):
        return f"{zona['via']} – {zona.get('sector') or zona.get('canton') or zona.get('provincia')}"
    return f"Recorrido {fuente} – {zona.get('canton') or zona.get('provincia')} {datetime.now():%d/%m %H:%M}"


def cerrar_recorridos_inactivos(con):
    limite = db.ahora(timedelta(minutes=-MINUTOS_RECORRIDO_ACTIVO))
    con.execute("UPDATE recorridos SET estado='completado' WHERE estado='en_proceso' AND origen_clave IS NOT NULL "
                "AND actualizado < ?", (limite,))


def recorrido_activo(con, fuente: str, ip: dict, lat: float, lon: float, zona: dict, sesion: str | None = None) -> int:
    """Recorrido en curso del mismo vehículo y sesión (cada Play de Unity es una sesión), o uno nuevo."""
    # "unity-simulado", "unity-yolo" y "unity-vivo" son el mismo vehículo
    dispositivo = f"{fuente.split('-')[0]}|{ip.get('ip_cliente')}"
    clave = f"{dispositivo}|{sesion}" if sesion else dispositivo
    cerrar_recorridos_inactivos(con)
    r = con.execute("SELECT id FROM recorridos WHERE origen_clave=? AND estado='en_proceso' ORDER BY id DESC LIMIT 1",
                    (clave,)).fetchone()
    if r:
        return r["id"]
    # Empieza una sesión nueva: los recorridos anteriores de este vehículo quedan completados
    con.execute("UPDATE recorridos SET estado='completado' WHERE estado='en_proceso' AND (origen_clave=? OR origen_clave LIKE ?)",
                (dispositivo, f"{dispositivo}|%"))
    return con.execute(
        """INSERT INTO recorridos (codigo, nombre, fuente, origen_clave, estado, creado, actualizado, lat, lon,
               provincia, canton, ip_cliente, ip_publica, ip_ciudad, ip_region, ip_isp)
           VALUES (?,?,?,?,'en_proceso',?,?,?,?,?,?,?,?,?,?,?)""",
        (db.nuevo_codigo_recorrido(con), nombre_recorrido(zona, fuente), fuente, clave, db.ahora(), db.ahora(),
         lat, lon, zona.get("provincia"), zona.get("canton"), ip.get("ip_cliente"), ip.get("ip_publica"),
         ip.get("ip_ciudad"), ip.get("ip_region"), ip.get("ip_isp"))).lastrowid


def insertar_dano(con, recorrido_id, fotograma_id, d: dict, lat, lon, ubicacion_por, zona: dict, ip: dict,
                  origen="ia", autor="IA") -> int:
    caja = d.get("caja") or [None] * 4
    return con.execute(
        """INSERT INTO danos (recorrido_id, fotograma_id, tipo, origen, confianza, bx, by, bw, bh,
               largo_cm, ancho_cm, profundidad_cm, severidad, estado, lat, lon, ubicacion_por,
               provincia, canton, direccion, ip_cliente, ip_publica, ip_ciudad, ip_region, ip_isp,
               creado, actualizado, creado_por)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,'pendiente',?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (recorrido_id, fotograma_id, d.get("tipo", "bache"), origen, d.get("confianza"), *caja,
         d.get("largo_cm"), d.get("ancho_cm"), d.get("profundidad_cm"), SEVERIDADES.get(d.get("severidad") or "", None),
         lat, lon, ubicacion_por, zona.get("provincia"), zona.get("canton"), zona.get("direccion"),
         ip.get("ip_cliente"), ip.get("ip_publica"), ip.get("ip_ciudad"), ip.get("ip_region"), ip.get("ip_isp"),
         db.ahora(), db.ahora(), autor)).lastrowid


def registrar_deteccion(detecciones: list[dict], lat, lon, fuente: str, ip_cliente: str,
                        imagen: str | None, velocidad: float | None, sesion: str | None = None) -> dict:
    """Registra lo que envía un vehículo (Unity / cámara). Devuelve el daño principal y si era duplicado."""
    ip = geo.info_ip(ip_cliente)
    ubicacion_por = "gps"
    if lat is None or lon is None:
        lat, lon, ubicacion_por = ip.get("ip_lat"), ip.get("ip_lon"), "ip"
        if lat is None:
            raise HTTPException(400, "Sin coordenadas GPS y no se pudo geolocalizar la IP")
    if not geo.dentro_de_ecuador(lat, lon):
        raise HTTPException(400, f"Coordenadas fuera de Ecuador: {lat}, {lon}")

    detecciones = [d for d in detecciones if d.get("tipo") not in TIPOS_SOLO_MANUAL]
    if not detecciones:
        raise HTTPException(422, "Las grietas no se registran automáticamente: márcalas a mano en el panel")
    principal = max(detecciones, key=lambda d: d.get("confianza") or 0)
    with db.conectar() as con:
        # El mismo daño visto otra vez: solo suma un reporte
        for f in con.execute("SELECT * FROM danos WHERE abs(lat-?)<0.001 AND abs(lon-?)<0.001 AND estado!='reparado'",
                             (lat, lon)):
            if geo.distancia_m(lat, lon, f["lat"], f["lon"]) <= RADIO_DUPLICADO_M:
                con.execute("UPDATE danos SET reportes=reportes+1, confianza=max(coalesce(confianza,0),?), actualizado=? "
                            "WHERE id=?", (principal.get("confianza") or 0, db.ahora(), f["id"]))
                con.execute("UPDATE recorridos SET actualizado=? WHERE id=?", (db.ahora(), f["recorrido_id"]))
                d = con.execute("SELECT * FROM danos WHERE id=?", (f["id"],)).fetchone()
                return {"dano": db.dano_json(d), "duplicado": True, "nuevos": []}

        zona = geo.zona_desde_coordenadas(lat, lon)
        rid = recorrido_activo(con, fuente, ip, lat, lon, zona, sesion)
        fid = con.execute(
            "INSERT INTO fotogramas (recorrido_id, imagen, lat, lon, velocidad, fecha) VALUES (?,?,?,?,?,?)",
            (rid, imagen, lat, lon, velocidad, db.ahora())).lastrowid
        nuevos = [insertar_dano(con, rid, fid, d, lat, lon, ubicacion_por, zona, ip, autor=fuente) for d in detecciones]
        con.execute("UPDATE recorridos SET actualizado=?, lat=?, lon=? WHERE id=?", (db.ahora(), lat, lon, rid))
        filas = [db.dano_json(con.execute("SELECT * FROM danos WHERE id=?", (i,)).fetchone()) for i in nuevos]
    principal_json = max(filas, key=lambda d: d.get("confianza") or 0)
    return {"dano": principal_json, "duplicado": False, "nuevos": filas}


def respuesta_compatible(res: dict) -> dict:
    """Formato de respuesta que esperan Unity y detectar_camara.py (versión anterior de la API)."""
    d = res["dano"]
    return {**d, "duplicado": res["duplicado"], "id": d["id"],
            "severidad": {"baja": "leve", "media": "moderado", "alta": "grave"}.get(d["severidad"], d["severidad"])}


async def avisar_danos(res: dict):
    if res["duplicado"]:
        await conexiones.emitir({"tipo": "dano", "accion": "actualizado", "dano": res["dano"]})
    for d in res["nuevos"]:
        await conexiones.emitir({"tipo": "dano", "accion": "nuevo", "dano": d})


# ================================================================ API de dispositivos (Unity, cámara, simulador)
class ReporteVehiculo(BaseModel):
    lat: float | None = Field(None, description="Latitud GPS; si falta se usa la ubicación de la IP")
    lon: float | None = None
    confianza: float = 1.0
    severidad: str = "moderado"
    tipo: str = "bache"
    fuente: str = "camara"
    imagen_b64: str | None = None
    velocidad: float | None = Field(None, description="km/h")
    # Recuadro normalizado (0-1) del daño dentro de la imagen
    bx: float | None = None
    by: float | None = None
    bw: float | None = None
    bh: float | None = None
    largo_cm: float | None = None
    ancho_cm: float | None = None
    sesion: str | None = Field(None, max_length=64, description="Identificador de la sesión (cada Play de Unity)")


@app.post("/api/baches", dependencies=[Depends(dispositivo_autorizado)])
async def recibir_reporte(rep: ReporteVehiculo, request: Request):
    imagen = guardar_imagen(base64.b64decode(rep.imagen_b64)) if rep.imagen_b64 else None
    caja = [rep.bx, rep.by, rep.bw, rep.bh] if None not in (rep.bx, rep.by, rep.bw, rep.bh) else None
    det = {"tipo": tipo_desde_clase(rep.tipo), "confianza": rep.confianza, "severidad": rep.severidad,
           "caja": caja, "largo_cm": rep.largo_cm, "ancho_cm": rep.ancho_cm}
    res = await asyncio.to_thread(registrar_deteccion, [det], rep.lat, rep.lon, rep.fuente, ip_de(request),
                                  imagen, rep.velocidad, rep.sesion)
    await avisar_danos(res)
    return respuesta_compatible(res)


@app.get("/api/baches", dependencies=[Depends(dispositivo_autorizado)])
def listar_para_dispositivos():
    """Lista simple de daños no reparados (minimapa de Unity)."""
    with db.conectar() as con:
        filas = con.execute("SELECT * FROM danos WHERE estado!='reparado' ORDER BY id DESC").fetchall()
    sev = {"baja": "leve", "media": "moderado", "alta": "grave"}
    return {"baches": [{**db.dano_json(f), "severidad": sev.get(f["severidad"], "moderado"),
                        "confianza": f["confianza"] or 1.0, "fuente": f["creado_por"], "fecha": f["creado"]}
                       for f in filas]}


@app.post("/api/detectar", dependencies=[Depends(dispositivo_autorizado)])
async def detectar_frame(
    request: Request,
    imagen: UploadFile = File(...),
    lat: float | None = Form(None),
    lon: float | None = Form(None),
    velocidad: float | None = Form(None),
    fuente: str = Form("unity"),
    sesion: str | None = Form(None),
):
    """Recibe un fotograma desde Unity u otra cámara, corre YOLO y registra los daños."""
    import cv2
    import numpy as np

    datos = await imagen.read()
    frame = cv2.imdecode(np.frombuffer(datos, np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(400, "Imagen inválida")
    alto, ancho = frame.shape[:2]

    t0 = time.perf_counter()
    detecciones = await asyncio.to_thread(detector().detectar, frame)
    ms = round((time.perf_counter() - t0) * 1000)

    bache = None
    dets = [{"tipo": tipo_desde_clase(d["clase"]), "confianza": d["confianza"], "severidad": d["severidad"],
             "caja": [d["x1"] / ancho, d["y1"] / alto, (d["x2"] - d["x1"]) / ancho, (d["y2"] - d["y1"]) / alto]}
            for d in detecciones]
    dets = [d for d in dets if d["tipo"] not in TIPOS_SOLO_MANUAL]
    if dets:
        res = await asyncio.to_thread(registrar_deteccion, dets, lat, lon, fuente, ip_de(request),
                                      guardar_imagen(datos), velocidad, sesion)
        await avisar_danos(res)
        bache = respuesta_compatible(res)
    return {"detecciones": detecciones, "ms": ms, "bache": bache, "ancho": ancho, "alto": alto}


# ================================================================ transmisión en vivo (Unity -> panel web)
SEGUNDOS_EN_VIVO = 8
VIVO: dict[int, dict] = {}          # recorrido_id -> último fotograma en vivo
_vivo_dispositivos: dict[str, dict] = {}


def en_vivo(rid: int) -> bool:
    v = VIVO.get(rid)
    return bool(v) and time.time() - v["t"] < SEGUNDOS_EN_VIVO


def _recorrido_para_vivo(fuente: str, ip_cliente: str, lat: float, lon: float, sesion: str | None) -> int:
    """Recorrido activo del vehículo (lo crea si hace falta). Se cachea para no consultar la IP en cada fotograma."""
    clave = f"{fuente.split('-')[0]}|{ip_cliente}|{sesion}"
    cache = _vivo_dispositivos.get(clave)
    with db.conectar() as con:
        if cache and time.time() - cache["t"] < 60:
            r = con.execute("SELECT estado FROM recorridos WHERE id=?", (cache["rid"],)).fetchone()
            if r and r["estado"] == "en_proceso":
                return cache["rid"]
    ip = geo.info_ip(ip_cliente)
    zona = geo.zona_desde_coordenadas(lat, lon)
    with db.conectar() as con:
        rid = recorrido_activo(con, fuente, ip, lat, lon, zona, sesion)
    _vivo_dispositivos[clave] = {"rid": rid, "t": time.time()}
    return rid


def _guardar_posicion(rid: int, lat: float, lon: float, velocidad: float | None):
    with db.conectar() as con:
        ultimo = con.execute("SELECT fecha FROM ruta WHERE recorrido_id=? ORDER BY id DESC LIMIT 1", (rid,)).fetchone()
        if not ultimo or ultimo["fecha"] < db.ahora(timedelta(seconds=-3)):
            con.execute("INSERT INTO ruta (recorrido_id, lat, lon, velocidad, fecha) VALUES (?,?,?,?,?)",
                        (rid, lat, lon, velocidad, db.ahora()))
            con.execute("UPDATE recorridos SET actualizado=?, lat=?, lon=? WHERE id=?", (db.ahora(), lat, lon, rid))


@app.post("/api/vivo", dependencies=[Depends(dispositivo_autorizado)])
async def recibir_vivo(
    request: Request,
    imagen: UploadFile = File(...),
    lat: float = Form(...),
    lon: float = Form(...),
    velocidad: float | None = Form(None),
    fuente: str = Form("unity-vivo"),
    detecciones: str = Form("[]"),
    sesion: str | None = Form(None),
):
    """Fotograma en vivo del vehículo (no se guarda en disco): el panel lo muestra en 'Cámara' mientras conduce."""
    if not geo.dentro_de_ecuador(lat, lon):
        raise HTTPException(400, "Coordenadas fuera de Ecuador")
    try:
        cajas = [d for d in json.loads(detecciones) if isinstance(d, dict)][:30]
    except ValueError:
        cajas = []
    rid = await asyncio.to_thread(_recorrido_para_vivo, fuente, ip_de(request), lat, lon, sesion)
    VIVO[rid] = {"imagen": await imagen.read(), "t": time.time(), "lat": lat, "lon": lon, "velocidad": velocidad,
                 "detecciones": cajas}
    await asyncio.to_thread(_guardar_posicion, rid, lat, lon, velocidad)
    await conexiones.emitir({"tipo": "vivo", "recorrido_id": rid, "lat": lat, "lon": lon, "velocidad": velocidad,
                             "detecciones": cajas, "t": VIVO[rid]["t"]})
    return {"recorrido_id": rid}


@app.post("/api/recorridos/{rid}/capturar")
async def capturar_vivo(rid: int, u: dict = Depends(usuario_actual)):
    """Guarda el fotograma en vivo actual como fotograma del recorrido (para marcar un daño a mano)."""
    v = VIVO.get(rid)
    if not v or not en_vivo(rid):
        raise HTTPException(409, "Este recorrido no está transmitiendo en vivo")
    ruta = guardar_imagen(v["imagen"])
    with db.conectar() as con:
        fid = con.execute(
            "INSERT INTO fotogramas (recorrido_id, imagen, lat, lon, velocidad, fecha, procesado) VALUES (?,?,?,?,?,?,1)",
            (rid, ruta, v["lat"], v["lon"], v["velocidad"], db.ahora())).lastrowid
    await conexiones.emitir({"tipo": "recorrido", "accion": "actualizado", "id": rid})
    return {"fotograma_id": fid}


@app.get("/api/vivo/{rid}.jpg")
def imagen_vivo(rid: int, u: dict = Depends(usuario_actual)):
    v = VIVO.get(rid)
    if not v:
        raise HTTPException(404, "Sin transmisión en vivo")
    return Response(v["imagen"], media_type="image/jpeg", headers={"Cache-Control": "no-store"})


# ================================================================ API del panel: recorridos
def resumen_recorrido(con, r) -> dict:
    d = dict(r)
    d["en_vivo"] = en_vivo(r["id"])
    c = con.execute(
        "SELECT count(*) total, sum(severidad='alta') altas, sum(estado='reparado') reparados FROM danos "
        "WHERE recorrido_id=?", (r["id"],)).fetchone()
    d.update(total_danos=c["total"], danos_altos=c["altas"] or 0, reparados=c["reparados"] or 0,
             sin_procesar=con.execute("SELECT count(*) FROM fotogramas WHERE recorrido_id=? AND procesado=0",
                                      (r["id"],)).fetchone()[0],
             fotogramas=con.execute("SELECT count(*) FROM fotogramas WHERE recorrido_id=?", (r["id"],)).fetchone()[0])
    d.pop("origen_clave", None)
    return d


def detalle_recorrido(con, rid: int) -> dict:
    r = con.execute("SELECT * FROM recorridos WHERE id=?", (rid,)).fetchone()
    if not r:
        raise HTTPException(404, "Recorrido no encontrado")
    datos = resumen_recorrido(con, r)
    datos["lista_fotogramas"] = [dict(f) for f in con.execute(
        "SELECT * FROM fotogramas WHERE recorrido_id=? ORDER BY fecha, id", (rid,))]
    datos["danos"] = [db.dano_json(f) for f in con.execute(
        "SELECT * FROM danos WHERE recorrido_id=? ORDER BY id", (rid,))]
    datos["ruta"] = [dict(f) for f in con.execute(
        "SELECT lat, lon, velocidad, fecha FROM ruta WHERE recorrido_id=? ORDER BY id", (rid,))]
    v = VIVO.get(rid)
    datos["vivo"] = {k: v[k] for k in ("lat", "lon", "velocidad", "detecciones", "t")} if datos["en_vivo"] else None
    return datos


@app.get("/api/recorridos")
def listar_recorridos(u: dict = Depends(usuario_actual)):
    with db.conectar() as con:
        cerrar_recorridos_inactivos(con)
        filas = con.execute("SELECT * FROM recorridos ORDER BY creado DESC, id DESC").fetchall()
        return {"recorridos": [resumen_recorrido(con, r) for r in filas]}


@app.get("/api/recorridos/{rid}")
def ver_recorrido(rid: int, u: dict = Depends(usuario_actual)):
    with db.conectar() as con:
        cerrar_recorridos_inactivos(con)
        return detalle_recorrido(con, rid)


@app.post("/api/recorridos")
async def subir_recorrido(
    nombre: str = Form(...),
    lat: float = Form(...),
    lon: float = Form(...),
    imagenes: list[UploadFile] = File(...),
    u: dict = Depends(usuario_actual),
):
    """Crea un recorrido a partir de fotos (queda 'Sin procesar' hasta analizarlo con la IA)."""
    if not geo.dentro_de_ecuador(lat, lon):
        raise HTTPException(400, "Las coordenadas deben estar en Ecuador")
    rutas = []
    for img in imagenes:
        ext = (Path(img.filename or "").suffix.lstrip(".") or "jpg").lower()
        if ext not in ("jpg", "jpeg", "png", "webp"):
            raise HTTPException(400, f"Formato no permitido: {img.filename}")
        rutas.append(guardar_imagen(await img.read(), ext))
    zona = await asyncio.to_thread(geo.zona_desde_coordenadas, lat, lon)
    with db.conectar() as con:
        rid = con.execute(
            "INSERT INTO recorridos (codigo, nombre, fuente, estado, creado, actualizado, lat, lon, provincia, canton) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (db.nuevo_codigo_recorrido(con), nombre.strip(), f"subido por {u['nombre']}", "pendiente", db.ahora(),
             db.ahora(), lat, lon, zona.get("provincia"), zona.get("canton"))).lastrowid
        for ruta in rutas:
            con.execute("INSERT INTO fotogramas (recorrido_id, imagen, lat, lon, fecha, procesado) VALUES (?,?,?,?,?,0)",
                        (rid, ruta, lat, lon, db.ahora()))
    await conexiones.emitir({"tipo": "recorrido", "accion": "nuevo", "id": rid})
    return {"id": rid}


def posicion_adelante(ruta, lat, lon, j: int) -> tuple[float, float]:
    """Los daños de un fotograma están delante de la cámara: se ubican sobre la ruta GPS, ~50 m + 75 m por daño."""
    if len(ruta) < 2 or lat is None:
        return lat, lon
    i = min(range(len(ruta)), key=lambda k: (ruta[k]["lat"] - lat) ** 2 + (ruta[k]["lon"] - lon) ** 2)
    p = ruta[min(i + 2 + 3 * j, len(ruta) - 1)]
    return p["lat"], p["lon"]


def _analizar_fotograma(f) -> list[dict]:
    """Daños de un fotograma: escena de ejemplo (conocidos) o YOLO para fotos reales."""
    m = re.search(r"demo_v(\d+)\.svg$", f["imagen"] or "")
    if m:
        return escena_demo.danos_detectables(int(m.group(1)))
    import cv2
    ruta = db.CAPTURAS / Path(f["imagen"]).name
    frame = cv2.imread(str(ruta))
    if frame is None:
        return []
    alto, ancho = frame.shape[:2]
    return [{"tipo": tipo_desde_clase(d["clase"]), "confianza": d["confianza"], "severidad": d["severidad"],
             "caja": [d["x1"] / ancho, d["y1"] / alto, (d["x2"] - d["x1"]) / ancho, (d["y2"] - d["y1"]) / alto]}
            for d in detector().detectar(frame)]


@app.post("/api/recorridos/{rid}/procesar")
async def procesar_recorrido(rid: int, u: dict = Depends(usuario_actual)):
    """Analiza con la IA los fotogramas pendientes del recorrido."""
    with db.conectar() as con:
        r = con.execute("SELECT * FROM recorridos WHERE id=?", (rid,)).fetchone()
        if not r:
            raise HTTPException(404, "Recorrido no encontrado")
        pendientes = con.execute("SELECT * FROM fotogramas WHERE recorrido_id=? AND procesado=0", (rid,)).fetchall()
    resultados = []
    for f in pendientes:
        try:
            resultados.append((f, await asyncio.to_thread(_analizar_fotograma, f)))
        except ImportError:
            raise HTTPException(503, "La IA (YOLO) no está instalada en el servidor. Instala 'ultralytics' y 'opencv-python'.")
    zona = {"provincia": r["provincia"], "canton": r["canton"], "direccion": None}
    with db.conectar() as con:
        ruta = con.execute("SELECT lat, lon FROM ruta WHERE recorrido_id=? ORDER BY id", (rid,)).fetchall()
        for f, dets in resultados:
            for j, d in enumerate(x for x in dets if x["tipo"] not in TIPOS_SOLO_MANUAL):
                lat, lon = posicion_adelante(ruta, f["lat"], f["lon"], j)
                insertar_dano(con, rid, f["id"], d, lat, lon, "gps", zona, {}, autor="IA")
            con.execute("UPDATE fotogramas SET procesado=1 WHERE id=?", (f["id"],))
        con.execute("UPDATE recorridos SET estado='completado', actualizado=? WHERE id=?", (db.ahora(), rid))
    await conexiones.emitir({"tipo": "recorrido", "accion": "actualizado", "id": rid})
    return {"ok": True, "danos": sum(len(d) for _, d in resultados)}


@app.delete("/api/recorridos/{rid}")
async def eliminar_recorrido(rid: int, u: dict = Depends(solo_admin)):
    with db.conectar() as con:
        if con.execute("DELETE FROM recorridos WHERE id=?", (rid,)).rowcount == 0:
            raise HTTPException(404, "Recorrido no encontrado")
    await conexiones.emitir({"tipo": "recorrido", "accion": "eliminado", "id": rid})
    return {"ok": True}


# ================================================================ API del panel: daños
Tipo = Literal["bache", "grieta", "hundimiento"]
Severidad = Literal["baja", "media", "alta"]


class DanoManual(BaseModel):
    fotograma_id: int | None = None
    tipo: Tipo = "hundimiento"
    caja: list[float] | None = Field(None, min_length=4, max_length=4)
    largo_cm: float | None = Field(None, ge=0)
    ancho_cm: float | None = Field(None, ge=0)
    profundidad_cm: float | None = Field(None, ge=0)
    severidad: Severidad | None = None


class DanoEdicion(BaseModel):
    tipo: Tipo
    largo_cm: float | None = Field(None, ge=0)
    ancho_cm: float | None = Field(None, ge=0)
    profundidad_cm: float | None = Field(None, ge=0)
    severidad: Severidad | None = None


class CambioEstado(BaseModel):
    accion: Literal["validar", "asignar", "reparar", "reabrir"]
    cuadrilla: str | None = None


def _dano(con, did: int):
    d = con.execute("SELECT * FROM danos WHERE id=?", (did,)).fetchone()
    if not d:
        raise HTTPException(404, "Daño no encontrado")
    return d


@app.get("/api/danos")
def listar_danos(tipo: str | None = None, severidad: str | None = None, estado: str | None = None,
                 recorrido: int | None = None, u: dict = Depends(usuario_actual)):
    filtros, valores = [], []
    for campo, valor in (("d.tipo", tipo), ("d.severidad", severidad), ("d.estado", estado), ("d.recorrido_id", recorrido)):
        if valor not in (None, ""):
            filtros.append(f"{campo}=?")
            valores.append(valor)
    where = ("WHERE " + " AND ".join(filtros)) if filtros else ""
    with db.conectar() as con:
        filas = con.execute(
            f"SELECT d.*, r.nombre recorrido_nombre, r.codigo recorrido_codigo, f.imagen FROM danos d "
            f"JOIN recorridos r ON r.id=d.recorrido_id LEFT JOIN fotogramas f ON f.id=d.fotograma_id "
            f"{where} ORDER BY d.id DESC", valores).fetchall()
    return {"danos": [db.dano_json(f) for f in filas]}


@app.post("/api/recorridos/{rid}/danos")
async def marcar_dano(rid: int, datos: DanoManual, u: dict = Depends(usuario_actual)):
    with db.conectar() as con:
        r = con.execute("SELECT * FROM recorridos WHERE id=?", (rid,)).fetchone()
        if not r:
            raise HTTPException(404, "Recorrido no encontrado")
        f = con.execute("SELECT * FROM fotogramas WHERE id=? AND recorrido_id=?", (datos.fotograma_id, rid)).fetchone() \
            if datos.fotograma_id else None
        lat, lon = (f["lat"], f["lon"]) if f else (r["lat"], r["lon"])
        vecino = con.execute("SELECT provincia, canton, direccion, ip_cliente, ip_publica, ip_ciudad, ip_region, ip_isp "
                             "FROM danos WHERE recorrido_id=? ORDER BY id DESC LIMIT 1", (rid,)).fetchone()
    zona = dict(vecino) if vecino else {"provincia": r["provincia"], "canton": r["canton"], "direccion": None}
    ip = dict(vecino) if vecino else {}
    with db.conectar() as con:
        did = insertar_dano(con, rid, f["id"] if f else None, datos.model_dump(), lat, lon, "gps", zona, ip,
                            origen="manual", autor=u["nombre"])
        d = db.dano_json(_dano(con, did))
    await conexiones.emitir({"tipo": "dano", "accion": "nuevo", "dano": d})
    return d


@app.put("/api/danos/{did}")
async def editar_dano(did: int, datos: DanoEdicion, u: dict = Depends(solo_admin)):
    with db.conectar() as con:
        _dano(con, did)
        con.execute("UPDATE danos SET tipo=?, largo_cm=?, ancho_cm=?, profundidad_cm=?, severidad=?, actualizado=? "
                    "WHERE id=?", (datos.tipo, datos.largo_cm, datos.ancho_cm, datos.profundidad_cm, datos.severidad,
                                   db.ahora(), did))
        d = db.dano_json(_dano(con, did))
    await conexiones.emitir({"tipo": "dano", "accion": "actualizado", "dano": d})
    return d


@app.post("/api/danos/{did}/estado")
async def cambiar_estado(did: int, datos: CambioEstado, u: dict = Depends(usuario_actual)):
    if datos.accion != "reparar" and u["rol"] != "admin":
        raise HTTPException(403, "Solo un administrador puede validar, asignar o reabrir daños")
    with db.conectar() as con:
        actual = _dano(con, did)
        if datos.accion == "asignar":
            if not datos.cuadrilla or not con.execute("SELECT 1 FROM cuadrillas WHERE nombre=?",
                                                      (datos.cuadrilla,)).fetchone():
                raise HTTPException(400, "Elige una cuadrilla válida")
            con.execute("UPDATE danos SET estado='asignado', cuadrilla=?, actualizado=? WHERE id=?",
                        (datos.cuadrilla, db.ahora(), did))
        else:
            nuevo = {"validar": "validado", "reparar": "reparado", "reabrir": "pendiente"}[datos.accion]
            cuadrilla = None if datos.accion == "reabrir" else actual["cuadrilla"]
            con.execute("UPDATE danos SET estado=?, cuadrilla=?, actualizado=? WHERE id=?",
                        (nuevo, cuadrilla, db.ahora(), did))
        d = db.dano_json(_dano(con, did))
    await conexiones.emitir({"tipo": "dano", "accion": "actualizado", "dano": d})
    return d


@app.delete("/api/danos/{did}")
async def eliminar_dano(did: int, u: dict = Depends(solo_admin)):
    with db.conectar() as con:
        d = _dano(con, did)
        con.execute("DELETE FROM danos WHERE id=?", (did,))
    await conexiones.emitir({"tipo": "dano", "accion": "eliminado", "id": did, "recorrido_id": d["recorrido_id"]})
    return {"ok": True}


# ================================================================ reportes
@app.post("/api/recorridos/{rid}/reportes")
def guardar_reporte(rid: int, u: dict = Depends(usuario_actual)):
    with db.conectar() as con:
        datos = detalle_recorrido(con, rid)
        repid = con.execute("INSERT INTO reportes (recorrido_id, autor, creado, datos) VALUES (?,?,?,?)",
                            (rid, u["nombre"], db.ahora(), db.a_json(datos))).lastrowid
    return {"id": repid}


@app.get("/api/reportes")
def listar_reportes(u: dict = Depends(usuario_actual)):
    with db.conectar() as con:
        filas = con.execute("SELECT id, recorrido_id, autor, creado, datos FROM reportes ORDER BY id DESC").fetchall()
    salida = []
    for f in filas:
        datos = json.loads(f["datos"])
        danos = datos.get("danos", [])
        salida.append({"id": f["id"], "recorrido_id": f["recorrido_id"], "autor": f["autor"], "creado": f["creado"],
                       "recorrido_nombre": datos.get("nombre"), "recorrido_codigo": datos.get("codigo"),
                       "total": len(danos), "altas": sum(d.get("severidad") == "alta" for d in danos),
                       "reparados": sum(d.get("estado") == "reparado" for d in danos)})
    return {"reportes": salida}


@app.get("/api/reportes/{repid}")
def ver_reporte(repid: int, u: dict = Depends(usuario_actual)):
    with db.conectar() as con:
        f = con.execute("SELECT * FROM reportes WHERE id=?", (repid,)).fetchone()
    if not f:
        raise HTTPException(404, "Reporte no encontrado")
    return {"id": f["id"], "autor": f["autor"], "creado": f["creado"], "recorrido": json.loads(f["datos"])}


@app.delete("/api/reportes/{repid}")
def eliminar_reporte(repid: int, u: dict = Depends(solo_admin)):
    with db.conectar() as con:
        con.execute("DELETE FROM reportes WHERE id=?", (repid,))
    return {"ok": True}


# ================================================================ configuración: cuadrillas y usuarios
class Cuadrilla(BaseModel):
    nombre: str = Field(min_length=2, max_length=60)


@app.get("/api/cuadrillas")
def listar_cuadrillas(u: dict = Depends(usuario_actual)):
    with db.conectar() as con:
        filas = con.execute(
            "SELECT c.id, c.nombre, (SELECT count(*) FROM danos d WHERE d.cuadrilla=c.nombre AND d.estado='asignado') "
            "pendientes FROM cuadrillas c ORDER BY c.nombre").fetchall()
    return {"cuadrillas": [dict(f) for f in filas]}


@app.post("/api/cuadrillas")
def crear_cuadrilla(datos: Cuadrilla, u: dict = Depends(solo_admin)):
    try:
        with db.conectar() as con:
            con.execute("INSERT INTO cuadrillas (nombre) VALUES (?)", (datos.nombre.strip(),))
    except Exception:
        raise HTTPException(400, "Ya existe una cuadrilla con ese nombre")
    return {"ok": True}


@app.delete("/api/cuadrillas/{cid}")
def eliminar_cuadrilla(cid: int, u: dict = Depends(solo_admin)):
    with db.conectar() as con:
        con.execute("DELETE FROM cuadrillas WHERE id=?", (cid,))
    return {"ok": True}


class NuevoUsuario(BaseModel):
    nombre: str = Field(min_length=3)
    correo: str = Field(pattern=USUARIO_VALIDO)
    rol: Literal["admin", "tecnico"]
    contrasena: str = Field(min_length=6)


@app.get("/api/admin/codigo")
def ver_codigo_admin(regenerar: bool = False, u: dict = Depends(solo_admin)):
    with db.conectar() as con:
        return {"codigo": db.codigo_admin(con, regenerar)}


@app.get("/api/admin/token-dispositivo")
def ver_token_dispositivo(regenerar: bool = False, u: dict = Depends(solo_admin)):
    with db.conectar() as con:
        return {"token": db.token_dispositivo(con, regenerar)}


@app.get("/api/usuarios")
def listar_usuarios(u: dict = Depends(solo_admin)):
    with db.conectar() as con:
        filas = con.execute("SELECT id, nombre, correo, cargo, rol, creado FROM usuarios ORDER BY nombre").fetchall()
    return {"usuarios": [dict(f) for f in filas]}


@app.post("/api/usuarios")
def crear_usuario(datos: NuevoUsuario, u: dict = Depends(solo_admin)):
    try:
        with db.conectar() as con:
            db.crear_usuario(con, datos.nombre.strip(), datos.correo, datos.rol, datos.contrasena)
    except Exception:
        raise HTTPException(400, "Ya existe un usuario con ese correo")
    return {"ok": True}


@app.delete("/api/usuarios/{uid}")
def eliminar_usuario(uid: int, u: dict = Depends(solo_admin)):
    if uid == u["id"]:
        raise HTTPException(400, "No puedes eliminar tu propia cuenta")
    with db.conectar() as con:
        con.execute("DELETE FROM usuarios WHERE id=?", (uid,))
    return {"ok": True}


app.mount("/capturas", StaticFiles(directory=db.CAPTURAS), name="capturas")
app.mount("/", StaticFiles(directory=WEB, html=True), name="web")

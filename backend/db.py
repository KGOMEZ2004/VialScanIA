"""
Base de datos SQLite de VialScan: usuarios, sesiones, cuadrillas, recorridos, fotogramas, daños y reportes.
La ruta se puede cambiar con la variable VIALSCAN_DB (útil para pruebas).
"""
import hashlib
import json
import os
import secrets
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import escena_demo

RAIZ = Path(__file__).resolve().parent
DB = Path(os.getenv("VIALSCAN_DB", RAIZ / "baches.db"))
CAPTURAS = RAIZ / "capturas"
CAPTURAS.mkdir(exist_ok=True)

ESQUEMA = """
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL, correo TEXT NOT NULL UNIQUE, cargo TEXT,
    rol TEXT NOT NULL CHECK (rol IN ('admin', 'tecnico')),
    sal TEXT NOT NULL, hash TEXT NOT NULL, creado TEXT
);
CREATE TABLE IF NOT EXISTS sesiones (
    token TEXT PRIMARY KEY, usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE, expira TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS config (clave TEXT PRIMARY KEY, valor TEXT);
CREATE TABLE IF NOT EXISTS cuadrillas (
    id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS recorridos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT UNIQUE, nombre TEXT, fuente TEXT, origen_clave TEXT,
    estado TEXT NOT NULL DEFAULT 'pendiente' CHECK (estado IN ('pendiente', 'en_proceso', 'completado')),
    creado TEXT, actualizado TEXT, lat REAL, lon REAL, provincia TEXT, canton TEXT,
    ip_cliente TEXT, ip_publica TEXT, ip_ciudad TEXT, ip_region TEXT, ip_isp TEXT
);
CREATE TABLE IF NOT EXISTS fotogramas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recorrido_id INTEGER NOT NULL REFERENCES recorridos(id) ON DELETE CASCADE,
    imagen TEXT, lat REAL, lon REAL, velocidad REAL, fecha TEXT, procesado INTEGER DEFAULT 1
);
CREATE TABLE IF NOT EXISTS danos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recorrido_id INTEGER NOT NULL REFERENCES recorridos(id) ON DELETE CASCADE,
    fotograma_id INTEGER REFERENCES fotogramas(id) ON DELETE SET NULL,
    tipo TEXT NOT NULL DEFAULT 'bache' CHECK (tipo IN ('bache', 'grieta', 'hundimiento')),
    origen TEXT NOT NULL DEFAULT 'ia' CHECK (origen IN ('ia', 'manual')),
    confianza REAL, bx REAL, by REAL, bw REAL, bh REAL,
    largo_cm REAL, ancho_cm REAL, profundidad_cm REAL,
    severidad TEXT CHECK (severidad IN ('baja', 'media', 'alta') OR severidad IS NULL),
    estado TEXT NOT NULL DEFAULT 'pendiente' CHECK (estado IN ('pendiente', 'validado', 'asignado', 'reparado')),
    cuadrilla TEXT,
    lat REAL, lon REAL, ubicacion_por TEXT, provincia TEXT, canton TEXT, direccion TEXT,
    ip_cliente TEXT, ip_publica TEXT, ip_ciudad TEXT, ip_region TEXT, ip_isp TEXT,
    reportes INTEGER DEFAULT 1, creado TEXT, actualizado TEXT, creado_por TEXT
);
CREATE TABLE IF NOT EXISTS ruta (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recorrido_id INTEGER NOT NULL REFERENCES recorridos(id) ON DELETE CASCADE,
    lat REAL, lon REAL, velocidad REAL, fecha TEXT
);
CREATE INDEX IF NOT EXISTS ix_ruta_recorrido ON ruta(recorrido_id);
CREATE TABLE IF NOT EXISTS reportes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recorrido_id INTEGER REFERENCES recorridos(id) ON DELETE SET NULL,
    autor TEXT, creado TEXT, datos TEXT
);
CREATE INDEX IF NOT EXISTS ix_danos_recorrido ON danos(recorrido_id);
CREATE INDEX IF NOT EXISTS ix_danos_pos ON danos(lat, lon);
CREATE INDEX IF NOT EXISTS ix_fotogramas_recorrido ON fotogramas(recorrido_id);
"""


def conectar():
    con = sqlite3.connect(DB, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def ahora(delta: timedelta = timedelta()) -> str:
    return (datetime.now() + delta).isoformat(timespec="seconds")


# ---------------------------------------------------------------- contraseñas
def hash_contrasena(contrasena: str, sal: str | None = None) -> tuple[str, str]:
    sal = sal or secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", contrasena.encode(), bytes.fromhex(sal), 200_000).hex()
    return sal, h


def verificar_contrasena(contrasena: str, sal: str, h: str) -> bool:
    return secrets.compare_digest(hash_contrasena(contrasena, sal)[1], h)


def crear_usuario(con, nombre, correo, rol, contrasena, cargo=None) -> int:
    sal, h = hash_contrasena(contrasena)
    cargo = cargo or ("Administrador · Mantenimiento vial" if rol == "admin" else "Técnico de mantenimiento")
    return con.execute(
        "INSERT INTO usuarios (nombre, correo, cargo, rol, sal, hash, creado) VALUES (?,?,?,?,?,?,?)",
        (nombre, correo.strip().lower(), cargo, rol, sal, h, ahora())).lastrowid


# ---------------------------------------------------------------- códigos
def nuevo_codigo_recorrido(con) -> str:
    anio = datetime.now().year
    n = con.execute("SELECT count(*) FROM recorridos WHERE codigo LIKE ?", (f"PRJ-{anio}-%",)).fetchone()[0]
    while True:
        n += 1
        codigo = f"PRJ-{anio}-{n:02d}"
        if not con.execute("SELECT 1 FROM recorridos WHERE codigo=?", (codigo,)).fetchone():
            return codigo


def codigo_dano(dano_id: int) -> str:
    return f"D-{dano_id + 100}"


# ---------------------------------------------------------------- datos de ejemplo
USUARIOS_INICIALES = [
    ("Administrador", "admin", "admin", "admin123"),
    ("Ing. Carlos Ruiz", "c.ruiz@milagro.gob.ec", "admin", "vialscan2026"),
    ("María Torres", "m.torres@milagro.gob.ec", "tecnico", "tecnico2026"),
]
TAMANOS = {"alta": (110, 80, 10), "media": (70, 50, 6), "baja": (40, 30, 3)}

# (nombre, estado, antigüedad, [(variante, fracción de la ruta, velocidad), ...], estados de los daños)
# Las rutas siguen el trazado real de las calles de Milagro (OpenStreetMap, backend/rutas_demo.json).
RECORRIDOS_DEMO = [
    ("Av. 17 de Septiembre – Centro", "completado", timedelta(hours=-2),
     [(1, 0.18, 38), (3, 0.55, 35)], ["pendiente"]),
    ("Av. Chirijos – Sector Sur", "en_proceso", timedelta(days=-1),
     [(2, 0.2, 29), (4, 0.6, 31)], ["validado", "asignado", "pendiente"]),
    ("Vía Milagro–Naranjito km 3", "pendiente", timedelta(days=-14),
     [(3, 0.25, 52), (2, 0.65, 55)], []),
    ("Av. Cristóbal Colón – Las Piñas", "completado", timedelta(days=-19),
     [(4, 0.15, 33), (1, 0.58, 36)], ["reparado", "reparado", "asignado", "validado"]),
]
MINUTOS_RECORRIDO_DEMO = 4


def _rutas_demo() -> dict:
    ruta = RAIZ / "rutas_demo.json"
    return json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else {}


def _metros(a, b) -> float:
    import math
    return math.hypot((a[0] - b[0]) * 111320, (a[1] - b[1]) * 111320 * math.cos(math.radians(a[0])))


def punto_en_ruta(ruta: list, f: float) -> tuple[float, float]:
    """Punto a la fracción f (0-1) del largo de la ruta."""
    tramos = [_metros(ruta[i - 1], ruta[i]) for i in range(1, len(ruta))]
    objetivo = max(0.0, min(1.0, f)) * sum(tramos)
    for i, t in enumerate(tramos):
        if objetivo <= t or i == len(tramos) - 1:
            k = 0 if t == 0 else min(1.0, objetivo / t)
            a, b = ruta[i], ruta[i + 1]
            return a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k
        objetivo -= t
    return tuple(ruta[-1])


def _svg_demo(variante: int) -> str:
    nombre = f"demo_v{variante}.svg"
    ruta = CAPTURAS / nombre
    if not ruta.exists():
        ruta.write_text(escena_demo.escena_svg(variante), encoding="utf-8")
    return f"/capturas/{nombre}"


def insertar_danos_demo(con, recorrido_id, fotograma_id, variante, posiciones, fecha, estados, cuadrillas):
    for i, d in enumerate(escena_demo.danos_detectables(variante)):
        lat, lon = posiciones[i % len(posiciones)]
        largo, ancho, prof = (180, 4, 3) if d["tipo"] == "grieta" else TAMANOS[d["severidad"]]
        estado = estados[i % len(estados)] if estados else "pendiente"
        cuadrilla = cuadrillas[i % len(cuadrillas)] if estado in ("asignado", "reparado") else None
        bx, by, bw, bh = d["caja"]
        con.execute(
            """INSERT INTO danos (recorrido_id, fotograma_id, tipo, origen, confianza, bx, by, bw, bh,
                   largo_cm, ancho_cm, profundidad_cm, severidad, estado, cuadrilla, lat, lon, ubicacion_por,
                   provincia, canton, direccion, creado, actualizado, creado_por)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (recorrido_id, fotograma_id, d["tipo"], "ia", d["confianza"], bx, by, bw, bh, largo, ancho, prof,
             d["severidad"], estado, cuadrilla, lat, lon, "gps",
             "Guayas", "Milagro", "Milagro, Guayas, Ecuador", fecha, fecha, "IA"))


def codigo_admin(con, regenerar: bool = False) -> str:
    """Código que pide el registro para crear cuentas de administrador."""
    fila = con.execute("SELECT valor FROM config WHERE clave='codigo_admin'").fetchone()
    if fila and not regenerar:
        return fila["valor"]
    codigo = f"{secrets.randbelow(900000) + 100000}"
    con.execute("INSERT OR REPLACE INTO config (clave, valor) VALUES ('codigo_admin', ?)", (codigo,))
    return codigo


def sembrar(con):
    # Usuarios iniciales (se crean los que falten; no se tocan las contraseñas de los existentes)
    for nombre, correo, rol, clave in USUARIOS_INICIALES:
        if not con.execute("SELECT 1 FROM usuarios WHERE correo=?", (correo,)).fetchone():
            crear_usuario(con, nombre, correo, rol, clave)
    codigo_admin(con)
    if not con.execute("SELECT 1 FROM cuadrillas").fetchone():
        con.executemany("INSERT INTO cuadrillas (nombre) VALUES (?)",
                        [("Cuadrilla Norte",), ("Cuadrilla Centro",), ("Cuadrilla Sur",)])
    if con.execute("SELECT 1 FROM recorridos").fetchone():
        return
    cuadrillas = [f["nombre"] for f in con.execute("SELECT nombre FROM cuadrillas")]
    rutas = _rutas_demo()
    for nombre, estado, delta, fotos, estados_danos in RECORRIDOS_DEMO:
        ruta = rutas.get(nombre) or [[-2.1326, -79.5832], [-2.1310, -79.5850]]
        inicio = datetime.now() + delta - timedelta(minutes=MINUTOS_RECORRIDO_DEMO)
        cuando = lambda f: (inicio + timedelta(minutes=MINUTOS_RECORRIDO_DEMO * f)).isoformat(timespec="seconds")
        fin = cuando(1)
        rid = con.execute(
            """INSERT INTO recorridos (codigo, nombre, fuente, estado, creado, actualizado, lat, lon, provincia, canton)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (nuevo_codigo_recorrido(con), nombre, "demo", estado, fin, fin, *ruta[0], "Guayas", "Milagro")).lastrowid
        # Ruta GPS: un punto cada ~25 m
        n = 45
        velocidades = [v for _, _, v in fotos]
        for k in range(n + 1):
            f = k / n
            con.execute("INSERT INTO ruta (recorrido_id, lat, lon, velocidad, fecha) VALUES (?,?,?,?,?)",
                        (rid, *punto_en_ruta(ruta, f), velocidades[k % len(velocidades)] + (k % 5) - 2, cuando(f)))
        for variante, f, vel in fotos:
            procesado = 0 if estado == "pendiente" else 1
            fid = con.execute(
                "INSERT INTO fotogramas (recorrido_id, imagen, lat, lon, velocidad, fecha, procesado) VALUES (?,?,?,?,?,?,?)",
                (rid, _svg_demo(variante), *punto_en_ruta(ruta, f), vel, cuando(f), procesado)).lastrowid
            if procesado:
                # Los daños del fotograma están por delante de la cámara, repartidos sobre la calle
                posiciones = [punto_en_ruta(ruta, f + 0.05 + 0.07 * j) for j in range(4)]
                insertar_danos_demo(con, rid, fid, variante, posiciones, cuando(f), estados_danos, cuadrillas)


def migrar_tabla_antigua(con):
    """Pasa los baches de la versión anterior (tabla 'baches') a un recorrido 'Registros anteriores'."""
    if not con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='baches'").fetchone():
        return
    filas = con.execute("SELECT * FROM baches ORDER BY id").fetchall()
    if filas:
        sev = {"leve": "baja", "moderado": "media", "grave": "alta"}
        rid = con.execute(
            "INSERT INTO recorridos (codigo, nombre, fuente, estado, creado, actualizado, lat, lon, provincia, canton) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (nuevo_codigo_recorrido(con), "Registros anteriores", "importado", "completado", filas[0]["fecha"],
             filas[-1]["fecha"], filas[0]["lat"], filas[0]["lon"], filas[0]["provincia"], filas[0]["canton"])).lastrowid
        for b in filas:
            fid = con.execute(
                "INSERT INTO fotogramas (recorrido_id, imagen, lat, lon, fecha) VALUES (?,?,?,?,?)",
                (rid, b["imagen"], b["lat"], b["lon"], b["fecha"])).lastrowid if b["imagen"] else None
            con.execute(
                """INSERT INTO danos (recorrido_id, fotograma_id, tipo, origen, confianza, severidad, lat, lon,
                       ubicacion_por, provincia, canton, direccion, ip_cliente, ip_publica, ip_ciudad, ip_region,
                       ip_isp, reportes, creado, actualizado, creado_por)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (rid, fid, "bache", "ia", b["confianza"], sev.get(b["severidad"], "media"), b["lat"], b["lon"],
                 b["ubicacion_por"], b["provincia"], b["canton"], b["direccion"], b["ip_cliente"], b["ip_publica"],
                 b["ip_ciudad"], b["ip_region"], b["ip_isp"], b["reportes"], b["fecha"], b["fecha"], b["fuente"]))
    con.execute("ALTER TABLE baches RENAME TO baches_version_anterior")


def iniciar():
    with conectar() as con:
        con.executescript(ESQUEMA)
        sembrar(con)
        migrar_tabla_antigua(con)
        # Una sola vez: en los recorridos de ejemplo, las grietas ya no las "detecta" la IA (se marcan a mano)
        if not con.execute("SELECT 1 FROM config WHERE clave='grietas_demo_manuales'").fetchone():
            con.execute("DELETE FROM danos WHERE tipo='grieta' AND origen='ia' AND recorrido_id IN "
                        "(SELECT id FROM recorridos WHERE fuente='demo')")
            con.execute("INSERT INTO config (clave, valor) VALUES ('grietas_demo_manuales', '1')")
        con.execute("DELETE FROM sesiones WHERE expira < ?", (ahora(),))
        print(f"[VialScan] Código para registrar administradores: {codigo_admin(con)}  (también en Configuración > Sistema)")


def fila(r) -> dict | None:
    return dict(r) if r else None


def dano_json(r) -> dict:
    d = dict(r)
    d["codigo"] = codigo_dano(d["id"])
    d["caja"] = [d.pop("bx"), d.pop("by"), d.pop("bw"), d.pop("bh")]
    if d["caja"][0] is None:
        d["caja"] = None
    return d


def a_json(obj) -> str:
    return json.dumps(obj, ensure_ascii=False)

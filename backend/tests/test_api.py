import pytest

import db
from conftest import CONTRASENA

QUITO = {"lat": -0.1807, "lon": -78.4678}


# ---------------------------------------------------------------- inicio de sesión
def test_login_correcto_devuelve_token_y_rol(cliente):
    r = cliente.post("/api/auth/login", json={"correo": "admin", "contrasena": CONTRASENA, "rol": "admin"})
    assert r.status_code == 200
    assert r.json()["token"]
    assert r.json()["usuario"]["rol"] == "admin"


@pytest.mark.parametrize("contrasena", ["incorrecta", *db.CONTRASENAS_ANTIGUAS])
def test_login_rechaza_contrasenas_incorrectas_y_las_fijas_antiguas(cliente, contrasena):
    r = cliente.post("/api/auth/login", json={"correo": "admin", "contrasena": contrasena, "rol": "admin"})
    assert r.status_code == 401


def test_logout_invalida_la_sesion(cliente, tecnico):
    assert cliente.get("/api/auth/yo", headers=tecnico).status_code == 200
    cliente.post("/api/auth/logout", headers=tecnico)
    assert cliente.get("/api/auth/yo", headers=tecnico).status_code == 401


def test_registro_de_admin_exige_el_codigo(cliente):
    datos = {"nombre": "Intruso", "correo": "intruso", "contrasena": "123456", "rol": "admin", "codigo_admin": "000000"}
    assert cliente.post("/api/auth/registro", json=datos).status_code == 403


# ---------------------------------------------------------------- rutas del panel
@pytest.mark.parametrize("ruta", ["/api/recorridos", "/api/danos", "/api/reportes", "/api/cuadrillas",
                                  "/api/usuarios", "/api/admin/codigo", "/api/admin/token-dispositivo",
                                  "/api/vivo/1.jpg"])
def test_rutas_del_panel_piden_sesion(cliente, ruta):
    assert cliente.get(ruta).status_code == 401


@pytest.mark.parametrize("ruta", ["/api/usuarios", "/api/admin/codigo", "/api/admin/token-dispositivo"])
def test_rutas_de_admin_rechazan_al_tecnico(cliente, tecnico, ruta):
    assert cliente.get(ruta, headers=tecnico).status_code == 403


def test_panel_lista_recorridos_y_danos_de_ejemplo(cliente, tecnico):
    assert cliente.get("/api/recorridos", headers=tecnico).json()["recorridos"]
    assert cliente.get("/api/danos", headers=tecnico).json()["danos"]


# ---------------------------------------------------------------- rutas de dispositivos (Unity / cámara)
@pytest.mark.parametrize("metodo,ruta", [("get", "/api/baches"), ("post", "/api/baches"),
                                         ("post", "/api/detectar"), ("post", "/api/vivo")])
@pytest.mark.parametrize("cabeceras", [{}, {"X-Token-Dispositivo": "token-falso"}])
def test_rutas_de_dispositivos_exigen_token(cliente, metodo, ruta, cabeceras):
    assert getattr(cliente, metodo)(ruta, headers=cabeceras).status_code == 401


def test_dispositivo_con_token_reporta_un_bache(cliente, dispositivo, tecnico):
    r = cliente.post("/api/baches", headers=dispositivo,
                     json={**QUITO, "confianza": 0.9, "severidad": "grave", "fuente": "simulador"})
    assert r.status_code == 200, r.text
    assert r.json()["provincia"] == "Pichincha"
    codigos = [b["codigo"] for b in cliente.get("/api/baches", headers=dispositivo).json()["baches"]]
    assert r.json()["codigo"] in codigos


def test_reporte_repetido_en_el_mismo_sitio_suma_reportes(cliente, dispositivo):
    punto = {"lat": -2.1710, "lon": -79.9224, "fuente": "simulador"}
    primero = cliente.post("/api/baches", headers=dispositivo, json=punto).json()
    segundo = cliente.post("/api/baches", headers=dispositivo, json=punto).json()
    assert segundo["duplicado"] is True
    assert segundo["id"] == primero["id"]


def test_regenerar_el_token_invalida_el_anterior(cliente, admin):
    viejo = cliente.get("/api/admin/token-dispositivo", headers=admin).json()["token"]
    nuevo = cliente.get("/api/admin/token-dispositivo?regenerar=true", headers=admin).json()["token"]
    assert nuevo != viejo
    assert cliente.get("/api/baches", headers={"X-Token-Dispositivo": viejo}).status_code == 401
    assert cliente.get("/api/baches", headers={"X-Token-Dispositivo": nuevo}).status_code == 200

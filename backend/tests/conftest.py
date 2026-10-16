"""
Cada sesión de pruebas usa una base de datos temporal, con una contraseña inicial conocida
y sin llamadas a internet (geolocalización por IP y Nominatim).
"""
import os
import sys
import tempfile
from pathlib import Path

import pytest

_TMP = tempfile.mkdtemp(prefix="vialscan_test_")
os.environ["VIALSCAN_DB"] = str(Path(_TMP) / "test.db")
os.environ["VIALSCAN_CONTRASENA_INICIAL"] = "clave-de-prueba"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import app as servidor  # noqa: E402  (después de configurar las variables de entorno)
import db  # noqa: E402
import geo_ecuador as geo  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

CONTRASENA = os.environ["VIALSCAN_CONTRASENA_INICIAL"]


@pytest.fixture(autouse=True)
def sin_red(monkeypatch):
    monkeypatch.setattr(geo, "info_ip", lambda ip: {"ip_cliente": ip, "ip_publica": None})
    monkeypatch.setattr(geo, "zona_desde_coordenadas", geo.provincia_mas_cercana)


@pytest.fixture(scope="session")
def cliente():
    return TestClient(servidor.app)


def _login(cliente, correo, rol):
    r = cliente.post("/api/auth/login", json={"correo": correo, "contrasena": CONTRASENA, "rol": rol})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


@pytest.fixture
def admin(cliente):
    return _login(cliente, "admin", "admin")


@pytest.fixture
def tecnico(cliente):
    return _login(cliente, "m.torres@milagro.gob.ec", "tecnico")


@pytest.fixture
def dispositivo():
    with db.conectar() as con:
        return {"X-Token-Dispositivo": db.token_dispositivo(con)}

"""
Geolocalización para Ecuador:
- Provincia / cantón a partir de coordenadas (Nominatim, con respaldo offline).
- IP del dispositivo que reporta y geolocalización por IP (ip-api.com).
"""
import ipaddress
import math
import time
from functools import lru_cache

import requests

USER_AGENT = "DetectorBachesEcuador/1.0"

# Límites aproximados de Ecuador (continente + Galápagos)
LAT_MIN, LAT_MAX = -5.1, 1.7
LON_MIN, LON_MAX = -92.1, -75.1

# Capitales provinciales (respaldo offline: provincia más cercana)
CAPITALES = {
    "Azuay": ("Cuenca", -2.9001, -79.0059),
    "Bolívar": ("Guaranda", -1.5926, -79.0010),
    "Cañar": ("Azogues", -2.7397, -78.8486),
    "Carchi": ("Tulcán", 0.8117, -77.7173),
    "Chimborazo": ("Riobamba", -1.6636, -78.6546),
    "Cotopaxi": ("Latacunga", -0.9352, -78.6155),
    "El Oro": ("Machala", -3.2581, -79.9554),
    "Esmeraldas": ("Esmeraldas", 0.9682, -79.6517),
    "Galápagos": ("Puerto Baquerizo Moreno", -0.9017, -89.6103),
    "Guayas": ("Guayaquil", -2.1710, -79.9224),
    "Imbabura": ("Ibarra", 0.3517, -78.1223),
    "Loja": ("Loja", -3.9931, -79.2042),
    "Los Ríos": ("Babahoyo", -1.8022, -79.5344),
    "Manabí": ("Portoviejo", -1.0546, -80.4545),
    "Morona Santiago": ("Macas", -2.3087, -78.1114),
    "Napo": ("Tena", -0.9938, -77.8129),
    "Orellana": ("Francisco de Orellana", -0.4629, -76.9872),
    "Pastaza": ("Puyo", -1.4924, -78.0024),
    "Pichincha": ("Quito", -0.1807, -78.4678),
    "Santa Elena": ("Santa Elena", -2.2262, -80.8583),
    "Santo Domingo de los Tsáchilas": ("Santo Domingo", -0.2530, -79.1754),
    "Sucumbíos": ("Nueva Loja", 0.0847, -76.8828),
    "Tungurahua": ("Ambato", -1.2491, -78.6168),
    "Zamora Chinchipe": ("Zamora", -4.0692, -78.9567),
}


def dentro_de_ecuador(lat: float, lon: float) -> bool:
    return LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX


def distancia_m(lat1, lon1, lat2, lon2) -> float:
    """Distancia Haversine en metros."""
    r = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def provincia_mas_cercana(lat: float, lon: float) -> dict:
    prov, (ciudad, _, _) = min(
        CAPITALES.items(),
        key=lambda kv: distancia_m(lat, lon, kv[1][1], kv[1][2]),
    )
    return {"provincia": prov, "canton": ciudad, "direccion": f"Cerca de {ciudad}, {prov}", "via": None, "sector": None}


_ultimo_nominatim = 0.0


@lru_cache(maxsize=2048)
def _reverse_nominatim(lat_r: float, lon_r: float) -> dict | None:
    global _ultimo_nominatim
    # Política de Nominatim: máximo 1 petición por segundo
    espera = 1.0 - (time.time() - _ultimo_nominatim)
    if espera > 0:
        time.sleep(espera)
    _ultimo_nominatim = time.time()
    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"lat": lat_r, "lon": lon_r, "format": "jsonv2", "accept-language": "es"},
            headers={"User-Agent": USER_AGENT},
            timeout=5,
        )
        r.raise_for_status()
        data = r.json()
        addr = data.get("address", {})
        provincia = addr.get("state", "").replace("Provincia de ", "").replace("Provincia del ", "")
        canton = addr.get("county") or addr.get("city") or addr.get("town") or addr.get("village", "")
        return {
            "provincia": provincia or None,
            "canton": canton.replace("Cantón ", "") or None,
            "direccion": data.get("display_name"),
            "via": addr.get("road"),
            "sector": addr.get("suburb") or addr.get("neighbourhood") or addr.get("quarter"),
        }
    except Exception:
        return None


def zona_desde_coordenadas(lat: float, lon: float) -> dict:
    """Devuelve provincia, cantón y dirección de un punto en Ecuador."""
    # Redondeo a ~100 m para aprovechar la caché
    info = _reverse_nominatim(round(lat, 3), round(lon, 3))
    if info and info.get("provincia"):
        return info
    return provincia_mas_cercana(lat, lon)


def es_ip_privada(ip: str) -> bool:
    try:
        return ipaddress.ip_address(ip).is_private or ipaddress.ip_address(ip).is_loopback
    except ValueError:
        return True


_cache_ip_publica = {"ip": None, "t": 0.0}


def ip_publica_servidor() -> str | None:
    """IP pública de la red donde corre el servidor (se cachea 10 min)."""
    if _cache_ip_publica["ip"] and time.time() - _cache_ip_publica["t"] < 600:
        return _cache_ip_publica["ip"]
    try:
        ip = requests.get("https://api.ipify.org", timeout=4).text.strip()
        _cache_ip_publica.update(ip=ip, t=time.time())
        return ip
    except Exception:
        return None


@lru_cache(maxsize=512)
def geolocalizar_ip(ip: str) -> dict:
    """Ubicación aproximada de una IP pública (ciudad, región, ISP, lat/lon)."""
    try:
        r = requests.get(
            f"http://ip-api.com/json/{ip}",
            params={"fields": "status,country,regionName,city,isp,lat,lon", "lang": "es"},
            timeout=4,
        )
        data = r.json()
        if data.get("status") == "success":
            return {
                "ip_pais": data.get("country"),
                "ip_region": data.get("regionName"),
                "ip_ciudad": data.get("city"),
                "ip_isp": data.get("isp"),
                "ip_lat": data.get("lat"),
                "ip_lon": data.get("lon"),
            }
    except Exception:
        pass
    return {}


def info_ip(ip_cliente: str) -> dict:
    """
    Resuelve la IP que reporta el bache.
    Si el dispositivo está en red local, se usa la IP pública de la red.
    """
    ip_publica = ip_cliente
    if es_ip_privada(ip_cliente):
        ip_publica = ip_publica_servidor()
    datos = {"ip_cliente": ip_cliente, "ip_publica": ip_publica}
    if ip_publica:
        datos.update(geolocalizar_ip(ip_publica))
    return datos

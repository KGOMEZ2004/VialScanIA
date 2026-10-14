"""
Genera la textura del mapa de Ecuador (provincias) para Unity.
Los bordes de la imagen coinciden con los límites de MapaEcuador.cs:
  lat 1.7 (norte) a -5.1 (sur), lon -81.2 (oeste) a -75.1 (este). Galápagos queda fuera.

  python herramientas/generar_mapa_unity.py
Fuente de límites: geoBoundaries (CC BY 4.0), https://www.geoboundaries.org
"""
import sys
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from geo_ecuador import CAPITALES  # noqa: E402

LAT_N, LAT_S, LON_O, LON_E = 1.7, -5.1, -81.2, -75.1
ANCHO = 2048
ALTO = round(ANCHO * (LAT_N - LAT_S) / (LON_E - LON_O))
API = "https://www.geoboundaries.org/api/current/gbOpen/ECU/ADM1/"
SALIDA = Path(__file__).resolve().parents[2] / "repo_unity" / "Assets" / "Baches" / "Texturas" / "MapaEcuador.png"

ETIQUETA_ABAJO = {"Zamora Chinchipe", "Azuay"}
PALETA = ["#dfe9c8", "#f2e2c4", "#d6e4ef", "#ead5e4", "#f3edc2", "#d3ead9", "#e8dccd", "#dcd8ef"]


def px(lon, lat):
    return ((lon - LON_O) / (LON_E - LON_O) * ANCHO, (LAT_N - lat) / (LAT_N - LAT_S) * ALTO)


def anillos(geom):
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    for poly in polys:
        yield poly[0]  # anillo exterior


def main():
    url = requests.get(API, timeout=30).json()["simplifiedGeometryGeoJSON"]
    geo = requests.get(url, timeout=60).json()

    img = Image.new("RGB", (ANCHO, ALTO), "#a9cfe6")  # océano
    d = ImageDraw.Draw(img)
    for i, f in enumerate(geo["features"]):
        for anillo in anillos(f["geometry"]):
            d.polygon([px(x, y) for x, y in anillo], fill=PALETA[i % len(PALETA)], outline="#5b6270")
    # Bordes más gruesos encima de los rellenos
    for f in geo["features"]:
        for anillo in anillos(f["geometry"]):
            d.line([px(x, y) for x, y in anillo] + [px(*anillo[0])], fill="#5b6270", width=3)

    try:
        fuente = ImageFont.truetype("arialbd.ttf", 30)
        fuente_ciudad = ImageFont.truetype("arial.ttf", 22)
    except OSError:
        fuente = fuente_ciudad = ImageFont.load_default()

    for prov, (ciudad, lat, lon) in CAPITALES.items():
        if not (LAT_S <= lat <= LAT_N and LON_O <= lon <= LON_E):
            continue
        x, y = px(lon, lat)
        d.ellipse([x - 7, y - 7, x + 7, y + 7], fill="#1d2230")
        # Provincias cuyas capitales están muy juntas: nombre debajo del punto
        y_nombre, anc_nombre, y_ciudad = (y + 12, "ma", y + 46) if prov in ETIQUETA_ABAJO else (y - 12, "md", y + 12)
        d.text((x, y_nombre), prov.upper(), font=fuente, fill="#1d2230", anchor=anc_nombre,
               stroke_width=3, stroke_fill="white")
        d.text((x, y_ciudad), ciudad, font=fuente_ciudad, fill="#3a4150", anchor="ma",
               stroke_width=2, stroke_fill="white")

    d.text((ANCHO - 20, ALTO - 20), "Límites: geoBoundaries (CC BY 4.0)", font=fuente_ciudad,
           fill="#3a4150", anchor="rd")
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    img.save(SALIDA)
    print(f"Mapa {ANCHO}x{ALTO} guardado en {SALIDA}")


if __name__ == "__main__":
    main()

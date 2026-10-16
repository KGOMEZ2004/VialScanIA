"""
Envía baches de prueba en ciudades de Ecuador para probar el mapa sin cámara ni YOLO.
  python simular.py --cantidad 15 --token <TOKEN>
"""
import argparse
import os
import random
import time

import requests

CIUDADES = [
    (-0.1807, -78.4678), (-2.1710, -79.9224), (-2.9001, -79.0059), (-1.2491, -78.6168),
    (-3.9931, -79.2042), (-1.0546, -80.4545), (0.3517, -78.1223), (-0.2530, -79.1754),
    (-1.6636, -78.6546), (-3.2581, -79.9554), (0.9682, -79.6517), (-0.9352, -78.6155),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cantidad", type=int, default=10)
    ap.add_argument("--servidor", default="http://127.0.0.1:8000")
    ap.add_argument("--token", default=os.getenv("VIALSCAN_TOKEN_DISPOSITIVO", ""),
                    help="token de dispositivo (Configuración > Sistema o consola del servidor)")
    args = ap.parse_args()

    for _ in range(args.cantidad):
        lat, lon = random.choice(CIUDADES)
        payload = {
            "lat": lat + random.uniform(-0.03, 0.03),
            "lon": lon + random.uniform(-0.03, 0.03),
            "confianza": round(random.uniform(0.5, 0.97), 2),
            "severidad": random.choice(["leve", "moderado", "grave"]),
            "fuente": "simulador",
        }
        r = requests.post(f"{args.servidor}/api/baches", json=payload,
                          headers={"X-Token-Dispositivo": args.token}, timeout=20)
        if not r.ok:
            raise SystemExit(f"[ERROR] {r.status_code}: {r.text}")
        b = r.json()
        print(f"#{b['id']} {b['provincia']} / {b['canton']} | IP {b['ip_publica']} | {b['severidad']}")
        time.sleep(1.1)  # respeta el límite de Nominatim


if __name__ == "__main__":
    main()

"""
Detección en vivo con YOLO desde webcam, video o cámara IP.
Cada bache detectado se envía al servidor, que lo ubica en el mapa de Ecuador con la IP de la zona.

Ejemplos:
  python detectar_camara.py                              # webcam 0, ubicación por IP
  python detectar_camara.py --fuente video.mp4 --lat -0.1807 --lon -78.4678
  python detectar_camara.py --fuente rtsp://192.168.1.20:554/stream
"""
import argparse
import base64
import threading
import time

import cv2
import requests

from yolo_detector import DetectorBaches, dibujar


def enviar(servidor: str, payload: dict):
    try:
        r = requests.post(f"{servidor}/api/baches", json=payload, timeout=15)
        b = r.json()
        if r.ok:
            estado = "ya registrado, +1 reporte" if b.get("duplicado") else "NUEVO"
            print(f"[MAPA] {b['codigo']} {estado} | {b['provincia']} - {b['canton']} | "
                  f"IP: {b['ip_publica']} ({b['ip_ciudad']}) | {b['lat']:.5f}, {b['lon']:.5f}")
        else:
            print(f"[ERROR] {r.status_code}: {b}")
    except Exception as e:
        print(f"[ERROR] No se pudo contactar al servidor: {e}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fuente", default="0", help="índice de webcam, ruta de video o URL rtsp/http")
    ap.add_argument("--modelo", default=None, help="ruta a .pt (por defecto models/baches.pt)")
    ap.add_argument("--conf", type=float, default=0.45)
    ap.add_argument("--servidor", default="http://127.0.0.1:8000")
    ap.add_argument("--lat", type=float, default=None, help="latitud GPS (si no, se usa la IP)")
    ap.add_argument("--lon", type=float, default=None)
    ap.add_argument("--espera", type=float, default=3.0, help="segundos mínimos entre reportes")
    args = ap.parse_args()

    detector = DetectorBaches(args.modelo, args.conf)
    fuente = int(args.fuente) if args.fuente.isdigit() else args.fuente
    cap = cv2.VideoCapture(fuente)
    if not cap.isOpened():
        raise SystemExit(f"No se pudo abrir la fuente: {args.fuente}")

    ultimo_envio = 0.0
    print("Presiona Q para salir.")
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        detecciones = detector.detectar(frame)
        vista = dibujar(frame.copy(), detecciones)

        if detecciones and time.time() - ultimo_envio >= args.espera:
            ultimo_envio = time.time()
            mejor = max(detecciones, key=lambda d: d["confianza"])
            _, jpg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])  # sin dibujos: el panel pinta los recuadros
            alto, ancho = frame.shape[:2]
            payload = {
                "lat": args.lat, "lon": args.lon,
                "confianza": mejor["confianza"], "severidad": mejor["severidad"], "tipo": mejor["clase"],
                "fuente": "camara", "imagen_b64": base64.b64encode(jpg.tobytes()).decode(),
                "bx": mejor["x1"] / ancho, "by": mejor["y1"] / alto,
                "bw": (mejor["x2"] - mejor["x1"]) / ancho, "bh": (mejor["y2"] - mejor["y1"]) / alto,
            }
            threading.Thread(target=enviar, args=(args.servidor, payload), daemon=True).start()

        cv2.putText(vista, f"Baches: {len(detecciones)}", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.imshow("Detector de Baches - Ecuador", vista)
        if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

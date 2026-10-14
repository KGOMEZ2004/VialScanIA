"""
Detector de baches con YOLO (Ultralytics).
Usa models/baches.pt (entrenado con entrenar.py). Si no existe, cae a yolov8n.pt en modo demostración.
"""
import os
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parent
MODELO_POR_DEFECTO = RAIZ / "models" / "baches.pt"
PALABRAS_BACHE = ("pothole", "bache", "hueco", "hole")


def severidad(area_caja: float, area_frame: float) -> str:
    ratio = area_caja / max(area_frame, 1)
    if ratio > 0.08:
        return "grave"
    if ratio > 0.03:
        return "moderado"
    return "leve"


class DetectorBaches:
    def __init__(self, modelo: str | None = None, confianza: float = 0.4):
        from ultralytics import YOLO

        ruta = Path(modelo or os.getenv("MODELO_YOLO") or MODELO_POR_DEFECTO)
        if not ruta.exists():
            print(f"[AVISO] No se encontró {ruta}. Usando yolov8n.pt (MODO DEMO: no detecta baches reales).")
            print("        Entrena tu modelo con: python entrenar.py --data <dataset.yaml>")
            ruta = Path("yolov8n.pt")

        self.modelo = YOLO(str(ruta))
        self.confianza = confianza
        nombres = self.modelo.names
        ids = [i for i, n in nombres.items() if any(p in n.lower() for p in PALABRAS_BACHE)]
        # Sin clase de bache en el modelo -> modo demo: acepta todas las clases
        self.clases_bache = ids or None
        self.modo_demo = not ids
        print(f"[YOLO] Modelo: {ruta.name} | clases bache: {[nombres[i] for i in ids] or 'TODAS (demo)'}")

    def detectar(self, frame: np.ndarray) -> list[dict]:
        h, w = frame.shape[:2]
        res = self.modelo.predict(frame, conf=self.confianza, classes=self.clases_bache, verbose=False)[0]
        detecciones = []
        for caja in res.boxes:
            x1, y1, x2, y2 = (float(v) for v in caja.xyxy[0])
            detecciones.append({
                "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                "confianza": round(float(caja.conf[0]), 3),
                "clase": self.modelo.names[int(caja.cls[0])],
                "severidad": severidad((x2 - x1) * (y2 - y1), w * h),
            })
        return detecciones


def dibujar(frame: np.ndarray, detecciones: list[dict]) -> np.ndarray:
    import cv2

    colores = {"leve": (0, 200, 255), "moderado": (0, 140, 255), "grave": (0, 0, 255)}
    for d in detecciones:
        c = colores[d["severidad"]]
        p1, p2 = (int(d["x1"]), int(d["y1"])), (int(d["x2"]), int(d["y2"]))
        cv2.rectangle(frame, p1, p2, c, 2)
        cv2.putText(frame, f"BACHE {d['confianza']:.0%} {d['severidad']}", (p1[0], max(p1[1] - 8, 15)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, c, 2)
    return frame

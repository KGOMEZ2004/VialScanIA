"""
Entrena YOLO para detectar baches.

1. Descarga un dataset de baches en formato "YOLOv8" (por ejemplo desde Roboflow Universe,
   busca "pothole detection") y descomprímelo en backend/datasets/baches/.
2. Ejecuta:  python entrenar.py --data datasets/baches/data.yaml --epochs 50
3. El mejor modelo se copia a backend/models/baches.pt (lo usan el servidor y detectar_camara.py).
"""
import argparse
import shutil
from pathlib import Path

from ultralytics import YOLO

RAIZ = Path(__file__).resolve().parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="ruta al data.yaml del dataset")
    ap.add_argument("--base", default="yolov8n.pt", help="modelo base (yolov8n/s/m.pt, yolo11n.pt...)")
    ap.add_argument("--epochs", type=int, default=50)
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--device", default=None, help="0 para GPU, cpu para CPU")
    args = ap.parse_args()

    modelo = YOLO(args.base)
    modelo.train(data=args.data, epochs=args.epochs, imgsz=args.imgsz, batch=args.batch,
                 device=args.device, project=str(RAIZ / "runs"), name="baches", exist_ok=True)

    mejor = RAIZ / "runs" / "baches" / "weights" / "best.pt"
    destino = RAIZ / "models" / "baches.pt"
    destino.parent.mkdir(exist_ok=True)
    shutil.copy(mejor, destino)
    print(f"Modelo listo en {destino}")
    print(modelo.val().results_dict)


if __name__ == "__main__":
    main()

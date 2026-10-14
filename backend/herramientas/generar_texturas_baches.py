"""
Genera texturas procedurales para la escena de Unity:
  - Asfalto.png: asfalto con líneas de carril (un tile = 8 m x 8 m de carretera).
  - Bache_0..3.png: baches con transparencia (bordes rotos, grava, fondo oscuro, a veces agua).

  python herramientas/generar_texturas_baches.py
"""
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

SALIDA = Path(__file__).resolve().parents[2] / "repo_unity" / "Assets" / "Baches" / "Texturas"


def ruido(tam, escala, semilla, base=0, amp=40):
    """Ruido de valor suavizado (sin dependencias)."""
    rnd = random.Random(semilla)
    peq = Image.new("L", (max(2, tam // escala), max(2, tam // escala)))
    peq.putdata([128 + base + rnd.randint(-amp, amp) for _ in range(peq.width * peq.height)])
    return peq.resize((tam, tam), Image.BICUBIC)


def asfalto(tam=1024):
    img = Image.new("RGB", (tam, tam), (78, 78, 82))
    capa = Image.merge("RGB", [ruido(tam, 4, 1, -48, 25)] * 3)
    img = Image.blend(img, capa, 0.35)
    # Gránulos de piedra
    rnd = random.Random(7)
    d = ImageDraw.Draw(img)
    for _ in range(tam * 60):
        x, y = rnd.randrange(tam), rnd.randrange(tam)
        g = rnd.randint(40, 150)
        d.point((x, y), fill=(g, g, g + 3))
    img = img.filter(ImageFilter.GaussianBlur(0.6))
    d = ImageDraw.Draw(img)
    m = tam / 8  # píxeles por metro
    # Líneas blancas de borde (0.15 m de ancho): simple a la izquierda, doble a la derecha (como en el diseño)
    for x0 in (0.3, 0.6, 8 - 0.45):   # Unity refleja la textura en la calzada: la doble queda a la derecha
        d.rectangle([x0 * m, 0, (x0 + 0.15) * m, tam], fill=(225, 225, 220))
    # Línea central blanca discontinua: 3 m pintado, 5 m libre
    d.rectangle([3.92 * m, 0.5 * m, 4.08 * m, 3.5 * m], fill=(232, 232, 226))
    return img.filter(ImageFilter.GaussianBlur(0.8))


def bache(semilla, tam=512):
    rnd = random.Random(semilla)
    c = tam / 2
    armonicos = [(k, rnd.uniform(0.02, 0.09) / k ** 0.5, rnd.uniform(0, 6.28)) for k in range(2, 9)]

    def radio(a):
        return 0.36 * tam * (1 + sum(amp * math.sin(k * a + fase) for k, amp, fase in armonicos))

    contorno = [(c + radio(a) * math.cos(a), c + radio(a) * math.sin(a))
                for a in (i * 2 * math.pi / 180 for i in range(180))]

    alfa = Image.new("L", (tam, tam), 0)
    ImageDraw.Draw(alfa).polygon(contorno, fill=255)
    alfa = alfa.filter(ImageFilter.GaussianBlur(3))

    # Profundidad: más oscuro hacia el centro
    prof = Image.new("L", (tam, tam), 0)
    dp = ImageDraw.Draw(prof)
    for i in range(30, 0, -1):
        f = i / 30
        dp.polygon([(c + (x - c) * f, c + (y - c) * f) for x, y in contorno], fill=int(255 * (1 - f) ** 0.6))
    prof = prof.filter(ImageFilter.GaussianBlur(10))

    fondo = Image.merge("RGB", [ruido(tam, 6, semilla, 0, 30)] * 3)
    img = Image.new("RGB", (tam, tam))
    px, pf, pp = img.load(), fondo.load(), prof.load()
    agua = rnd.random() < 0.4
    for y in range(tam):
        for x in range(tam):
            n = pf[x, y][0] - 128
            p = pp[x, y] / 255
            base = 88 - 66 * p + n * 0.5
            r, g, b = base + 10, base + 5, base
            if agua and p > 0.55:
                r, g, b = 35 + n * 0.3, 42 + n * 0.3, 48 + n * 0.3
            px[x, y] = (int(max(0, r)), int(max(0, g)), int(max(0, b)))

    d = ImageDraw.Draw(img)
    # Grava suelta dentro del bache
    for _ in range(260):
        a, rr = rnd.uniform(0, 6.28), rnd.uniform(0, 0.9)
        x, y = c + radio(a) * rr * math.cos(a), c + radio(a) * rr * math.sin(a)
        s, g = rnd.uniform(1.5, 5), rnd.randint(60, 115)
        d.ellipse([x - s, y - s, x + s, y + s], fill=(g, g - 3, g - 8))
    # Borde de asfalto roto (más claro)
    d.line(contorno + [contorno[0]], fill=(115, 112, 108), width=7)
    # Grietas que salen del borde
    grietas = Image.new("L", (tam, tam), 0)
    dg = ImageDraw.Draw(grietas)
    for _ in range(rnd.randint(4, 8)):
        a = rnd.uniform(0, 6.28)
        x, y = c + radio(a) * math.cos(a), c + radio(a) * math.sin(a)
        for _ in range(rnd.randint(4, 9)):
            a += rnd.uniform(-0.6, 0.6)
            nx, ny = x + 14 * math.cos(a), y + 14 * math.sin(a)
            d.line([x, y, nx, ny], fill=(25, 25, 25), width=3)
            dg.line([x, y, nx, ny], fill=255, width=4)
            x, y = nx, ny
    img = img.filter(ImageFilter.GaussianBlur(0.7))
    img.putalpha(Image.composite(Image.new("L", (tam, tam), 255), alfa, grietas))
    return img


def grieta(semilla, ancho=256, alto=1024):
    """Grieta longitudinal con ramificaciones (transparente fuera de la grieta)."""
    rnd = random.Random(semilla)
    alfa = Image.new("L", (ancho, alto), 0)
    color = Image.new("RGB", (ancho, alto), (30, 27, 25))
    da, dc = ImageDraw.Draw(alfa), ImageDraw.Draw(color)

    def trazo(x, y, ang, largo, grosor):
        pts = [(x, y)]
        for _ in range(int(largo / 18)):
            ang = ang * 0.8 + rnd.uniform(-0.45, 0.45)
            x, y = x + 18 * math.sin(ang), y + 18 * math.cos(ang)
            pts.append((x, y))
            if grosor > 5 and rnd.random() < 0.12:
                trazo(x, y, ang + rnd.choice((-1, 1)) * rnd.uniform(0.6, 1.2), largo * 0.3, grosor * 0.5)
        da.line(pts, fill=255, width=int(grosor + 4))
        dc.line(pts, fill=(70, 66, 62), width=int(grosor + 4))
        dc.line(pts, fill=(22, 20, 19), width=int(grosor))

    trazo(ancho / 2, 20, 0, alto - 60, 9)
    return Image.merge("RGBA", (*color.filter(ImageFilter.GaussianBlur(0.6)).split(), alfa.filter(ImageFilter.GaussianBlur(1.2))))


def hundimiento(semilla, tam=512):
    """Zona hundida: mancha oscura de bordes suaves con fisuras en el contorno."""
    rnd = random.Random(semilla)
    c = tam / 2
    alfa = Image.new("L", (tam, tam), 0)
    da = ImageDraw.Draw(alfa)
    for i in range(40, 0, -1):
        f = i / 40
        da.ellipse([c - c * 0.92 * f, c - c * 0.7 * f, c + c * 0.92 * f, c + c * 0.7 * f], fill=int(210 * (1 - f) ** 0.35))
    alfa = alfa.filter(ImageFilter.GaussianBlur(14))
    base = Image.merge("RGB", [ruido(tam, 8, semilla, -80, 18)] * 3)
    d = ImageDraw.Draw(base)
    for _ in range(9):
        a = rnd.uniform(0, 6.28)
        x, y = c + c * 0.75 * math.cos(a), c + c * 0.55 * math.sin(a)
        for _ in range(4):
            a += rnd.uniform(-0.7, 0.7)
            nx, ny = x + 16 * math.cos(a), y + 16 * math.sin(a)
            d.line([x, y, nx, ny], fill=(18, 17, 16), width=3)
            x, y = nx, ny
    return Image.merge("RGBA", (*base.split(), alfa))


def fachada(pared, tam=(256, 192)):
    """Tile de fachada: 4 m de ancho x 3 m de alto (una ventana por piso)."""
    w, h = tam
    img = Image.new("RGB", tam, pared)
    img = Image.blend(img, Image.merge("RGB", [ruido(w, 16, sum(pared), -20, 12).resize(tam)] * 3), 0.12)
    d = ImageDraw.Draw(img)
    d.rectangle([w * 0.22, h * 0.2, w * 0.78, h * 0.78], fill=(62, 74, 92))          # vidrio
    d.polygon([(w * 0.22, h * 0.2), (w * 0.5, h * 0.2), (w * 0.3, h * 0.78), (w * 0.22, h * 0.78)], fill=(88, 104, 128))
    d.rectangle([w * 0.2, h * 0.78, w * 0.8, h * 0.83], fill=tuple(max(0, v - 35) for v in pared))  # alféizar
    d.line([w * 0.5, h * 0.2, w * 0.5, h * 0.78], fill=(45, 52, 63), width=3)
    d.rectangle([0, h - 4, w, h], fill=tuple(max(0, v - 18) for v in pared))
    return img


def main():
    SALIDA.mkdir(parents=True, exist_ok=True)
    asfalto().save(SALIDA / "Asfalto.png")
    for i in range(4):
        bache(100 + i).save(SALIDA / f"Bache_{i}.png")
    for i in range(3):
        grieta(200 + i).save(SALIDA / f"Grieta_{i}.png")
    for i in range(2):
        hundimiento(300 + i).save(SALIDA / f"Hundimiento_{i}.png")
    fachada((184, 167, 143)).save(SALIDA / "Fachada_Beige.png")
    fachada((168, 151, 127)).save(SALIDA / "Fachada_Arena.png")
    fachada((174, 180, 189)).save(SALIDA / "Fachada_Gris.png")
    fachada((158, 165, 174)).save(SALIDA / "Fachada_Azul.png")
    print(f"Texturas guardadas en {SALIDA}")


if __name__ == "__main__":
    main()

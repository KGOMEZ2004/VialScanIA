"""
Escena ilustrada de una calle (SVG 1000x1000) al estilo del diseño de VialScan.
Se usa en el login y como fotogramas de los recorridos de ejemplo. Cada variante devuelve
también los daños con su recuadro normalizado (0-1), alineado con lo que se dibuja.
"""

# Daños por variante: ("bache", cx, cy, rx, ry, confianza, severidad) | ("grieta", x, y0, y1, confianza, severidad)
# confianza None = daño visible que la IA no detectó (para marcarlo a mano)
VARIANTES = {
    0: [("bache", 380, 760, 75, 22, None, None), ("bache", 530, 690, 38, 12, None, None),
        ("bache", 440, 905, 105, 34, None, None), ("grieta", 690, 730, 990, None, None)],
    1: [("bache", 430, 880, 95, 32, 0.95, "alta"), ("bache", 560, 690, 40, 13, 0.91, "alta"),
        ("grieta", 655, 740, 950, 0.88, "media"), ("bache", 330, 765, 70, 22, None, None)],
    2: [("bache", 620, 830, 85, 27, 0.93, "alta"), ("bache", 470, 700, 45, 14, 0.84, "media"),
        ("grieta", 360, 760, 960, 0.79, "baja")],
    3: [("bache", 520, 900, 115, 36, 0.97, "alta"), ("bache", 640, 730, 35, 11, 0.72, "baja")],
    4: [("grieta", 560, 700, 980, 0.9, "media"), ("bache", 360, 850, 62, 20, 0.86, "media")],
}


def _dashes():
    """Línea central discontinua en perspectiva."""
    x0, y0, x1, y1 = 522, 565, 330, 1000
    partes = []
    for a, b in [(0.02, 0.045), (0.09, 0.14), (0.22, 0.32), (0.43, 0.6), (0.78, 1.05)]:
        pts = []
        for t, lado in [(a, -1), (b, -1), (b, 1), (a, 1)]:
            w = 1.5 + 9 * t
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            pts.append(f"{x + lado * w:.1f},{y:.1f}")
        partes.append(f'<polygon points="{" ".join(pts)}" fill="#e9e9e4"/>')
    return "".join(partes)


def _bache(cx, cy, rx, ry):
    return (f'<g><ellipse cx="{cx}" cy="{cy + ry * 0.15}" rx="{rx * 1.14}" ry="{ry * 1.3}" fill="#2b2d31" opacity=".85"/>'
            f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="#46484d"/>'
            f'<ellipse cx="{cx}" cy="{cy + ry * 0.08}" rx="{rx * 0.84}" ry="{ry * 0.74}" fill="url(#hueco)"/>'
            f'<ellipse cx="{cx}" cy="{cy + ry * 0.2}" rx="{rx * 0.38}" ry="{ry * 0.22}" fill="#5b4747" opacity=".55"/></g>')


def _grieta(x, y0, y1):
    pasos = 7
    pts, ramas = [], []
    for i in range(pasos + 1):
        y = y0 + (y1 - y0) * i / pasos
        dx = (-12, 10, -6, 14, -10, 8, -4, 12)[i]
        pts.append(f"{x + dx},{y:.0f}")
        if i in (2, 4, 6):
            ramas.append(f'<path d="M{x + dx},{y:.0f} l{18 if i % 4 else -20},{14}" stroke="#2a2522" stroke-width="3" fill="none"/>')
    return (f'<polyline points="{" ".join(pts)}" stroke="#2a2522" stroke-width="4" fill="none" stroke-linejoin="round"/>'
            + "".join(ramas))


def _caja(d):
    """Recuadro normalizado (x, y, ancho, alto) del daño."""
    if d[0] == "bache":
        _, cx, cy, rx, ry, *_ = d
        return [(cx - rx * 1.2) / 1000, (cy - ry * 1.45) / 1000, rx * 2.4 / 1000, ry * 2.9 / 1000]
    _, x, y0, y1, *_ = d
    return [(x - 32) / 1000, (y0 - 12) / 1000, 64 / 1000, (y1 - y0 + 24) / 1000]


def escena_svg(variante: int = 0) -> str:
    danos = VARIANTES.get(variante, VARIANTES[0])
    arbol = lambda x, y, r, h: (f'<rect x="{x - 7}" y="{y}" width="14" height="{h}" fill="#5b4332"/>'
                                f'<circle cx="{x}" cy="{y}" r="{r}" fill="#3f8a3a"/>'
                                f'<circle cx="{x - r * 0.3}" cy="{y - r * 0.3}" r="{r * 0.55}" fill="#4d9a45" opacity=".7"/>')
    elementos = "".join(_bache(*d[1:5]) if d[0] == "bache" else _grieta(*d[1:4]) for d in danos)
    parche = '<polygon points="400,930 560,905 578,988 392,1000" fill="#34373c" opacity=".75"/>' if variante == 1 else ""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 1000" width="1000" height="1000">
<defs>
  <linearGradient id="cielo" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#7fa6cf"/><stop offset="1" stop-color="#d3e3ef"/></linearGradient>
  <linearGradient id="asfalto" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3b3e44"/><stop offset="1" stop-color="#5d6066"/></linearGradient>
  <radialGradient id="hueco" cx=".5" cy=".45" r=".6"><stop offset="0" stop-color="#1a1416"/><stop offset=".7" stop-color="#241c1d"/><stop offset="1" stop-color="#3a3032"/></radialGradient>
</defs>
<rect width="1000" height="600" fill="url(#cielo)"/>
<ellipse cx="160" cy="45" rx="170" ry="38" fill="#fff" opacity=".45"/>
<ellipse cx="330" cy="25" rx="110" ry="28" fill="#fff" opacity=".35"/>
<ellipse cx="880" cy="95" rx="150" ry="36" fill="#fff" opacity=".45"/>
<g fill="#8d9db2" opacity=".85">
  <rect x="330" y="455" width="45" height="110"/><rect x="372" y="480" width="40" height="85"/><rect x="408" y="500" width="30" height="65"/>
  <rect x="595" y="470" width="40" height="95"/><rect x="630" y="440" width="45" height="125"/><rect x="560" y="505" width="38" height="60"/>
</g>
<polygon points="0,120 335,420 335,585 0,770" fill="#b8a78f"/>
<polygon points="0,420 170,470 170,690 0,770" fill="#a8977f"/>
<polygon points="200,330 250,345 250,400 200,390" fill="#6d7686"/>
<polygon points="1000,110 690,420 690,585 1000,770" fill="#aeb4bd"/>
<polygon points="1000,430 830,480 830,690 1000,770" fill="#9ea5ae"/>
<polygon points="800,330 750,345 750,400 800,390" fill="#6d7686"/>
<polygon points="0,770 335,585 690,585 1000,770 1000,1000 0,1000" fill="#c7c2b9"/>
<polygon points="468,560 578,560 1000,905 1000,1000 0,1000 0,835" fill="url(#asfalto)"/>
<polyline points="468,560 0,835" stroke="#ecebe6" stroke-width="7" fill="none"/>
<polyline points="578,560 1000,905" stroke="#ecebe6" stroke-width="7" fill="none"/>
<polyline points="570,560 980,905" stroke="#ecebe6" stroke-width="4" fill="none"/>
{_dashes()}
<g stroke="#4a4d52" stroke-width="7" fill="none"><path d="M335,590 V410 H365"/><path d="M690,590 V410 H660"/></g>
{arbol(60, 330, 110, 250)}{arbol(190, 400, 80, 150)}{arbol(940, 330, 110, 250)}{arbol(810, 400, 80, 150)}
<g><rect x="478" y="590" width="74" height="44" rx="7" fill="#b3202a"/><rect x="486" y="595" width="58" height="13" rx="3" fill="#3a1418"/>
<rect x="484" y="614" width="10" height="6" fill="#ff5a5a"/><rect x="536" y="614" width="10" height="6" fill="#ff5a5a"/>
<rect x="505" y="617" width="20" height="7" fill="#f2f2f2"/><rect x="480" y="632" width="12" height="7" fill="#161616"/><rect x="538" y="632" width="12" height="7" fill="#161616"/></g>
{parche}{elementos}
<path d="M0,1000 L0,962 Q500,922 1000,962 L1000,1000 Z" fill="#0e1013"/>
</svg>'''


def danos_detectables(variante: int) -> list[dict]:
    """Daños que la 'IA' detecta en la variante (los de confianza None se dejan para marcar a mano)."""
    salida = []
    for d in VARIANTES.get(variante, []):
        conf, sev = d[-2], d[-1]
        if conf is None or d[0] == "grieta":   # grietas: se marcan a mano
            continue
        salida.append({"tipo": d[0], "confianza": conf, "severidad": sev, "caja": [round(v, 4) for v in _caja(d)]})
    return salida

# 🚧 VialScan AI — Detector de baches Ecuador (YOLO + Unity + Google Maps)

Panel de mantenimiento vial: los vehículos (cámara con **YOLO** o el simulador de **Unity**) detectan baches, grietas y
hundimientos; el panel web los agrupa en **recorridos**, los ubica en el **mapa de Ecuador** (provincia, cantón, **IP de la zona**)
y el equipo municipal los **valida, asigna a cuadrillas y marca como reparados**.

```
 Unity (vehículo + cámara) ──┐  POST /api/baches, /api/detectar
 Cámara real (YOLO) ─────────┼──────────────────────────────► Servidor FastAPI ──► SQLite
                             │                                  │ recorridos → fotogramas → daños
                             │                                  │ provincia, cantón, IP (Nominatim, ip-api)
 Panel web (login) ◄─────────┴──────── WebSocket tiempo real ───┘ reportes y PDF
```

## ✅ Guía de instalación paso a paso

Sigue los pasos **en orden**. Los pasos 1 a 5 son obligatorios (servidor + panel web); el 6 (Unity), el 7 (YOLO real),
el 8 (Google Maps) y el 9 (cámara real) son opcionales.

### Paso 0 — Requisitos

| Programa | Versión | Para qué | Obligatorio |
|---|---|---|---|
| [Python](https://www.python.org/downloads/) | **3.10 o superior** (probado con 3.13) | Servidor y panel web | Sí |
| Navegador (Chrome, Edge, Firefox) | Reciente | Panel web | Sí |
| Conexión a internet | — | Instalar paquetes; ubicar provincia/cantón/IP (Nominatim, ip-api) y mapas | Sí (recomendado) |
| [Unity Hub](https://unity.com/download) + **Unity 6000.6.3f1** (Unity 6, URP) | La del proyecto | Simulador del vehículo | No |
| GPU NVIDIA con CUDA | — | Entrenar YOLO más rápido | No |

> Al instalar Python en Windows marca **"Add python.exe to PATH"**. Comprueba con `python --version` en PowerShell.

### Paso 1 — Abrir una terminal en la carpeta del servidor

```powershell
cd "C:\Users\<tu usuario>\OneDrive\Escritorio\PROYECTO HUECOS XD\backend"
```

(O en VS Code: *Terminal › Nueva terminal* y luego `cd backend`.)

### Paso 2 — Crear un entorno virtual (recomendado)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Debe aparecer `(.venv)` al inicio de la línea. Si PowerShell bloquea el script, ejecuta una vez:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

`iniciar_servidor.bat` activa automáticamente `backend\.venv` si existe.

### Paso 3 — Instalar las dependencias (solo la primera vez)

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Esto instala FastAPI, Uvicorn, OpenCV, NumPy y **Ultralytics (YOLO)**. Ultralytics descarga PyTorch (~1–2 GB), así que
puede tardar varios minutos.

> **Instalación ligera** (sin YOLO, el sistema funciona en *modo simulado*):
> `pip install fastapi "uvicorn[standard]" python-multipart requests numpy opencv-python`

### Paso 4 — Arrancar el servidor

Opción A — doble clic en **`iniciar_servidor.bat`** (en la raíz del proyecto). Abre el navegador solo.

Opción B — desde la terminal, dentro de `backend` y con el entorno activado:

```powershell
python -m uvicorn app:app --host 0.0.0.0 --port 8000
```

En la consola debe verse algo como:

```
[VialScan] Cuenta creada: admin / Xq3v9LmT2wPa  (cámbiala en Configuración > Mi cuenta)
[VialScan] Código para registrar administradores: 123456  (también en Configuración > Sistema)
[VialScan] Token de dispositivos (Unity / cámara): 9fK2...
INFO:     Uvicorn running on http://0.0.0.0:8000
```

La primera vez se crea solo `backend/baches.db` (base SQLite) con los datos de ejemplo y la carpeta `backend/capturas/`.
**Apunta las contraseñas de las cuentas creadas**: son aleatorias y solo se muestran esa vez (ver *Cuentas iniciales*).
**No cierres esta ventana** mientras uses el sistema (para detenerlo: `Ctrl + C`).

### Paso 5 — Entrar al panel web

1. Abre **http://127.0.0.1:8000** en el navegador.
2. Escribe correo y contraseña de una de las cuentas iniciales (las que mostró la consola) y **elige el rol correcto**.
3. Verás la pantalla *Recorridos* con los recorridos de ejemplo de Milagro (Guayas).

Con esto el programa ya funciona. Para generar daños de prueba sin Unity ni cámara, abre **otra** terminal (con el
entorno activado, dentro de `backend`) y ejecuta:

```powershell
python simular.py --cantidad 15 --token <TOKEN>
```

`<TOKEN>` es el **token de dispositivos** que muestra la consola al arrancar (también en *Configuración › Sistema*).
Puedes definirlo una vez con `$env:VIALSCAN_TOKEN_DISPOSITIVO = "<TOKEN>"` y omitir `--token`.

### Paso 6 — (Opcional) Simulador de Unity

`repo_unity/` es un proyecto de Unity completo.

1. Abre **Unity Hub › Add › Add project from disk** y elige la carpeta `repo_unity`.
   Usa la versión **6000.6.3f1** (si Hub lo pide, instálala). La primera apertura tarda porque reconstruye `Library/`.
2. Abre la escena `Assets/Scenes/SampleScene`.
3. En el menú superior elige **Baches › Configurar escena** (crea calle, vehículo, cámara, GPS y detector).
4. Copia el **token de dispositivos** (consola del servidor o *Configuración › Sistema*) en el campo
   **Token Dispositivo** de los componentes `CamaraDetectorYOLO` y `BachesEnMapa`.
5. Comprueba que el servidor del **Paso 4** está corriendo.
6. Pulsa **Play** y conduce con **W / A / S / D**.
7. En el panel web aparece un recorrido nuevo con **● EN VIVO** (cámara + mapa GPS).

Notas:
- Si usas tu propio proyecto de Unity 6 + URP, copia `repo_unity/Assets/Baches` dentro de su `Assets/` y sigue desde el punto 3.
- Si Unity muestra *401* o *"Token de dispositivo incorrecto"*, revisa el campo **Token Dispositivo**.
- Si Unity corre en **otra PC**, cambia el campo `servidor` (por defecto `http://127.0.0.1:8000`) en los componentes
  `CamaraDetectorYOLO` y `BachesEnMapa` por la IP de la PC del servidor (p. ej. `http://192.168.1.20:8000`) y permite el
  puerto 8000 en el Firewall de Windows.
- Si Unity muestra *"Servidor no disponible"*, el servidor no está encendido o la dirección es incorrecta.

### Paso 7 — (Opcional) Detección real con YOLO

El repositorio ya incluye un modelo entrenado en **`backend/models/baches.pt`** (YOLO11n de segmentación, clases
`pothole` y `Crack`; el servidor solo usa `pothole`). Sin ese archivo, el servidor usa `yolov8n.pt` en
**modo demostración** y Unity pasa a **modo simulado**. Para entrenar un modelo propio:

1. Descarga un dataset de baches ("pothole") de [Roboflow](https://universe.roboflow.com/) en formato **YOLOv8** y
   descomprímelo en `backend/datasets/baches/` (debe contener `data.yaml`).
2. Entrena (dentro de `backend`):

   ```powershell
   python entrenar.py --data datasets/baches/data.yaml --epochs 50            # CPU
   python entrenar.py --data datasets/baches/data.yaml --epochs 50 --device 0 # GPU NVIDIA
   ```

3. Verifica que el modelo quedó en **`backend/models/baches.pt`** (o indica otra ruta con la variable `MODELO_YOLO`).
4. Reinicia el servidor (Paso 4).

### Paso 8 — (Opcional) Google Maps con API key

Sin clave el sistema funciona (Google Maps embebido + enlaces). Para mapas grandes de Google Maps:

1. En Google Cloud Console activa **Maps JavaScript API** y crea una API key.
2. Pégala (solo la clave, en una línea) en `backend/google_maps_key.txt`, o defínela en la variable de entorno
   `GOOGLE_MAPS_API_KEY`.
3. Reinicia el servidor. *Configuración* muestra el estado de los mapas.

> `google_maps_key.txt` está en `.gitignore`: no lo subas a GitHub.

### Paso 9 — (Opcional) Cámara real

Con el servidor corriendo y YOLO instalado:

```powershell
python detectar_camara.py --token <TOKEN> --lat -2.13 --lon -79.58             # webcam 0
python detectar_camara.py --token <TOKEN> --fuente video.mp4 --lat -2.13 --lon -79.58
```

Opciones: `--fuente` (índice de webcam, video o URL rtsp/http), `--modelo`, `--conf 0.45`, `--servidor`, `--espera 3`, `--token`.
Sin `--lat/--lon` la ubicación se estima por la IP.

### Herramientas extra (solo si modificas la escena de Unity)

```powershell
pip install pillow
python herramientas/generar_texturas_baches.py   # texturas de asfalto y baches
python herramientas/generar_mapa_unity.py        # mapa de Ecuador para Unity
```

### Problemas frecuentes

| Problema | Solución |
|---|---|
| `python` no se reconoce | Reinstala Python marcando *Add to PATH*, o usa `py` en lugar de `python` |
| `No module named fastapi` / `uvicorn` | Activa el entorno (`.\.venv\Scripts\Activate.ps1`) y repite el Paso 3 |
| `address already in use` / puerto 8000 ocupado | Cierra el otro servidor o usa `--port 8001` (y cambia la URL en Unity) |
| No puedo iniciar sesión | Revisa que el **rol** elegido coincide con la cuenta |
| No sé el código de administrador o el token | Aparecen en la consola al arrancar y en *Configuración › Sistema* |
| No sé la contraseña inicial | Solo se muestra al crear la base: borra `backend/baches.db` y arranca de nuevo |
| `[AVISO] ... contraseña de prueba antigua` | Tu base es de una versión anterior con `admin123`, etc.: cámbiala en *Configuración* |
| Provincia/cantón vacíos | Falta internet (Nominatim / ip-api) |
| Unity: "Servidor no disponible" | Arranca el servidor (Paso 4) y revisa el campo `servidor` |
| "MODO DEMO" / modo simulado | Normal sin `models/baches.pt`; ver Paso 7 |
| Quiero empezar de cero | Detén el servidor y borra `backend/baches.db` y `backend/capturas/` (se recrean al arrancar) |

## Cuentas iniciales

Al crear la base, el servidor crea estas cuentas con una **contraseña aleatoria** que muestra **una sola vez** en la
consola (cámbiala en *Configuración › Mi cuenta*). Para fijarla tú, define `VIALSCAN_CONTRASENA_INICIAL` antes de arrancar.

| Rol | Correo | Puede |
|---|---|---|
| Administrador | `admin` | Todo: validar, editar, eliminar, asignar cuadrillas, usuarios |
| Administrador | `c.ruiz@milagro.gob.ec` | Igual que el anterior |
| Técnico de mantenimiento | `m.torres@milagro.gob.ec` | Ver, marcar daños a mano, marcar reparado, reportes |

En el login hay que elegir el **rol** de la cuenta.

**Crear cuenta**: en el login, *¿No tienes cuenta? Crear una*. Cualquiera puede registrarse como Técnico; para
registrarse como Administrador se necesita el **código de administrador** (6 dígitos), que aparece en la consola al
arrancar el servidor y en *Configuración › Sistema* (desde ahí se puede generar uno nuevo).

## Pantallas

| Pantalla | Qué hace |
|---|---|
| **Inicio de sesión** | Correo, contraseña y rol |
| **Recorridos** | Recorridos recibidos (código `PRJ-AAAA-NN`, nº de daños, estado). *Subir recorrido* con fotos propias |
| **Resultados del análisis** | Cámara con recuadros de la IA · *Mapa GPS* · lista de anomalías · detalle del daño (validar, asignar cuadrilla, reparado) · editar (tipo, largo × ancho, profundidad, severidad) · eliminar con confirmación · **marcar daño manualmente** arrastrando sobre la imagen · *Guardar reporte* · *Exportar PDF* |
| **Mapas** | Todos los daños en Google Maps con filtros; detalle con Google Maps embebido, Street View y *Cómo llegar* |
| **Reportes** | Reportes guardados → PDF (vista imprimible: *Guardar como PDF*) |
| **Configuración** | Mi cuenta (contraseña), cuadrillas, usuarios (admin), estado de IA / mapas / tiempo real |

Los recorridos de ejemplo (Milagro, Guayas) usan una escena ilustrada. Los baches que registraste con la versión anterior
se importan solos al recorrido **"Registros anteriores"**.

## Unity en vivo en la página web

Mientras conduces en Unity, el panel muestra el recorrido con **● EN VIVO**:
- **Cámara**: lo que ve la cámara del vehículo (~3 fotogramas/s) con los recuadros de detección, GPS y velocidad.
  *Ver fotogramas guardados* muestra la foto de cada daño registrado.
- **Mapa GPS**: el vehículo (punto azul) avanzando, su ruta y los daños detectados.

La escena de Unity reproduce la calle del diseño: edificios con ventanas, veredas, árboles, postes, auto rojo delante,
capó del vehículo, y daños de tres tipos (baches, grietas, hundimientos).

## Recorridos al azar y grietas manuales

- **Cada Play de Unity es un recorrido nuevo y distinto**: se elige al azar una avenida real de Ecuador
  (`repo_unity/Assets/Baches/Datos/rutas_ecuador.json`: Quito, Cuenca, Ambato, Loja, Manta y Milagro, trazados de
  OpenStreetMap) y se generan al azar la calle (edificios, árboles, postes) y los daños. El GPS sigue el trazado real.
  Para repetir siempre lo mismo: desactiva `aleatorio` (GeneradorCiudad / GeneradorBaches) y `rutaAleatoria` (GPSSimulado).
- **Las grietas no se registran solas** (ni Unity, ni YOLO, ni los ejemplos): las marca una persona.
  En un recorrido en vivo pulsa **📸 Capturar y marcar** (o *Marcar daño manualmente*): se congela el fotograma actual,
  arrastras sobre la grieta y se guarda como daño manual (el tipo empieza en *Grieta*).

## Cómo llegan los recorridos

- **Unity**: cada vehículo que envía detecciones abre un recorrido *En proceso*, nombrado por la calle
  (p. ej. "Diego Noboa – Barrio Batán Alto"). Tras 10 min sin detecciones pasa a *Completado*.
  Unity envía la foto, el recuadro del bache, su tamaño y la velocidad.
- **Cámara real**: `python detectar_camara.py --token <TOKEN> --lat -2.13 --lon -79.58` (necesita el modelo YOLO).
- **Fotos subidas** desde el panel: quedan *Sin procesar* hasta pulsar **Analizar con IA** (necesita YOLO).
- Un daño a menos de 8 m de otro no reparado se cuenta como el mismo (suma "reportes").

## Modelo YOLO

Sin `ultralytics` o sin modelo de baches, Unity usa el **modo simulado** (el panel lo indica abajo a la izquierda).
Para detección real:

```powershell
pip install ultralytics opencv-python
python entrenar.py --data datasets/baches/data.yaml --epochs 50   # dataset "pothole" de Roboflow en formato YOLOv8
```

El modelo queda en `backend/models/baches.pt` (reemplaza al incluido).

## Google Maps

Sin API key: el detalle de cada daño muestra Google Maps embebido + enlaces. Con API key (Maps JavaScript API) en
`backend/google_maps_key.txt`, los mapas grandes también son Google Maps (estilo oscuro).

## Unity (proyecto "Verificador de baches", Unity 6 + URP)

El proyecto está en `repo_unity/` (ver Paso 6). En otro proyecto: copia `repo_unity/Assets/Baches` a `Assets/`, menú **Baches → Configurar escena**, arranca el servidor y pulsa **Play**
(W/A/S/D). Modos del detector (`CamaraDetectorYOLO`): *Automático* (YOLO si hay modelo; si no, simulado), *YOLO*, *Simulado*.

## Estructura

| Archivo | Contenido |
|---|---|
| `backend/app.py` | API: login y roles, recorridos, daños, reportes, cuadrillas, usuarios, dispositivos, WebSocket |
| `backend/db.py` | Esquema SQLite, contraseñas (PBKDF2), datos de ejemplo, migración de la versión anterior |
| `backend/escena_demo.py` | Escena ilustrada (login y fotogramas de ejemplo) con recuadros alineados |
| `backend/geo_ecuador.py` | Provincia, cantón, calle y sector (Nominatim) e IP de la zona (ipify + ip-api) |
| `backend/yolo_detector.py`, `entrenar.py`, `detectar_camara.py`, `simular.py` | IA y pruebas |
| `web/index.html`, `web/js/*.js`, `web/css/vialscan.css` | Panel (SPA sin framework) |
| `web/reporte.html` | Reporte imprimible / PDF |
| `backend/tests/` | Pruebas automáticas (pytest) |
| `repo_unity/` | Proyecto de Unity 6 (URP); lo propio está en `Assets/Baches/` |

## API principal

| Método | Ruta | Uso |
|---|---|---|
| POST | `/api/auth/login` | `{correo, contrasena, rol}` → token (enviar `Authorization: Bearer <token>`) |
| GET | `/api/recorridos`, `/api/recorridos/{id}` | Lista / detalle con fotogramas y daños |
| POST | `/api/recorridos` · `/api/recorridos/{id}/procesar` | Subir fotos · analizar con IA |
| POST | `/api/recorridos/{id}/danos` | Daño manual `{fotograma_id, tipo, caja, largo_cm, ancho_cm, profundidad_cm, severidad}` |
| PUT / DELETE | `/api/danos/{id}` | Editar / eliminar (admin) |
| POST | `/api/danos/{id}/estado` | `{accion: validar\|asignar\|reparar\|reabrir, cuadrilla}` |
| POST / GET | `/api/recorridos/{id}/reportes` · `/api/reportes` | Guardar / listar reportes |
| GET / POST | `/api/baches` · POST `/api/detectar`, `/api/vivo` | Dispositivos (Unity, cámara): cabecera `X-Token-Dispositivo: <token>` |
| GET | `/api/admin/token-dispositivo[?regenerar=true]` | Ver / cambiar el token de dispositivos (admin) |
| GET | `/api/estado`, `/api/config` | Estado de YOLO · API key de Maps |
| WS | `/ws?token=` | Eventos de daños y recorridos |

> Seguridad: el panel exige sesión y los dispositivos, el token. Aun así está pensado para red local: no expongas el
> puerto 8000 a internet sin HTTPS (el token y las contraseñas viajan en claro por HTTP).

## Pruebas

```powershell
cd backend
pip install -r requirements-test.txt
python -m pytest tests -v
```

Usan una base temporal y no necesitan internet ni YOLO. GitHub Actions las ejecuta en cada *push*
(`.github/workflows/pruebas.yml`), junto con una revisión de sintaxis de `web/js`.

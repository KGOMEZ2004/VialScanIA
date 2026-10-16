using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.Text;
using UnityEngine;
using UnityEngine.Networking;

public enum ModoDeteccion
{
    [Tooltip("Usa YOLO; si el servidor no tiene YOLO instalado, pasa a Simulado")]
    Automatico,
    YOLO,
    [Tooltip("Sin YOLO: detecta los BacheVirtual visibles para probar el sistema completo")]
    Simulado,
}

/// <summary>
/// Cámara frontal del vehículo:
/// - Detecta daños (YOLO en el servidor o modo Simulado) y registra cada uno con provincia, cantón e IP.
/// - Transmite en vivo lo que ve (POST /api/vivo) para verlo en el panel web: Cámara / Mapa GPS.
/// </summary>
[RequireComponent(typeof(Camera))]
public class CamaraDetectorYOLO : MonoBehaviour
{
    public string servidor = "http://127.0.0.1:8000";
    [Tooltip("Token de dispositivo: panel web > Configuración > Sistema, o consola del servidor")]
    public string tokenDispositivo = "";
    public ModoDeteccion modo = ModoDeteccion.Automatico;
    public GPSSimulado gps;
    [Tooltip("Segundos entre análisis")]
    public float intervalo = 0.5f;
    [Tooltip("Ancho del fotograma enviado (el alto sigue la proporción de la pantalla)")]
    public int ancho = 640;

    [Header("Transmisión en vivo al panel web")]
    public bool transmitirEnVivo = true;
    [Tooltip("Segundos entre fotogramas en vivo")]
    public float intervaloVivo = 0.35f;

    [Header("Modo Simulado")]
    [Tooltip("Distancia máxima (m) a la que se 've' un daño")]
    public float rangoVision = 30f;
    [Tooltip("Distancia (m) a la que se confirma y reporta el daño")]
    public float rangoReporte = 15f;
    [Tooltip("Tipos de daño que NO detecta la IA: se registran a mano desde el panel web")]
    public string[] tiposManuales = { "grieta" };

    Camera cam, camCaptura;
    VehiculoSimulado vehiculo;
    RenderTexture rt;
    Texture2D captura;
    RespuestaDeteccion ultima;
    string mensaje;
    float mensajeHasta;
    bool yoloNoDisponible, enviandoVivo, vivoConectado;
    int reportados;
    // Cada Play es una sesión distinta: el servidor abre un recorrido nuevo
    readonly string sesion = Guid.NewGuid().ToString("N");

    float VelocidadKmh => vehiculo != null ? Mathf.Abs(vehiculo.Velocidad) * 3.6f : 0f;
    bool UsarSimulado => modo == ModoDeteccion.Simulado || (modo == ModoDeteccion.Automatico && yoloNoDisponible);

    struct Visible { public BacheVirtual bache; public DeteccionDTO det; public float dist; }

    void Start()
    {
        cam = GetComponent<Camera>();
        if (gps == null) gps = GetComponentInParent<GPSSimulado>();
        vehiculo = GetComponentInParent<VehiculoSimulado>();

        // Cámara gemela que renderiza a una textura (sin la interfaz OnGUI encima), compatible con URP
        int alto = Mathf.Max(32, Mathf.RoundToInt(ancho * (float)Screen.height / Screen.width / 32f) * 32);
        rt = new RenderTexture(ancho, alto, 24);
        captura = new Texture2D(ancho, alto, TextureFormat.RGB24, false);

        var go = new GameObject("CamaraCapturaYOLO");
        go.transform.SetParent(transform, false);
        camCaptura = go.AddComponent<Camera>();
        camCaptura.CopyFrom(cam);
        camCaptura.targetTexture = rt;
        camCaptura.depth = cam.depth - 1;

        StartCoroutine(Bucle());
        if (transmitirEnVivo) StartCoroutine(TransmitirVivo());
    }

    IEnumerator ConsultarEstado()
    {
        using var req = UnityWebRequest.Get(servidor + "/api/estado");
        req.timeout = 120;   // la primera vez el servidor carga el modelo YOLO
        Mostrar("Consultando estado de YOLO en el servidor...", 120f);
        yield return req.SendWebRequest();
        if (req.result != UnityWebRequest.Result.Success)
        {
            Mostrar($"Servidor no disponible: {req.error}\n¿Está corriendo uvicorn en {servidor}?");
            yoloNoDisponible = true;
            yield break;
        }
        var e = JsonUtility.FromJson<EstadoServidor>(req.downloadHandler.text);
        yoloNoDisponible = !e.yolo || e.modo_demo;
        Mostrar(!e.yolo ? "YOLO no está instalado en el servidor → modo SIMULADO."
              : e.modo_demo ? "YOLO sin modelo de baches (models/baches.pt) → modo SIMULADO."
              : "YOLO listo con modelo de baches.", 6f);
    }

    IEnumerator Bucle()
    {
        if (modo == ModoDeteccion.Automatico) yield return ConsultarEstado();
        while (true)
        {
            yield return new WaitForSeconds(intervalo);
            if (UsarSimulado) yield return DetectarSimulado();
            else yield return DetectarConYOLO(CapturarJPG());
        }
    }

    byte[] CapturarJPG(int calidad = 85)
    {
        var previa = RenderTexture.active;
        RenderTexture.active = rt;
        captura.ReadPixels(new Rect(0, 0, rt.width, rt.height), 0, 0);
        captura.Apply();
        RenderTexture.active = previa;
        return captura.EncodeToJPG(calidad);
    }

    // ------------------------------------------------------------------ transmisión en vivo
    IEnumerator TransmitirVivo()
    {
        while (true)
        {
            yield return new WaitForSeconds(intervaloVivo);
            if (enviandoVivo || gps == null) continue;
            StartCoroutine(EnviarVivo());
        }
    }

    IEnumerator EnviarVivo()
    {
        enviandoVivo = true;
        var form = new WWWForm();
        form.AddBinaryData("imagen", CapturarJPG(70), "vivo.jpg", "image/jpeg");
        form.AddField("lat", gps.Latitud.ToString("F7", CultureInfo.InvariantCulture));
        form.AddField("lon", gps.Longitud.ToString("F7", CultureInfo.InvariantCulture));
        form.AddField("velocidad", VelocidadKmh.ToString("F1", CultureInfo.InvariantCulture));
        form.AddField("fuente", "unity-vivo");
        form.AddField("sesion", sesion);
        form.AddField("detecciones", DeteccionesVivoJson());
        using var req = UnityWebRequest.Post(servidor + "/api/vivo", form);
        req.SetRequestHeader("X-Token-Dispositivo", tokenDispositivo);
        req.timeout = 10;
        yield return req.SendWebRequest();
        vivoConectado = req.result == UnityWebRequest.Result.Success;
        enviandoVivo = false;
    }

    /// <summary>Recuadros normalizados (0-1) de lo que se ve ahora, para dibujarlos en el panel web.</summary>
    string DeteccionesVivoJson()
    {
        var sb = new StringBuilder("[");
        void Agregar(float x, float y, float w, float h, float conf, string sev, string tipo)
        {
            if (sb.Length > 1) sb.Append(',');
            sb.Append(string.Format(CultureInfo.InvariantCulture,
                "{{\"x\":{0:F4},\"y\":{1:F4},\"w\":{2:F4},\"h\":{3:F4},\"confianza\":{4:F3},\"severidad\":\"{5}\",\"tipo\":\"{6}\"}}",
                x, y, w, h, conf, sev, tipo));
        }
        if (UsarSimulado)
        {
            foreach (var v in CalcularVisibles())
                Agregar(v.det.x1 / Screen.width, v.det.y1 / Screen.height, (v.det.x2 - v.det.x1) / Screen.width,
                        (v.det.y2 - v.det.y1) / Screen.height, v.det.confianza, v.det.severidad, v.bache.tipo);
        }
        else if (ultima?.detecciones != null && ultima.ancho > 0)
        {
            foreach (var d in ultima.detecciones)
                Agregar(d.x1 / ultima.ancho, d.y1 / ultima.alto, (d.x2 - d.x1) / ultima.ancho, (d.y2 - d.y1) / ultima.alto,
                        d.confianza, d.severidad, TipoDeClase(d.clase));
        }
        return sb.Append(']').ToString();
    }

    static string TipoDeClase(string clase)
    {
        var c = (clase ?? "").ToLowerInvariant();
        if (c.Contains("crack") || c.Contains("grieta")) return "grieta";
        if (c.Contains("hundimiento") || c.Contains("depression") || c.Contains("sink")) return "hundimiento";
        return "bache";
    }

    // ------------------------------------------------------------------ YOLO
    IEnumerator DetectarConYOLO(byte[] jpg)
    {
        var form = new WWWForm();
        form.AddBinaryData("imagen", jpg, "frame.jpg", "image/jpeg");
        form.AddField("fuente", "unity-yolo");
        form.AddField("sesion", sesion);
        form.AddField("velocidad", VelocidadKmh.ToString("F1", CultureInfo.InvariantCulture));
        if (gps != null)
        {
            form.AddField("lat", gps.Latitud.ToString("F6", CultureInfo.InvariantCulture));
            form.AddField("lon", gps.Longitud.ToString("F6", CultureInfo.InvariantCulture));
        }

        using var req = UnityWebRequest.Post(servidor + "/api/detectar", form);
        req.SetRequestHeader("X-Token-Dispositivo", tokenDispositivo);
        req.timeout = 15;
        yield return req.SendWebRequest();

        if (req.result == UnityWebRequest.Result.ProtocolError && modo == ModoDeteccion.Automatico)
        {
            // El servidor responde pero YOLO falla (p.ej. ultralytics no instalado)
            yoloNoDisponible = true;
            Mostrar("YOLO no disponible en el servidor → modo SIMULADO.\n" + Recortar(req.downloadHandler?.text), 8f);
            Debug.LogWarning("[Baches] YOLO no disponible, usando modo simulado: " + req.downloadHandler?.text);
            yield break;
        }
        if (req.result != UnityWebRequest.Result.Success)
        {
            Mostrar($"Servidor no disponible: {req.error}\n¿Está corriendo uvicorn en {servidor}?");
            yield break;
        }

        ultima = JsonUtility.FromJson<RespuestaDeteccion>(req.downloadHandler.text);
        var b = ultima.bache;
        if (b != null && b.id > 0) Anunciar(b);
    }

    // ------------------------------------------------------------------ Simulado
    List<Visible> CalcularVisibles()
    {
        var lista = new List<Visible>();
        var esquinas = new Vector3[8];
        foreach (var b in BacheVirtual.Todos)
        {
            if (Array.IndexOf(tiposManuales, b.tipo) >= 0) continue;   // p.ej. grietas: las registra una persona
            var lim = b.Limites;
            float dist = Vector3.Distance(cam.transform.position, lim.center);
            if (dist > rangoVision) continue;

            // Caja en pantalla a partir de las 8 esquinas del daño
            lim.Expand(new Vector3(0, 0.05f, 0));
            int k = 0;
            for (int x = 0; x < 2; x++)
            for (int y = 0; y < 2; y++)
            for (int z = 0; z < 2; z++)
                esquinas[k++] = new Vector3(x == 0 ? lim.min.x : lim.max.x, y == 0 ? lim.min.y : lim.max.y, z == 0 ? lim.min.z : lim.max.z);

            float x1 = float.MaxValue, y1 = float.MaxValue, x2 = float.MinValue, y2 = float.MinValue;
            bool detras = false;
            foreach (var e in esquinas)
            {
                var p = cam.WorldToScreenPoint(e);
                if (p.z <= 0) { detras = true; break; }
                float yGui = Screen.height - p.y;
                x1 = Mathf.Min(x1, p.x); x2 = Mathf.Max(x2, p.x);
                y1 = Mathf.Min(y1, yGui); y2 = Mathf.Max(y2, yGui);
            }
            if (detras) continue;
            x1 = Mathf.Max(x1, 0); y1 = Mathf.Max(y1, 0);
            x2 = Mathf.Min(x2, Screen.width); y2 = Mathf.Min(y2, Screen.height);
            if (x2 - x1 < 4 || y2 - y1 < 4) continue;

            // Confianza estable por daño (no parpadea entre fotogramas)
            float ruido = (Mathf.PerlinNoise(b.transform.position.z * 0.1f, 0.3f) - 0.5f) * 0.06f;
            float conf = Mathf.Clamp01(Mathf.Lerp(0.96f, 0.6f, dist / rangoVision) + ruido);
            lista.Add(new Visible
            {
                bache = b, dist = dist,
                det = new DeteccionDTO { x1 = x1, y1 = y1, x2 = x2, y2 = y2, confianza = conf, clase = b.tipo, severidad = b.Severidad },
            });
        }
        return lista;
    }

    IEnumerator DetectarSimulado()
    {
        var visibles = CalcularVisibles();
        Visible? porReportar = null;
        foreach (var v in visibles)
            if (!v.bache.reportado && v.dist <= rangoReporte && (porReportar == null || v.dist < porReportar.Value.dist))
                porReportar = v;

        var dets = new DeteccionDTO[visibles.Count];
        for (int i = 0; i < dets.Length; i++) dets[i] = visibles[i].det;
        ultima = new RespuestaDeteccion { detecciones = dets, ms = 0, ancho = Screen.width, alto = Screen.height };

        if (porReportar != null)
        {
            porReportar.Value.bache.reportado = true;
            yield return Reportar(porReportar.Value);
        }
    }

    IEnumerator Reportar(Visible v)
    {
        var b = v.bache;
        var det = v.det;
        var pos = b.transform.position;
        var escala = b.transform.lossyScale;   // el quad del daño mide escala.x × escala.y metros
        var rep = new ReporteDTO
        {
            lat = gps != null ? gps.LatitudDe(pos) : 0,
            lon = gps != null ? gps.LongitudDe(pos) : 0,
            confianza = (float)Math.Round(det.confianza, 3),
            severidad = b.Severidad,
            fuente = "unity-simulado",
            sesion = sesion,
            imagen_b64 = Convert.ToBase64String(CapturarJPG()),
            tipo = b.tipo,
            velocidad = VelocidadKmh,
            // Recuadro normalizado (la captura tiene la misma vista y proporción que la pantalla)
            bx = det.x1 / Screen.width, by = det.y1 / Screen.height,
            bw = (det.x2 - det.x1) / Screen.width, bh = (det.y2 - det.y1) / Screen.height,
            largo_cm = Mathf.Round(Mathf.Max(escala.x, escala.y) * 100f),
            ancho_cm = Mathf.Round(Mathf.Min(escala.x, escala.y) * 100f),
        };
        string json = JsonUtility.ToJson(rep);
        if (gps == null) json = json.Replace("\"lat\":0.0,\"lon\":0.0,", "");   // sin GPS: el servidor usa la IP

        using var req = UnityWebRequest.Post(servidor + "/api/baches", json, "application/json");
        req.SetRequestHeader("X-Token-Dispositivo", tokenDispositivo);
        req.timeout = 20;
        yield return req.SendWebRequest();

        if (req.result != UnityWebRequest.Result.Success)
        {
            b.reportado = false;   // reintentar la próxima vez
            Mostrar($"No se pudo reportar: {req.error}\n{Recortar(req.downloadHandler?.text)}");
            yield break;
        }
        Anunciar(JsonUtility.FromJson<BacheDTO>(req.downloadHandler.text));
    }

    // ------------------------------------------------------------------ UI
    void Anunciar(BacheDTO b)
    {
        if (!b.duplicado) reportados++;
        string estado = b.duplicado ? "ya registrado (+1 reporte)" : "NUEVO";
        Mostrar($"¡DAÑO {estado}! {b.codigo}  {b.provincia} - {b.canton}\n" +
                $"IP zona: {b.ip_publica} ({b.ip_ciudad}, {b.ip_isp})\n" +
                $"Lat {b.lat:F5}  Lon {b.lon:F5}  |  {b.severidad}  {b.confianza:P0}");
        Debug.Log("[Baches] " + mensaje.Replace("\n", " | "));
    }

    void Mostrar(string texto, float segundos = 4f)
    {
        mensaje = texto;
        mensajeHasta = Time.time + segundos;
    }

    static string Recortar(string s) => string.IsNullOrEmpty(s) ? "" : s.Length > 160 ? s.Substring(0, 160) + "..." : s;

    static string Etiqueta(string clase) => TipoDeClase(clase).ToUpperInvariant();

    void OnGUI()
    {
        // Cajas de detección (en píxeles del frame analizado) escaladas a la pantalla
        if (ultima?.detecciones != null && ultima.ancho > 0)
        {
            float sx = (float)Screen.width / ultima.ancho, sy = (float)Screen.height / ultima.alto;
            foreach (var d in ultima.detecciones)
            {
                var r = new Rect(d.x1 * sx, d.y1 * sy, (d.x2 - d.x1) * sx, (d.y2 - d.y1) * sy);
                Color c = d.severidad == "grave" ? Color.red : d.severidad == "moderado" ? new Color(1f, .78f, .1f) : new Color(.25f, .8f, .35f);
                DibujarMarco(r, c, 3);
                GUI.color = c;
                GUI.Label(new Rect(r.x, r.y - 20, 250, 20), $"{Etiqueta(d.clase)} ({d.confianza:P0})");
                GUI.color = Color.white;
            }
        }

        bool conMensaje = Time.time < mensajeHasta;
        var estilo = new GUIStyle(GUI.skin.box) { fontSize = 15, alignment = TextAnchor.UpperLeft, wordWrap = true };
        string gpsTxt = gps != null ? $"{gps.NombreRuta}  ·  GPS: {gps.Latitud:F5}, {gps.Longitud:F5}  ·  {VelocidadKmh:F0} km/h" : "GPS: (usa IP)";
        string modoTxt = UsarSimulado ? "SIMULADO" : "YOLO";
        string det = ultima != null
            ? $"{modoTxt}: {ultima.detecciones?.Length ?? 0} daños a la vista" + (UsarSimulado ? "" : $" · {ultima.ms} ms")
            : $"{modoTxt}: esperando...";
        string vivo = transmitirEnVivo ? (vivoConectado ? "  ·  ● EN VIVO en el panel" : "  ·  panel desconectado") : "";
        string texto = $"{gpsTxt}\n{det} · reportados: {reportados}{vivo}" + (conMensaje ? "\n\n" + mensaje : "");
        GUI.Box(new Rect(10, 10, 600, conMensaje ? 150 : 55), texto, estilo);
    }

    static void DibujarMarco(Rect r, Color c, float g)
    {
        var t = Texture2D.whiteTexture;
        GUI.color = c;
        GUI.DrawTexture(new Rect(r.x, r.y, r.width, g), t);
        GUI.DrawTexture(new Rect(r.x, r.yMax - g, r.width, g), t);
        GUI.DrawTexture(new Rect(r.x, r.y, g, r.height), t);
        GUI.DrawTexture(new Rect(r.xMax - g, r.y, g, r.height), t);
        GUI.color = Color.white;
    }

    void OnDestroy()
    {
        if (rt != null) rt.Release();
    }
}

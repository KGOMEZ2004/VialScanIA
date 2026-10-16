using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Networking;
#if ENABLE_INPUT_SYSTEM
using UnityEngine.InputSystem;
#endif

/// <summary>
/// Consulta el servidor cada pocos segundos y coloca un marcador por cada bache sobre el MapaEcuador.
/// Clic sobre un marcador (en la vista de la cámara del mapa) = ficha con provincia, cantón e IP.
/// Si se asigna un GPSSimulado, también muestra la posición del vehículo en el mapa.
/// </summary>
public class BachesEnMapa : MonoBehaviour
{
    public string servidor = "http://127.0.0.1:8000";
    [Tooltip("Token de dispositivo: panel web > Configuración > Sistema, o consola del servidor")]
    public string tokenDispositivo = "";
    public MapaEcuador mapa;
    public Camera camaraMapa;
    public GPSSimulado gpsVehiculo;
    public GameObject prefabMarcador;   // opcional; si no, se crea una esfera
    public float intervalo = 3f;
    public float escalaMarcador = 0.6f;

    readonly Dictionary<int, MarcadorBache> marcadores = new();
    Transform marcadorVehiculo;
    bool primeraCarga = true;

    void Start()
    {
        if (gpsVehiculo != null)
        {
            var go = GameObject.CreatePrimitive(PrimitiveType.Cube);
            go.name = "Vehiculo_EnMapa";
            Destroy(go.GetComponent<Collider>());
            go.GetComponent<Renderer>().material.color = new Color(0.1f, 0.4f, 0.95f);
            go.transform.localScale = new Vector3(0.7f, 0.7f, 0.7f);
            marcadorVehiculo = go.transform;
        }
        StartCoroutine(Actualizar());
    }

    void Update()
    {
        if (marcadorVehiculo != null)
            marcadorVehiculo.position = mapa.LatLonAMundo((float)gpsVehiculo.Latitud, (float)gpsVehiculo.Longitud, 0.5f);

        if (camaraMapa == null || !ClicEsteFrame(out Vector2 pos)) return;
        if (!camaraMapa.pixelRect.Contains(pos)) return;
        if (Physics.Raycast(camaraMapa.ScreenPointToRay(pos), out var hit, 1000f) &&
            hit.collider.TryGetComponent(out MarcadorBache m))
            m.Seleccionar();
    }

    static bool ClicEsteFrame(out Vector2 pos)
    {
#if ENABLE_INPUT_SYSTEM
        pos = Mouse.current != null ? Mouse.current.position.ReadValue() : Vector2.zero;
        return Mouse.current != null && Mouse.current.leftButton.wasPressedThisFrame;
#else
        pos = Input.mousePosition;
        return Input.GetMouseButtonDown(0);
#endif
    }

    IEnumerator Actualizar()
    {
        while (true)
        {
            using (var req = UnityWebRequest.Get(servidor + "/api/baches"))
            {
                req.SetRequestHeader("X-Token-Dispositivo", tokenDispositivo);
                yield return req.SendWebRequest();
                if (req.result == UnityWebRequest.Result.Success)
                    Sincronizar(JsonUtility.FromJson<ListaBaches>(req.downloadHandler.text).baches);
                else
                    Debug.LogWarning("[Mapa] Servidor no disponible: " + req.error);
            }
            yield return new WaitForSeconds(intervalo);
        }
    }

    void Sincronizar(BacheDTO[] baches)
    {
        var vigentes = new HashSet<int>();
        foreach (var b in baches)
        {
            vigentes.Add(b.id);
            if (!mapa.Contiene(b.lat, b.lon)) continue;   // p.ej. Galápagos queda fuera de la textura

            if (!marcadores.TryGetValue(b.id, out var m))
            {
                var go = prefabMarcador ? Instantiate(prefabMarcador, transform) : CrearEsfera();
                go.name = $"Bache_{b.id}";
                m = go.AddComponent<MarcadorBache>();
                marcadores[b.id] = m;
                if (!primeraCarga) m.Resaltar();   // bache nuevo mientras la app corre
            }
            m.transform.position = mapa.LatLonAMundo(b.lat, b.lon);
            m.escalaBase = Vector3.one * escalaMarcador * (1f + 0.15f * Mathf.Min(b.reportes, 6));
            m.Asignar(b);
        }
        primeraCarga = false;

        // Baches reparados (eliminados en el servidor)
        var quitar = new List<int>();
        foreach (var id in marcadores.Keys) if (!vigentes.Contains(id)) quitar.Add(id);
        foreach (var id in quitar)
        {
            Destroy(marcadores[id].gameObject);
            marcadores.Remove(id);
        }
    }

    GameObject CrearEsfera()
    {
        var go = GameObject.CreatePrimitive(PrimitiveType.Sphere);
        go.transform.SetParent(transform, false);
        return go;
    }
}

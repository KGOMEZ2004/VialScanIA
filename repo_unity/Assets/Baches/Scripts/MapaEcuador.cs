using UnityEngine;

/// <summary>
/// Mapa de Ecuador continental en el plano XZ de este objeto (norte = +Z, este = +X).
/// La textura Assets/Baches/Texturas/MapaEcuador.png está recortada exactamente a estos límites
/// (se regenera con backend/herramientas/generar_mapa_unity.py).
/// </summary>
public class MapaEcuador : MonoBehaviour
{
    [Header("Límites geográficos de la textura")]
    public float latNorte = 1.7f;
    public float latSur = -5.1f;
    public float lonOeste = -81.2f;
    public float lonEste = -75.1f;

    [Header("Tamaño del mapa en unidades de Unity")]
    public float anchoMundo = 61f;   // 6.1° de longitud
    public float altoMundo = 68f;    // 6.8° de latitud

    public bool Contiene(float lat, float lon) =>
        lat <= latNorte && lat >= latSur && lon >= lonOeste && lon <= lonEste;

    public Vector3 LatLonAMundo(float lat, float lon, float altura = 0.3f)
    {
        float u = Mathf.InverseLerp(lonOeste, lonEste, lon) - 0.5f;
        float v = Mathf.InverseLerp(latSur, latNorte, lat) - 0.5f;
        return transform.TransformPoint(new Vector3(u * anchoMundo, altura, v * altoMundo));
    }

    public Vector2 MundoALatLon(Vector3 mundo)
    {
        var local = transform.InverseTransformPoint(mundo);
        float lon = Mathf.LerpUnclamped(lonOeste, lonEste, local.x / anchoMundo + 0.5f);
        float lat = Mathf.LerpUnclamped(latSur, latNorte, local.z / altoMundo + 0.5f);
        return new Vector2(lat, lon);
    }

    void OnDrawGizmos()
    {
        Gizmos.matrix = transform.localToWorldMatrix;
        Gizmos.color = Color.cyan;
        Gizmos.DrawWireCube(Vector3.zero, new Vector3(anchoMundo, 0, altoMundo));
    }
}

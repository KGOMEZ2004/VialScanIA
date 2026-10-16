using UnityEngine;

/// <summary>Marcador de un bache en el mapa. Al seleccionarlo muestra provincia, cantón e IP de la zona.</summary>
public class MarcadorBache : MonoBehaviour
{
    public BacheDTO datos;
    public Vector3 escalaBase = Vector3.one;

    public static MarcadorBache Seleccionado { get; private set; }

    Renderer rend;
    float pulsoHasta;

    public void Asignar(BacheDTO b)
    {
        datos = b;
        if (rend == null) rend = GetComponent<Renderer>();
        if (rend == null) return;
        rend.material.color = b.severidad switch
        {
            "grave" => new Color(0.84f, 0.16f, 0.16f),
            "moderado" => new Color(0.91f, 0.35f, 0.05f),
            _ => new Color(0.95f, 0.7f, 0f),
        };
    }

    public void Resaltar() => pulsoHasta = Time.time + 5f;
    public void Seleccionar() => Seleccionado = this;

    void Update()
    {
        float pulso = Time.time < pulsoHasta ? 1f + 0.5f * Mathf.Abs(Mathf.Sin(Time.time * 6f)) : 1f;
        transform.localScale = escalaBase * pulso;
    }

    void OnGUI()
    {
        if (Seleccionado != this || datos == null) return;
        var b = datos;
        string texto =
            $"<b>Bache #{b.id}</b>  ({b.severidad}, {b.confianza:P0})\n" +
            $"Provincia: <b>{b.provincia}</b>\nCantón: {b.canton}\n" +
            $"IP pública: <b>{b.ip_publica}</b>\nIP dispositivo: {b.ip_cliente}\n" +
            $"Zona IP: {b.ip_ciudad}, {b.ip_region} — {b.ip_isp}\n" +
            $"Coordenadas: {b.lat:F5}, {b.lon:F5} ({b.ubicacion_por})\n" +
            $"Reportes: {b.reportes}   Fuente: {b.fuente}\nFecha: {b.fecha}";
        var estilo = new GUIStyle(GUI.skin.box) { richText = true, fontSize = 14, alignment = TextAnchor.UpperLeft, wordWrap = true };
        var r = new Rect(Screen.width - 400, 10, 390, 215);
        GUI.Box(r, texto, estilo);
        if (GUI.Button(new Rect(r.xMax - 70, r.yMax - 28, 62, 22), "Cerrar")) Seleccionado = null;
    }
}

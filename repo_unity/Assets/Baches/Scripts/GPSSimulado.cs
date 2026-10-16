using System;
using UnityEngine;

/// <summary>
/// GPS simulado del vehículo. Convierte lo que avanza en la escena (1 unidad = 1 metro, eje Z) en una posición
/// sobre una avenida real de Ecuador (Assets/Baches/Datos/rutas_ecuador.json, trazados de OpenStreetMap).
/// Con rutaAleatoria, cada vez que se pulsa Play se elige una ruta distinta.
/// Sin rutas, usa una línea recta hacia el norte desde latitudInicio/longitudInicio.
/// </summary>
public class GPSSimulado : MonoBehaviour
{
    [Tooltip("JSON con las rutas reales ({\"rutas\":[{\"nombre\":..., \"puntos\":[lat,lon,lat,lon,...]}]})")]
    public TextAsset rutas;
    public bool rutaAleatoria = true;
    [Tooltip("Ruta a usar si rutaAleatoria está desactivado")]
    public int indiceRuta;

    [Header("Si no hay rutas: línea recta hacia el norte")]
    public double latitudInicio = -0.1807;
    public double longitudInicio = -78.4678;

    [Serializable] class Ruta { public string nombre; public double[] puntos; }
    [Serializable] class ListaRutas { public Ruta[] rutas; }

    const double MetrosPorGrado = 111320.0;
    Vector3 origen;
    bool iniciado;
    double[] lat, lon, acumulado;   // puntos de la ruta y distancia acumulada (m)

    public string NombreRuta { get; private set; } = "Ruta recta";
    public double Latitud => LatitudDe(transform.position);
    public double Longitud => LongitudDe(transform.position);

    void Awake() => Iniciar();

    void Iniciar()
    {
        if (iniciado) return;
        iniciado = true;
        origen = transform.position;
        if (rutas == null) return;
        var lista = JsonUtility.FromJson<ListaRutas>(rutas.text);
        if (lista?.rutas == null || lista.rutas.Length == 0) return;
        int i = rutaAleatoria ? new System.Random(Guid.NewGuid().GetHashCode()).Next(lista.rutas.Length)
                              : Mathf.Clamp(indiceRuta, 0, lista.rutas.Length - 1);
        var r = lista.rutas[i];
        int n = r.puntos.Length / 2;
        if (n < 2) return;
        lat = new double[n]; lon = new double[n]; acumulado = new double[n];
        for (int k = 0; k < n; k++)
        {
            lat[k] = r.puntos[2 * k];
            lon[k] = r.puntos[2 * k + 1];
            if (k > 0) acumulado[k] = acumulado[k - 1] + Metros(lat[k - 1], lon[k - 1], lat[k], lon[k]);
        }
        NombreRuta = r.nombre;
        Debug.Log($"[Baches] Ruta GPS de este recorrido: {r.nombre} ({acumulado[n - 1]:F0} m)");
    }

    static double Metros(double la1, double lo1, double la2, double lo2)
    {
        double dy = (la2 - la1) * MetrosPorGrado, dx = (lo2 - lo1) * MetrosPorGrado * Math.Cos(la1 * Math.PI / 180.0);
        return Math.Sqrt(dx * dx + dy * dy);
    }

    /// <summary>Posición GPS de cualquier punto de la escena: avance en Z sobre la ruta, desvío en X hacia la derecha.</summary>
    public (double lat, double lon) PosicionDe(Vector3 pos)
    {
        Iniciar();
        double avance = pos.z - origen.z, lateral = pos.x - origen.x;
        if (lat == null)
            return (latitudInicio + avance / MetrosPorGrado,
                    longitudInicio + lateral / (MetrosPorGrado * Math.Cos(latitudInicio * Math.PI / 180.0)));

        // Tramo de la ruta donde cae el avance (antes del inicio o después del final se prolonga el primer/último tramo)
        int k = 1;
        while (k < acumulado.Length - 1 && acumulado[k] < avance) k++;
        double largo = acumulado[k] - acumulado[k - 1];
        double t = largo > 0 ? (avance - acumulado[k - 1]) / largo : 0;
        double la = lat[k - 1] + (lat[k] - lat[k - 1]) * t;
        double lo = lon[k - 1] + (lon[k] - lon[k - 1]) * t;

        // Desvío lateral perpendicular a la dirección del tramo
        double cos = Math.Cos(la * Math.PI / 180.0);
        double dy = (lat[k] - lat[k - 1]) * MetrosPorGrado, dx = (lon[k] - lon[k - 1]) * MetrosPorGrado * cos;
        double norma = Math.Sqrt(dx * dx + dy * dy);
        if (norma > 0)
        {
            double derX = dy / norma, derY = -dx / norma;   // vector a la derecha del sentido de avance
            la += lateral * derY / MetrosPorGrado;
            lo += lateral * derX / (MetrosPorGrado * cos);
        }
        return (la, lo);
    }

    public double LatitudDe(Vector3 pos) => PosicionDe(pos).lat;
    public double LongitudDe(Vector3 pos) => PosicionDe(pos).lon;
}

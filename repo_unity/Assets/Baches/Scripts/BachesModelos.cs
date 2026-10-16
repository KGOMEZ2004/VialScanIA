using System;

// Estructuras JSON que devuelve el servidor (backend/app.py).
// JsonUtility requiere campos públicos con el mismo nombre que las claves JSON.

[Serializable]
public class BacheDTO
{
    public int id;
    public string codigo;
    public string fecha;
    public float lat;
    public float lon;
    public string ubicacion_por;
    public string provincia;
    public string canton;
    public string direccion;
    public float confianza;
    public string severidad;
    public string fuente;
    public string imagen;
    public int reportes;
    public string ip_cliente;
    public string ip_publica;
    public string ip_pais;
    public string ip_region;
    public string ip_ciudad;
    public string ip_isp;
    public bool duplicado;
}

[Serializable]
public class ListaBaches
{
    public BacheDTO[] baches;
}

[Serializable]
public class DeteccionDTO
{
    public float x1, y1, x2, y2;
    public float confianza;
    public string clase;
    public string severidad;
}

[Serializable]
public class RespuestaDeteccion
{
    public DeteccionDTO[] detecciones;
    public int ms;
    public int ancho;
    public int alto;
    public BacheDTO bache;
}

[Serializable]
public class ReporteDTO
{
    public double lat;
    public double lon;
    public float confianza;
    public string severidad;
    public string fuente;
    public string imagen_b64;
    public string tipo = "bache";
    public float velocidad;            // km/h
    // Recuadro del bache dentro de la imagen, normalizado 0-1 (origen arriba a la izquierda)
    public float bx, by, bw, bh;
    public float largo_cm, ancho_cm;
    public string sesion;              // cada Play de Unity es un recorrido nuevo
}

[Serializable]
public class EstadoServidor
{
    public bool yolo;
    public bool modo_demo;
    public string error;
}

using UnityEngine;

/// <summary>Auto rojo que circula por delante del vehículo (como en el diseño), manteniendo distancia.</summary>
public class AutoNPC : MonoBehaviour
{
    public Transform objetivo;
    public float carril = -1.9f;
    public float distanciaMin = 20f, distanciaMax = 45f;
    public float largoCalle = 1000f;
    public Material carroceria, vidrios, luces, llantas;

    float velocidad = 10f;

    void Start()
    {
        Pieza(PrimitiveType.Cube, new Vector3(0, 0.62f, 0), new Vector3(1.8f, 0.7f, 4.2f), carroceria);
        Pieza(PrimitiveType.Cube, new Vector3(0, 1.2f, -0.2f), new Vector3(1.6f, 0.55f, 2.2f), vidrios);
        Pieza(PrimitiveType.Cube, new Vector3(-0.62f, 0.72f, -2.11f), new Vector3(0.36f, 0.16f, 0.04f), luces);
        Pieza(PrimitiveType.Cube, new Vector3(0.62f, 0.72f, -2.11f), new Vector3(0.36f, 0.16f, 0.04f), luces);
        Pieza(PrimitiveType.Cube, new Vector3(0, 0.55f, -2.11f), new Vector3(0.5f, 0.14f, 0.03f), null);   // placa
        foreach (var x in new[] { -0.82f, 0.82f })
        foreach (var z in new[] { -1.35f, 1.35f })
        {
            var r = Pieza(PrimitiveType.Cylinder, new Vector3(x, 0.34f, z), new Vector3(0.66f, 0.12f, 0.66f), llantas);
            r.transform.localRotation = Quaternion.Euler(0, 0, 90);
        }
    }

    GameObject Pieza(PrimitiveType tipo, Vector3 pos, Vector3 escala, Material mat)
    {
        var go = GameObject.CreatePrimitive(tipo);
        Destroy(go.GetComponent<Collider>());
        go.transform.SetParent(transform, false);
        go.transform.localPosition = pos;
        go.transform.localScale = escala;
        if (mat) go.GetComponent<Renderer>().sharedMaterial = mat;
        return go;
    }

    void Update()
    {
        if (objetivo == null) return;
        float d = transform.position.z - objetivo.position.z;
        if (d < distanciaMin) velocidad += 5f * Time.deltaTime;
        else if (d > distanciaMax) velocidad -= 5f * Time.deltaTime;
        velocidad = Mathf.Clamp(velocidad, 4f, 26f);
        var p = transform.position + Vector3.forward * velocidad * Time.deltaTime;
        // Al llegar al final de la calle (o si quedó atrás) reaparece delante del vehículo
        if (p.z > largoCalle - 5f || d < -5f) p.z = Mathf.Min(objetivo.position.z + distanciaMax, largoCalle - 40f);
        transform.position = new Vector3(carril, 0, p.z);
    }
}

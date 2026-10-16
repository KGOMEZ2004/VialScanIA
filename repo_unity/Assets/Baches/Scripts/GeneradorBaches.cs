using UnityEngine;

/// <summary>
/// Coloca daños aleatorios sobre la calzada: baches, grietas y hundimientos (texturas en Assets/Baches/Texturas).
/// Si no hay GeneradorCiudad en la escena, también crea una carretera simple (crearCarretera).
/// </summary>
public class GeneradorBaches : MonoBehaviour
{
    public float largo = 1000f;
    public float anchoCarretera = 8f;
    public int cantidadBaches = 70;
    public int cantidadGrietas = 28;
    public int cantidadHundimientos = 18;
    public bool crearCarretera = true;
    public Material materialAsfalto;
    public Material[] materialesBache;
    public Material[] materialesGrieta;
    public Material[] materialesHundimiento;
    [Tooltip("Opcional: modelo 3D de bache; si se asigna, reemplaza a las texturas de bache")]
    public GameObject prefabBache;
    [Tooltip("Cada Play coloca los daños en lugares distintos (si no, usa la semilla)")]
    public bool aleatorio = true;
    public int semilla = 42;

    int orden;

    void Start()
    {
        Random.InitState(aleatorio ? System.Guid.NewGuid().GetHashCode() : semilla);
        if (crearCarretera) CrearCarretera();
        // Cantidades con algo de variación en cada recorrido
        if (aleatorio)
        {
            cantidadBaches = Mathf.RoundToInt(cantidadBaches * Random.Range(0.7f, 1.3f));
            cantidadGrietas = Mathf.RoundToInt(cantidadGrietas * Random.Range(0.7f, 1.3f));
            cantidadHundimientos = Mathf.RoundToInt(cantidadHundimientos * Random.Range(0.7f, 1.3f));
        }

        for (int i = 0; i < cantidadBaches; i++)
            Colocar("bache", Random.Range(0.9f, 2.4f), i, materialesBache);
        for (int i = 0; i < cantidadGrietas; i++)
            Colocar("grieta", Random.Range(1.8f, 4.5f), i, materialesGrieta);
        for (int i = 0; i < cantidadHundimientos; i++)
            Colocar("hundimiento", Random.Range(1.2f, 2.6f), i, materialesHundimiento);
    }

    void CrearCarretera()
    {
        var carretera = GameObject.CreatePrimitive(PrimitiveType.Cube);
        carretera.name = "Asfalto";
        carretera.transform.SetParent(transform, false);
        carretera.transform.localScale = new Vector3(anchoCarretera, 0.1f, largo);
        carretera.transform.localPosition = new Vector3(0, -0.05f, largo / 2);
        var rend = carretera.GetComponent<Renderer>();
        if (materialAsfalto)
        {
            rend.sharedMaterial = materialAsfalto;
            rend.material.mainTextureScale = new Vector2(anchoCarretera / 8f, largo / 8f);
        }
        else rend.material.color = new Color(0.32f, 0.32f, 0.34f);
    }

    void Colocar(string tipo, float tam, int i, Material[] materiales)
    {
        float margen = tipo == "grieta" ? 0.8f : 1f;
        var pos = new Vector3(Random.Range(-anchoCarretera / 2 + margen, anchoCarretera / 2 - margen),
                              0.012f + (orden++) * 0.0001f, Random.Range(25f, largo - 10f));
        GameObject go;
        if (tipo == "bache" && prefabBache)
        {
            go = Instantiate(prefabBache, transform);
            go.transform.localScale *= tam;
            go.transform.localRotation = Quaternion.Euler(0, Random.Range(0, 360f), 0);
        }
        else
        {
            go = GameObject.CreatePrimitive(PrimitiveType.Quad);
            Destroy(go.GetComponent<Collider>());
            go.transform.SetParent(transform, false);
            // Quad acostado: su eje Y local queda a lo largo de la calle
            float giro = tipo == "grieta" ? Random.Range(-18f, 18f) : Random.Range(0, 360f);
            go.transform.localRotation = Quaternion.Euler(90, giro, 0);
            go.transform.localScale = tipo switch
            {
                "grieta" => new Vector3(tam * 0.25f, tam, 1),
                "hundimiento" => new Vector3(tam, tam * Random.Range(0.6f, 0.85f), 1),
                _ => new Vector3(tam, tam * Random.Range(0.7f, 1.2f), 1),
            };
            var r = go.GetComponent<Renderer>();
            r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            if (materiales != null && materiales.Length > 0) r.sharedMaterial = materiales[i % materiales.Length];
            else r.material.color = new Color(0.08f, 0.07f, 0.06f);
        }
        go.name = $"{tipo}_{i}";
        go.transform.localPosition = pos;
        var v = go.AddComponent<BacheVirtual>();
        v.tipo = tipo;
        v.diametro = tam;
    }
}

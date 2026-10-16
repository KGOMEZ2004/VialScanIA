using UnityEngine;

/// <summary>
/// Calle urbana como la del diseño de VialScan: asfalto con líneas, veredas, edificios con ventanas a ambos lados,
/// árboles, postes de luz y edificios al fondo. Los materiales los asigna el menú "Baches > Configurar escena".
/// </summary>
public class GeneradorCiudad : MonoBehaviour
{
    public float largo = 1000f;
    public float anchoCarretera = 8f;
    public float anchoVereda = 3.2f;
    [Tooltip("Cada Play genera una calle distinta (si no, usa la semilla)")]
    public bool aleatorio = true;
    public int semilla = 7;

    [Header("Materiales")]
    public Material materialAsfalto;
    public Material materialVereda;
    public Material materialTronco;
    public Material[] materialesHojas;
    public Material materialPoste;
    public Material[] fachadasIzquierda;
    public Material[] fachadasDerecha;

    static readonly int BaseMapST = Shader.PropertyToID("_BaseMap_ST");
    static readonly int MainTexST = Shader.PropertyToID("_MainTex_ST");
    MaterialPropertyBlock bloque;

    void Start()
    {
        Random.InitState(aleatorio ? System.Guid.NewGuid().GetHashCode() : semilla);
        bloque = new MaterialPropertyBlock();
        Carretera();
        for (int lado = -1; lado <= 1; lado += 2)
        {
            Vereda(lado);
            Edificios(lado);
            Arboles(lado);
        }
        Postes();
        Horizonte();
    }

    GameObject Pieza(PrimitiveType tipo, string nombre, Vector3 pos, Vector3 escala, Material mat, bool colision = false)
    {
        var go = GameObject.CreatePrimitive(tipo);
        go.name = nombre;
        go.transform.SetParent(transform, false);
        go.transform.localPosition = pos;
        go.transform.localScale = escala;
        if (!colision) Destroy(go.GetComponent<Collider>());
        if (mat) go.GetComponent<Renderer>().sharedMaterial = mat;
        return go;
    }

    void Mosaico(Renderer r, float x, float y)
    {
        r.GetPropertyBlock(bloque);
        var st = new Vector4(x, y, 0, 0);
        bloque.SetVector(BaseMapST, st);
        bloque.SetVector(MainTexST, st);
        r.SetPropertyBlock(bloque);
    }

    void Carretera()
    {
        var c = Pieza(PrimitiveType.Cube, "Asfalto", new Vector3(0, -0.05f, largo / 2), new Vector3(anchoCarretera, 0.1f, largo + 60),
                      materialAsfalto, colision: true);
        Mosaico(c.GetComponent<Renderer>(), anchoCarretera / 8f, (largo + 60) / 8f);   // 1 tile = 8 m x 8 m
    }

    void Vereda(int lado)
    {
        float x = lado * (anchoCarretera / 2 + anchoVereda / 2);
        Pieza(PrimitiveType.Cube, "Vereda", new Vector3(x, 0.08f, largo / 2), new Vector3(anchoVereda, 0.16f, largo + 60), materialVereda, true);
        // Bordillo
        Pieza(PrimitiveType.Cube, "Bordillo", new Vector3(lado * (anchoCarretera / 2 + 0.08f), 0.1f, largo / 2),
              new Vector3(0.16f, 0.2f, largo + 60), materialVereda);
    }

    void Edificios(int lado)
    {
        var fachadas = lado < 0 ? fachadasIzquierda : fachadasDerecha;
        float z = -30;
        while (z < largo + 40)
        {
            float frente = Random.Range(9f, 20f), fondo = 14f, alto = Random.Range(8f, 24f);
            float x = lado * (anchoCarretera / 2 + anchoVereda + fondo / 2 + 0.2f);
            var mat = fachadas != null && fachadas.Length > 0 ? fachadas[Random.Range(0, fachadas.Length)] : null;
            var e = Pieza(PrimitiveType.Cube, "Edificio", new Vector3(x, alto / 2, z + frente / 2), new Vector3(fondo, alto, frente), mat);
            Mosaico(e.GetComponent<Renderer>(), frente / 4f, alto / 3f);             // 1 ventana cada 4 m x 3 m
            z += frente + Random.Range(0f, 1.2f);
        }
    }

    void Arboles(int lado)
    {
        float x = lado * (anchoCarretera / 2 + 1.1f);
        for (float z = Random.Range(6f, 14f); z < largo; z += Random.Range(14f, 22f))
        {
            float h = Random.Range(2.8f, 3.6f), copa = Random.Range(3.2f, 4.4f);
            var hojas = materialesHojas != null && materialesHojas.Length > 0 ? materialesHojas : new Material[] { null };
            Pieza(PrimitiveType.Cylinder, "Tronco", new Vector3(x, h / 2 + 0.16f, z), new Vector3(0.32f, h / 2, 0.32f), materialTronco);
            Pieza(PrimitiveType.Sphere, "Copa", new Vector3(x, h + copa * 0.35f, z), Vector3.one * copa, hojas[0]);
            Pieza(PrimitiveType.Sphere, "Copa2", new Vector3(x - lado * 0.5f, h + copa * 0.62f, z - 0.4f), Vector3.one * copa * 0.62f,
                  hojas[hojas.Length - 1]);
        }
    }

    void Postes()
    {
        int lado = 1;
        for (float z = 20; z < largo; z += 34f, lado = -lado)
        {
            float x = lado * (anchoCarretera / 2 + 0.45f);
            Pieza(PrimitiveType.Cylinder, "Poste", new Vector3(x, 3.6f, z), new Vector3(0.18f, 3.6f, 0.18f), materialPoste);
            Pieza(PrimitiveType.Cube, "Brazo", new Vector3(x - lado * 0.9f, 7.1f, z), new Vector3(1.9f, 0.14f, 0.14f), materialPoste);
            Pieza(PrimitiveType.Cube, "Lampara", new Vector3(x - lado * 1.75f, 6.98f, z), new Vector3(0.5f, 0.12f, 0.25f), materialPoste);
        }
    }

    void Horizonte()
    {
        // Edificios lejanos al final de la calle
        float z0 = largo + 80;
        for (int i = 0; i < 9; i++)
        {
            float x = Random.Range(-40f, 40f), alto = Random.Range(18f, 45f), ancho = Random.Range(10f, 18f);
            if (Mathf.Abs(x) < 7) x += Mathf.Sign(x == 0 ? 1 : x) * 8;
            var mats = i % 2 == 0 ? fachadasDerecha : fachadasIzquierda;
            var e = Pieza(PrimitiveType.Cube, "Edificio lejano", new Vector3(x, alto / 2, z0 + Random.Range(0f, 60f)),
                          new Vector3(ancho, alto, 12f), mats != null && mats.Length > 0 ? mats[0] : null);
            Mosaico(e.GetComponent<Renderer>(), ancho / 4f, alto / 3f);
        }
    }
}

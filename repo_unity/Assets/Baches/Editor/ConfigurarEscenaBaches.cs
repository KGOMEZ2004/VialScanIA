using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;

/// <summary>
/// Menú "Baches > Configurar escena": arma en la escena abierta la carretera con baches,
/// el vehículo con cámara de detección + GPS y el mapa de Ecuador (minimapa).
/// También habilita HTTP para hablar con el servidor local.
/// Se puede ejecutar varias veces: reemplaza lo que creó antes.
/// </summary>
[InitializeOnLoad]
public static class ConfigurarEscenaBaches
{
    const string Raiz = "Baches_Sistema";
    const string CarpetaTexturas = "Assets/Baches/Texturas";
    const string CarpetaMateriales = "Assets/Baches/Materiales";
    const int CantidadTexturasBache = 4;
    static readonly Vector3 PosicionMapa = new(5000, 0, 0);   // lejos de la carretera

    const int VersionEscena = 3;   // 3 = recorrido al azar (ruta real, calle y daños) + grietas manuales
    static string ClavePregunta => $"Baches.PreguntaConfigurar.v{VersionEscena}." + Application.dataPath;

    // Al abrir el proyecto por primera vez con estos scripts, ofrece configurar la escena
    static ConfigurarEscenaBaches()
    {
        if (Application.isBatchMode || EditorPrefs.GetBool(ClavePregunta)) return;
        EditorApplication.delayCall += Preguntar;
    }

    static void Preguntar()
    {
        if (EditorApplication.isCompiling || EditorApplication.isUpdating)
        {
            EditorApplication.delayCall += Preguntar;
            return;
        }
        EditorPrefs.SetBool(ClavePregunta, true);
        var raiz = GameObject.Find(Raiz);
        var gpsActual = raiz ? raiz.GetComponentInChildren<GPSSimulado>() : null;
        if (raiz && raiz.transform.Find("Ciudad") && gpsActual && gpsActual.rutas) return;   // ya tiene la versión actual
        string texto = raiz
            ? "Hay una versión nueva de la escena: cada Play genera un recorrido distinto (ruta real de Ecuador, calle y " +
              "daños al azar), las grietas se marcan a mano en el panel y hay transmisión EN VIVO.\n\n¿Actualizar la escena ahora?"
            : "¿Configurar ahora la escena abierta para la detección de baches?\n\n" +
              "Se agregará: calle urbana con baches, grietas y hundimientos, vehículo con cámara de detección, " +
              "GPS simulado y minimapa de Ecuador. También se habilitará HTTP para el servidor local.";
        if (EditorUtility.DisplayDialog("Detector de baches", texto + "\n\nLuego puedes repetirlo desde el menú Baches > Configurar escena.",
                raiz ? "Actualizar" : "Configurar", "Ahora no"))
            Configurar();
    }

    /// <summary>Para modo batch: Unity -batchmode -executeMethod ConfigurarEscenaBaches.ConfigurarSampleScene</summary>
    public static void ConfigurarSampleScene()
    {
        EditorSceneManager.OpenScene("Assets/Scenes/SampleScene.unity");
        Configurar();
    }

    [MenuItem("Baches/Configurar escena")]
    public static void Configurar()
    {
        // HTTP hacia http://127.0.0.1:8000 (Unity lo bloquea por defecto)
        PlayerSettings.insecureHttpOption = InsecureHttpOption.AlwaysAllowed;

        var cam = Camera.main;
        var anterior = GameObject.Find(Raiz);
        if (anterior)
        {
            if (cam != null && cam.transform.IsChildOf(anterior.transform)) cam.transform.SetParent(null);
            Object.DestroyImmediate(anterior);
        }
        var raiz = new GameObject(Raiz).transform;

        // ---------- Ciudad (calle, veredas, edificios, árboles, postes) como en el diseño
        var ciudad = new GameObject("Ciudad").AddComponent<GeneradorCiudad>();
        ciudad.transform.SetParent(raiz);
        ciudad.materialAsfalto = CrearMaterial("Asfalto", Color.white, Textura("Asfalto", true));
        ciudad.materialVereda = CrearMaterial("Vereda", new Color(0.78f, 0.76f, 0.72f));
        ciudad.materialTronco = CrearMaterial("Tronco", new Color(0.36f, 0.26f, 0.2f));
        ciudad.materialesHojas = new[] { CrearMaterial("Hojas", new Color(0.25f, 0.54f, 0.23f)), CrearMaterial("Hojas_Claro", new Color(0.3f, 0.6f, 0.27f)) };
        ciudad.materialPoste = CrearMaterial("Poste", new Color(0.29f, 0.3f, 0.32f));
        ciudad.fachadasIzquierda = new[] { CrearMaterial("Fachada_Beige", Color.white, Textura("Fachada_Beige", true)),
                                           CrearMaterial("Fachada_Arena", Color.white, Textura("Fachada_Arena", true)) };
        ciudad.fachadasDerecha = new[] { CrearMaterial("Fachada_Gris", Color.white, Textura("Fachada_Gris", true)),
                                         CrearMaterial("Fachada_Azul", Color.white, Textura("Fachada_Azul", true)) };

        // ---------- Daños sobre la calzada: baches, grietas y hundimientos
        var carretera = new GameObject("Danos");
        carretera.transform.SetParent(raiz);
        var generador = carretera.AddComponent<GeneradorBaches>();
        generador.crearCarretera = false;
        generador.materialesBache = new Material[CantidadTexturasBache];
        for (int i = 0; i < CantidadTexturasBache; i++)
            generador.materialesBache[i] = CrearMaterial($"Bache_{i}", Color.white, Textura($"Bache_{i}", false), recorteAlfa: true);
        generador.materialesGrieta = new Material[3];
        for (int i = 0; i < 3; i++)
            generador.materialesGrieta[i] = CrearMaterial($"Grieta_{i}", Color.white, Textura($"Grieta_{i}", false), recorteAlfa: true);
        generador.materialesHundimiento = new Material[2];
        for (int i = 0; i < 2; i++)
            generador.materialesHundimiento[i] = CrearMaterial($"Hundimiento_{i}", Color.white, Textura($"Hundimiento_{i}", false), transparente: true);

        var pasto = GameObject.CreatePrimitive(PrimitiveType.Plane);
        pasto.name = "Terreno";
        pasto.transform.SetParent(raiz);
        pasto.transform.position = new Vector3(0, -0.12f, 500);
        pasto.transform.localScale = new Vector3(40, 1, 110);
        pasto.GetComponent<Renderer>().sharedMaterial = CrearMaterial("Terreno", new Color(0.55f, 0.53f, 0.5f));

        // Neblina ligera para dar profundidad a la calle (como el fondo del diseño)
        RenderSettings.fog = true;
        RenderSettings.fogMode = FogMode.Linear;
        RenderSettings.fogColor = new Color(0.78f, 0.85f, 0.91f);
        RenderSettings.fogStartDistance = 90;
        RenderSettings.fogEndDistance = 520;

        // ---------- Vehículo (carril derecho) con capó visible
        var vehiculo = new GameObject("Vehiculo");
        vehiculo.transform.SetParent(raiz);
        vehiculo.transform.position = new Vector3(1.9f, 0, 0);
        vehiculo.AddComponent<VehiculoSimulado>();
        var gps = vehiculo.AddComponent<GPSSimulado>();
        gps.rutas = AssetDatabase.LoadAssetAtPath<TextAsset>("Assets/Baches/Datos/rutas_ecuador.json");
        if (gps.rutas == null) Debug.LogWarning("[Baches] Falta Assets/Baches/Datos/rutas_ecuador.json: el GPS irá en línea recta.");

        var carroceria = GameObject.CreatePrimitive(PrimitiveType.Cube);
        carroceria.name = "Carroceria";
        carroceria.transform.SetParent(vehiculo.transform, false);
        carroceria.transform.localPosition = new Vector3(0, 0.7f, -1.2f);
        carroceria.transform.localScale = new Vector3(1.8f, 1.2f, 4f);
        carroceria.GetComponent<Renderer>().sharedMaterial = CrearMaterial("Vehiculo", new Color(0.95f, 0.8f, 0.1f));

        var capo = GameObject.CreatePrimitive(PrimitiveType.Sphere);
        capo.name = "Capo";
        Object.DestroyImmediate(capo.GetComponent<Collider>());
        capo.transform.SetParent(vehiculo.transform, false);
        capo.transform.localPosition = new Vector3(0, 0.6f, 1.35f);
        capo.transform.localScale = new Vector3(2.6f, 0.5f, 2.3f);
        capo.GetComponent<Renderer>().sharedMaterial = CrearMaterial("Capo", new Color(0.055f, 0.063f, 0.075f));

        if (cam == null)
        {
            cam = new GameObject("Main Camera", typeof(Camera), typeof(AudioListener)).GetComponent<Camera>();
            cam.tag = "MainCamera";
        }
        cam.transform.SetParent(vehiculo.transform, false);
        cam.transform.localPosition = new Vector3(0, 1.55f, 0.9f);
        cam.transform.localRotation = Quaternion.Euler(9, 0, 0);
        cam.fieldOfView = 62;
        cam.nearClipPlane = 0.1f;
        cam.farClipPlane = 700;
        cam.clearFlags = CameraClearFlags.Skybox;
        cam.rect = new Rect(0, 0, 1, 1);
        if (!cam.TryGetComponent(out CamaraDetectorYOLO detector)) detector = cam.gameObject.AddComponent<CamaraDetectorYOLO>();
        detector.gps = gps;

        // ---------- Auto rojo que va delante
        var auto = new GameObject("AutoRojo").AddComponent<AutoNPC>();
        auto.transform.SetParent(raiz);
        auto.transform.position = new Vector3(-1.9f, 0, 32);
        auto.objetivo = vehiculo.transform;
        auto.carroceria = CrearMaterial("Auto_Rojo", new Color(0.7f, 0.12f, 0.16f));
        auto.vidrios = CrearMaterial("Auto_Vidrios", new Color(0.22f, 0.08f, 0.1f));
        auto.luces = CrearMaterial("Auto_Luces", new Color(1f, 0.25f, 0.25f), emision: new Color(1f, 0.2f, 0.2f));
        auto.llantas = CrearMaterial("Auto_Llantas", new Color(0.06f, 0.06f, 0.06f));

        // ---------- Mapa de Ecuador (minimapa)
        var mapaGO = new GameObject("MapaEcuador");
        mapaGO.transform.SetParent(raiz);
        mapaGO.transform.position = PosicionMapa;
        var mapa = mapaGO.AddComponent<MapaEcuador>();

        var quad = GameObject.CreatePrimitive(PrimitiveType.Quad);
        quad.name = "TexturaMapa";
        quad.transform.SetParent(mapaGO.transform, false);
        quad.transform.localRotation = Quaternion.Euler(90, 0, 0);   // mira hacia arriba, norte = +Z
        quad.transform.localScale = new Vector3(mapa.anchoMundo, mapa.altoMundo, 1);
        quad.GetComponent<Renderer>().sharedMaterial =
            CrearMaterial("MapaEcuador", Color.white, Textura("MapaEcuador", false), sinLuz: true);

        var camMapa = new GameObject("CamaraMapa").AddComponent<Camera>();
        camMapa.transform.SetParent(raiz);
        camMapa.transform.position = PosicionMapa + Vector3.up * 100;
        camMapa.transform.rotation = Quaternion.Euler(90, 0, 0);
        camMapa.orthographic = true;
        camMapa.orthographicSize = mapa.altoMundo / 2 + 1;
        camMapa.clearFlags = CameraClearFlags.SolidColor;
        camMapa.backgroundColor = new Color(0.66f, 0.81f, 0.9f);
        camMapa.rect = new Rect(0.69f, 0.02f, 0.3f, 0.5f);   // minimapa abajo a la derecha
        camMapa.depth = cam.depth + 1;
        camMapa.farClipPlane = 200;

        var baches = new GameObject("BachesEnMapa").AddComponent<BachesEnMapa>();
        baches.transform.SetParent(raiz);
        baches.mapa = mapa;
        baches.camaraMapa = camMapa;
        baches.gpsVehiculo = gps;

        AssetDatabase.SaveAssets();
        EditorSceneManager.MarkSceneDirty(EditorSceneManager.GetActiveScene());
        EditorSceneManager.SaveOpenScenes();
        Selection.activeGameObject = vehiculo;
        Debug.Log("[Baches] Escena configurada. Inicia el servidor (uvicorn app:app --port 8000) y pulsa Play. W/A/S/D para manejar.");
    }

    static Texture2D Textura(string nombre, bool repetir)
    {
        string ruta = $"{CarpetaTexturas}/{nombre}.png";
        if (AssetImporter.GetAtPath(ruta) is TextureImporter imp)
        {
            imp.maxTextureSize = 2048;
            imp.wrapMode = repetir ? TextureWrapMode.Repeat : TextureWrapMode.Clamp;
            imp.alphaIsTransparency = !repetir;
            imp.anisoLevel = repetir ? 8 : 1;
            imp.mipmapEnabled = true;
            imp.SaveAndReimport();
        }
        var tex = AssetDatabase.LoadAssetAtPath<Texture2D>(ruta);
        if (tex == null) Debug.LogWarning($"[Baches] Falta {ruta}. Genérala con los scripts de backend/herramientas/");
        return tex;
    }

    static Material CrearMaterial(string nombre, Color color, Texture textura = null, bool sinLuz = false, bool recorteAlfa = false,
                                  bool transparente = false, Color? emision = null)
    {
        if (!AssetDatabase.IsValidFolder(CarpetaMateriales))
            AssetDatabase.CreateFolder("Assets/Baches", "Materiales");
        string ruta = $"{CarpetaMateriales}/{nombre}.mat";
        var mat = AssetDatabase.LoadAssetAtPath<Material>(ruta);
        if (mat == null)
        {
            var shader = Shader.Find(sinLuz ? "Universal Render Pipeline/Unlit" : "Universal Render Pipeline/Lit");
            if (shader == null) shader = Shader.Find(sinLuz ? "Unlit/Texture" : "Standard");
            mat = new Material(shader);
            AssetDatabase.CreateAsset(mat, ruta);
        }
        mat.color = color;
        if (textura) mat.mainTexture = textura;
        if (mat.HasProperty("_Smoothness")) mat.SetFloat("_Smoothness", 0.15f);
        if (recorteAlfa)
        {
            mat.SetFloat("_AlphaClip", 1);
            mat.SetFloat("_Cutoff", 0.4f);
            mat.EnableKeyword("_ALPHATEST_ON");
            mat.renderQueue = (int)RenderQueue.AlphaTest;
        }
        if (transparente)
        {
            mat.SetFloat("_Surface", 1);
            mat.SetFloat("_Blend", 0);
            mat.SetFloat("_SrcBlend", (float)BlendMode.SrcAlpha);
            mat.SetFloat("_DstBlend", (float)BlendMode.OneMinusSrcAlpha);
            mat.SetFloat("_ZWrite", 0);
            mat.EnableKeyword("_SURFACE_TYPE_TRANSPARENT");
            mat.renderQueue = (int)RenderQueue.Transparent;
        }
        if (emision is Color e)
        {
            mat.EnableKeyword("_EMISSION");
            mat.SetColor("_EmissionColor", e);
        }
        EditorUtility.SetDirty(mat);
        return mat;
    }
}

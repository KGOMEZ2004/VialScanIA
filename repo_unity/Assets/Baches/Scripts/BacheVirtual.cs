using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// Marca un objeto de la escena como daño real (verdad de terreno): bache, grieta o hundimiento.
/// Lo usa el modo "Simulado" de CamaraDetectorYOLO cuando YOLO no está disponible.
/// </summary>
public class BacheVirtual : MonoBehaviour
{
    public static readonly List<BacheVirtual> Todos = new();

    [Tooltip("bache, grieta o hundimiento")]
    public string tipo = "bache";
    [Tooltip("Tamaño principal en metros (diámetro del bache / largo de la grieta)")]
    public float diametro = 1f;
    [HideInInspector] public bool reportado;

    public string Severidad => tipo switch
    {
        "grieta" => diametro > 3.8f ? "grave" : diametro > 2.6f ? "moderado" : "leve",
        "hundimiento" => diametro > 2.2f ? "grave" : diametro > 1.5f ? "moderado" : "leve",
        _ => diametro > 1.7f ? "grave" : diametro > 1.1f ? "moderado" : "leve",
    };

    Renderer rend;
    public Bounds Limites => rend != null ? rend.bounds : new Bounds(transform.position, Vector3.one * diametro);

    void Awake() => rend = GetComponent<Renderer>();
    void OnEnable() => Todos.Add(this);
    void OnDisable() => Todos.Remove(this);
}

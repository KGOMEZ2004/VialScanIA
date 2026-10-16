using UnityEngine;
#if ENABLE_INPUT_SYSTEM
using UnityEngine.InputSystem;
#endif

/// <summary>Control simple del vehículo: W/S (o flechas) acelera y frena, A/D gira.</summary>
public class VehiculoSimulado : MonoBehaviour
{
    public float velocidadMax = 15f;   // m/s (~54 km/h)
    public float aceleracion = 6f;
    public float giro = 60f;

    public float Velocidad { get; private set; }

    void Update()
    {
        LeerEntrada(out float v, out float h);

        Velocidad = Mathf.MoveTowards(Velocidad, v * velocidadMax, aceleracion * Time.deltaTime);
        transform.Translate(Vector3.forward * Velocidad * Time.deltaTime);
        if (Mathf.Abs(Velocidad) > 0.1f)
            transform.Rotate(0, h * giro * Time.deltaTime * Mathf.Sign(Velocidad), 0);
    }

    static void LeerEntrada(out float v, out float h)
    {
#if ENABLE_INPUT_SYSTEM
        var k = Keyboard.current;
        v = h = 0;
        if (k == null) return;
        if (k.wKey.isPressed || k.upArrowKey.isPressed) v += 1;
        if (k.sKey.isPressed || k.downArrowKey.isPressed) v -= 1;
        if (k.dKey.isPressed || k.rightArrowKey.isPressed) h += 1;
        if (k.aKey.isPressed || k.leftArrowKey.isPressed) h -= 1;
#else
        v = Input.GetAxis("Vertical");
        h = Input.GetAxis("Horizontal");
#endif
    }
}

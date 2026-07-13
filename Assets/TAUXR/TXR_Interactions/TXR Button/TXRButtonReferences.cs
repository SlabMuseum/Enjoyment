using TMPro;
using UnityEngine;

public class TXRButtonReferences : MonoBehaviour
{
    public TXRButton ButtonBehavior;
    public TXRButtonVisuals ButtonVisuals;
    public TXRButtonInput ButtonInput;

    public Transform ButtonSurface;
    public AudioSource SoundPress;
    public AudioSource SoundRelease;

    public Shapes.Rectangle Backface;
    public Shapes.Rectangle Stroke;
    public TextMeshPro Text;
    public ButtonVisualsConfigurations Configurations;

    public Color ActiveColor;
    public Color PressedColor;
    public Color DisabledColor;
    public Color HoverGradientColor;
}

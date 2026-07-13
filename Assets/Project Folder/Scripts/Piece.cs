using UnityEngine;
using UnityEngine.UI;

public class Piece : MonoBehaviour
{
    public RawImage imageComponent;
    public Arrow arrow;
    public AudioGuideButton audioGuideButton;
    public AudioClip audioGuideClip;
    public Texture2D resizedImage;
    public Transform questionBoardPositioner;
    public ArtPieceProximityDetector proximityDetector;
    public Collider imageCollider;

}


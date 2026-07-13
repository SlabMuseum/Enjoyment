using TMPro;
using UnityEngine;

public class FollowEyeSphere : MonoBehaviour
{
    [SerializeField] private float lerpSpeed;
    private TXRPlayer player;
    private TextMeshPro focusedObjectText;


    private void Start()
    {
        focusedObjectText = GetComponentInChildren<TextMeshPro>();
        player = TXRPlayer.Instance;

    }

    private void Update()
    {
        transform.position = Vector3.Lerp(transform.position, player.EyeGazeHitPosition,
            lerpSpeed * Time.deltaTime);
        UpdateFocusedObjectText();
    }

    private void UpdateFocusedObjectText()
    {
        if (focusedObjectText != null)
        {
            if (player.FocusedObject != null)
            {
                focusedObjectText.text = player.FocusedObject.name;

                Vector3 reverseDirection = (transform.position - player.PlayerHead.position).normalized;
                transform.rotation = Quaternion.LookRotation(reverseDirection);
            }
            else
            {
                focusedObjectText.text = "Nothing";
            }
        }
    }
}
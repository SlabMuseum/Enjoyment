using Shapes;
using TMPro;
using UnityEngine;

public class AudioTimeLeft : MonoBehaviour
{
    private AudioSource audioSource;
    private float timeLeft;
    public TextMeshPro text;
    public Line line;

    private Piece _piece;
    private Vector3 initialLineLength;
    private float initialLineLengthX;
    private float initilTime;


    void Start()
    {
        audioSource = GetComponentInParent<AudioGuideButton>().GetComponent<AudioSource>();
        if (audioSource == null)
        {
            Debug.LogError("DEBUG: AudioSource not found in " + gameObject.name);
        }

        _piece = GetComponentInParent<AudioGuideButton>().GetComponentInParent<Piece>();
        if (_piece == null)
        {
            Debug.LogError("DEBUG: Piece component not found in " + gameObject.name);
        }
        initialLineLengthX = line.End.x;
        initilTime = _piece.audioGuideClip.length;
    }

    // Update is called once per frame
    void Update()
    {
        if (!audioSource.isPlaying)
        {
            return;
        }
        timeLeft = audioSource.clip.length - audioSource.time;

        // Calculate minutes and seconds
        int minutes = Mathf.FloorToInt(timeLeft / 60);
        int seconds = Mathf.FloorToInt(timeLeft % 60);

        // Format the time as "00:00"
        string timeFormatted = string.Format("{0:00}:{1:00}", minutes, seconds);

        // Assign the formatted string to the text component
        text.text = timeFormatted;

        // Update the line length
        line.End = new Vector3(initialLineLengthX * (timeLeft / initilTime), line.End.y, line.End.z);

    }
}

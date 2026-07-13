using UnityEngine;
using UnityEngine.Events;
using TMPro;

// currently not used. To be implemented in the future.
public enum SliderState
{
    Unrated,
    BeingRatedNow,
    WasRated
}

public class TXRSlider : MonoBehaviour
{
    [Header("Configuration")]
    [Range(0f, 1f)]
    [SerializeField] float valueStart = .5f;
    [Range(0f, 1f)]
    [SerializeField] float stepSize = .01f;
    [SerializeField] bool ShouldShowTextValue = true;

    [Header("References")]
    [SerializeField] Transform lineStart;
    [SerializeField] Transform lineEnd;

    [SerializeField] LineRenderer lineBackground;
    [SerializeField] LineRenderer lineValue;

    [SerializeField] TXRButton touchButton;         // need to get a referece to the touchButton to get the toucher transform.

    [SerializeField] TextMeshPro valueText;
    [SerializeField] AudioSource soundTick;

    // the Transform touching the slider node.
    Transform toucher;
    bool isNodeTouched = false;

    float valueCurrent = 0;

    Transform node;
    Vector3 nodePositionTarget;
    float nodeLerpSpeed = 15f;
    float detachmentDistanceThreshold = .1f;    

    private float playTickStepFrequency = .05f;
    float valueLastTick = 0;

    [Header("Events")]

    public UnityEvent SliderReset;
    public UnityEvent NodeTouched;
    public UnityEvent NodeDetached;
    public float Value => valueCurrent;

    // Call to reset slider value and states.
    public void Reset()
    {
        Init();
    }

    public void Reset(float resetToValue)
    {
        valueStart = resetToValue;
        Init();
    }


    private void Start()
    {
        Init();
    }

    private void Init()
    {
        valueStart = RoundToStepSize(stepSize, valueStart);
        valueCurrent = valueStart;
        valueLastTick = valueStart;

        valueText.GetComponent<MeshRenderer>().enabled = ShouldShowTextValue;
        UpdateValueText(valueStart);

        node = touchButton.transform;
        node.position = TAUXRUtilities.GetPointOnLineFromNormalizedValue(lineStart.position, lineEnd.position, valueStart);
        nodePositionTarget = node.position;        

        SliderReset.Invoke();
    }

    // TODO: improve and move to TAUXRFunctions.
    private float RoundToStepSize(float stepSize, float clampedValue)
    {
        stepSize = Mathf.Clamp01(stepSize);
        float multiplicand = Mathf.Round(clampedValue / stepSize);
        return stepSize * multiplicand;
    }
    private void UpdateValueText(float value)
    {
        if (valueText != null)
        {
            //valueText.text = (value * 100f).ToString();
            valueText.text = (Mathf.CeilToInt(value * 100f)).ToString();
        }
    }


    private void Update()
    {
        // Set background line position in runtime.
        SetLineRendererPositions(lineBackground, lineStart.position, lineEnd.position, 0f);

        if (isNodeTouched)
        {
            // Calculate node position based on touching finger position
            nodePositionTarget = TAUXRUtilities.GetClosestPointOnLine(lineStart.position, lineEnd.position, toucher.position);

            // Checks if finger is still sliding
            if (ShouldDetachNode(toucher.position, nodePositionTarget, detachmentDistanceThreshold))
            {
                DetachNodeFromToucher();
            }
            
            // Calculate slider value based on finger percise position on slider line.
            valueCurrent = TAUXRUtilities.GetNormalizedValueFromPointOnLine(lineStart.position, lineEnd.position, nodePositionTarget);
            valueCurrent = RoundToStepSize(stepSize,valueCurrent);

            // Update node position target to match step size round.
            nodePositionTarget = TAUXRUtilities.GetPointOnLineFromNormalizedValue(lineStart.position, lineEnd.position, valueCurrent);

            if (ShouldPlayTickSound())
            {
                valueLastTick = valueCurrent;
                PlayTickAudio();
            }

            DebugShowDetachmentLine();
            UpdateValueText(valueCurrent);
        }

        // this line is out of isNodeTouch to allow node continue moving after finger left button (especially in cases the node is placed on 0/100).
        node.position = Vector3.Lerp(node.position, nodePositionTarget, nodeLerpSpeed * Time.deltaTime);

        // Set value line position in runtime.
        SetLineRendererPositions(lineValue, lineStart.position, node.position, -.001f);

        // make node infront of lines
        Vector3 nodeLocalPosition = node.localPosition;
        nodeLocalPosition.z = -.002f;
        node.localPosition = nodeLocalPosition;
    }

    private void SetLineRendererPositions(LineRenderer line, Vector3 start, Vector3 end, float lineLocalDepthValue)
    {
        line.transform.position = start;
        line.transform.rotation = Quaternion.LookRotation(end - start, line.transform.up);
        line.SetPosition(1, new Vector3(0, 0, (end - start).magnitude));
        
        // TODO: Move to shader!
        // moves the line on its local z axis to allow multiple lines depth organization.
        Vector3 linePosition = line.transform.localPosition;
        linePosition.z = lineLocalDepthValue;
        line.transform.localPosition = linePosition;
    }
    private bool ShouldDetachNode(Vector3 toucherPosition, Vector3 linePoint, float threshold)
    {
        float toucherToLineDistance = (toucherPosition - linePoint).magnitude;
        return (toucherToLineDistance > threshold);
    }
    
    // Ends the rating action by detaching node from toucher.
    private void DetachNodeFromToucher()
    {
        touchButton.TriggerButtonEventFromCode(ButtonEvent.Released, ButtonColliderResponse.Internal);
        NodeDetached.Invoke();

        isNodeTouched = false;
    }

    private bool ShouldPlayTickSound()
    {
        return Mathf.Abs(valueCurrent - valueLastTick) >= playTickStepFrequency;
    }
    private void PlayTickAudio()
    {
        if (soundTick == null) return;

        soundTick.Stop();
        soundTick.Play();
    }

    private void DebugShowDetachmentLine()
    {
        Vector3 toucherDirection = (toucher.position - nodePositionTarget).normalized;
        Vector3 detachmentPoint = nodePositionTarget + toucherDirection * detachmentDistanceThreshold;
        Debug.DrawLine(nodePositionTarget, detachmentPoint, Color.red);

        Debug.DrawLine(lineStart.position, nodePositionTarget, Color.green);
    }


    // Called from the TAUXRButton used as the slider node.
    public void OnNodeTouched()
    {
        if (isNodeTouched) return;

        // Activate button internal response from the slider script so it will be called only on the first press.
        touchButton.TriggerButtonEventFromCode(ButtonEvent.Pressed, ButtonColliderResponse.Internal);
        NodeTouched.Invoke();

        toucher = touchButton.ActiveToucher;
        isNodeTouched = true;
    }
}

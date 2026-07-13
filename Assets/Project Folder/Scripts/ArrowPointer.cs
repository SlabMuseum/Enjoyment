using UnityEngine;

//Obsolete class, use DirectionGuideArrow instead
public class ArrowPointer : MonoBehaviour
{
    public Transform target; // Reference to the target GameObject
    private Transform _playerHead;

    public float radius;
    public float heightOffset;

    private float initialRadius;

    private Vector3 arrowPosition;

    public Vector3 arrowOffset;

    void Update()
    {
        if (target != null)
        {
            Vector3 direction = (target.position - _playerHead.position).normalized;
            UpdateRadius();
            transform.position = _playerHead.position + arrowOffset + (direction * radius + Vector3.up * heightOffset);
            transform.LookAt(target);
        }
    }

    public void Show() { gameObject.SetActive(true); }
    public void Hide() { gameObject.SetActive(false); }

    public void SetTarget(Transform newTarget)
    {
        target = newTarget;
    }

    public void ShowAndSetTarget(Transform newTarget)
    {
        SetTarget(newTarget);
        Show();
    }

    private void Start()
    {
        _playerHead = TXRPlayer.Instance.PlayerHead;
        initialRadius = radius;
    }

    // if the player is close to the target' update the radius to avoid the arrow to be inside the target
    private void UpdateRadius()
    {
        Vector3 distanceToTarget = target.position - _playerHead.position;
        if (distanceToTarget.magnitude < radius)
        {
            Debug.Log("distance to target: " + distanceToTarget.magnitude);
            radius = distanceToTarget.magnitude;
        }
        else
        {
            radius = initialRadius;
        }
    }

}

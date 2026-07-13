using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class LookAtButton : MonoBehaviour
{
    public float LookAtSpeed;
    Transform lookTarget;
    Quaternion targetRotation;
    Quaternion startRotation;

    void Start()
    {
        startRotation = transform.localRotation;
    }

    void Update()
    {
        if (lookTarget != null)
            targetRotation = Quaternion.LookRotation(lookTarget.position - transform.position, transform.up);
        else
            targetRotation = transform.parent.rotation;

        transform.rotation = Quaternion.Slerp(transform.rotation, targetRotation, LookAtSpeed * Time.deltaTime);
    }

    public void SetLookTarget(Transform target)
    {
        lookTarget = target;
    }

    public void RemoveTarget(Transform target)
    {
        if (lookTarget != target)
            return;

        lookTarget = null;
    }
}
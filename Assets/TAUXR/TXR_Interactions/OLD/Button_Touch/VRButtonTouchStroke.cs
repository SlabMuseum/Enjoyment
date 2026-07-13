using System.Collections;
using System.Collections.Generic;
using TMPro;
using UnityEngine;

public class VRButtonTouchStroke : MonoBehaviour
{
    public Transform buttonSurface;
    public Transform activeToucher;
    public float DISTANCE_DEFAULT = .03f;

    public float DISTANCE_MAX = .06f;
    public float DISTANCE_MIN = .01f;
    
    public float ANGLE_MAX = 25f;
    public float ANGLE_MIN = -25f;

    public float lerpSpeedPosition= 10;
    public float lerpSpeedRotation= 10;

    Vector3 targetPosition;
    Quaternion targetRotation;
    Quaternion startRotation;

    public void Init(Transform buttonTransform)
    {
        buttonSurface = buttonTransform;
        startRotation = transform.rotation;
        transform.position = GetPositionAlongLine(buttonSurface.position, buttonSurface.forward, DISTANCE_DEFAULT);
    }


    public void UpdateStrokeBehavior(Vector3 toucherPosition)
    {
        if (toucherPosition != Vector3.zero)
        {
            targetPosition = GetClosestPointOnLine(buttonSurface.position, buttonSurface.forward, toucherPosition);
            targetRotation = GetLookAtRotationWithLimits(toucherPosition, ANGLE_MIN, ANGLE_MAX);
            
        }
        else
        {
            targetPosition = GetPositionAlongLine(buttonSurface.position, buttonSurface.forward, DISTANCE_DEFAULT);
            targetRotation = startRotation;
        }

        transform.position = Vector3.Lerp(transform.position, targetPosition, lerpSpeedPosition * Time.deltaTime);
        targetRotation = Quaternion.Slerp(transform.rotation, targetRotation, lerpSpeedRotation * Time.deltaTime);
        transform.eulerAngles = GetEulerRotationWithoutZ(targetRotation);
    }

    private Vector3 GetEulerRotationWithoutZ(Quaternion rotation)
    {
        Vector3 eulerRotation = rotation.eulerAngles;
        eulerRotation.z = 0;
        return eulerRotation;
    }


    Vector3 GetClosestPointOnLine(Vector3 lineStart, Vector3 lineDirection, Vector3 point)
    {
        Vector3 pointVector = point - lineStart;
        float projectionLength = Vector3.Dot(pointVector, lineDirection);
        projectionLength = Mathf.Clamp(projectionLength, DISTANCE_MIN, DISTANCE_MAX);
        return lineStart + lineDirection * projectionLength;
    }

    private Vector3 GetPositionAlongLine(Vector3 lineStart, Vector3 lineDirection, float normalizedPosition)
    {
        normalizedPosition = Mathf.Clamp(normalizedPosition, DISTANCE_MIN, DISTANCE_MAX);
        return lineStart + (lineDirection.normalized * normalizedPosition);
    }

    private Quaternion GetLookAtRotationWithLimits(Vector3 targetPosition, float angleMin, float angleMax)
    {
        Vector3 lookDirection = targetPosition - buttonSurface.position;
        float lookAngle = Vector3.Angle(lookDirection, buttonSurface.forward);
        Debug.DrawRay(buttonSurface.position, lookDirection);
        Debug.DrawRay(buttonSurface.position, buttonSurface.forward);

        if(lookAngle > angleMin && lookAngle < angleMax)
        {
            Quaternion lookRotation = Quaternion.LookRotation(lookDirection, transform.up);
            return lookRotation;
        }
        return transform.rotation;

    }
}

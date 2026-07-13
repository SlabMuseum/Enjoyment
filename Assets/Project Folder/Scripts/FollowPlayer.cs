using UnityEngine;


public enum HeightOffsetType
{
    FromGround,
    FromPlayer,
    FromHand
}

public class FollowPlayer : MonoBehaviour
{
    [SerializeField] private HeightOffsetType _heightOffsetType;
    [SerializeField] private bool isRightHand;
    [SerializeField] float _heightOffset = 1f;
    [SerializeField] float _radius = 1f;
    [SerializeField] float _angle;
    [SerializeField] private Vector3 _rotationOffset;
    [SerializeField] private bool _shouldLookAtPlayer = true;
    //[SerializeField] private float _maxDistance = .4f;
    [SerializeField] private float lerpSpeed = 5f;
    [SerializeField] private float _minDistanceToControl = .3f;
    [SerializeField] private float _angleOffset = 5f;
    private Vector3 _handPositionLastFrame;

    void LateUpdate()
    {
        if (TXRPlayer.Instance == null) return;

        Vector3 targetPosition = GetTargetPositionOnCircle();
        Quaternion targetRotation = GetTargetRotation(targetPosition);
        targetRotation.eulerAngles += _rotationOffset;
        float distance = Vector3.Distance(transform.position, targetPosition);

        transform.position = Vector3.Lerp(transform.position, targetPosition, lerpSpeed * Time.deltaTime);
        if (_shouldLookAtPlayer)
            transform.rotation = Quaternion.Slerp(transform.rotation, targetRotation, lerpSpeed * Time.deltaTime);
    }

    private Vector3 GetTargetPositionOnCircle()
    {
        float heightOffset = _heightOffset;
        float radius = _radius;
        // float angle = Mathf.Deg2Rad * _angle + 1.57f;       // 1.57 radians are 90 deg. without it 0 angle point towards X, with this offset we will use Z as forward.
        //float angle = Mathf.Deg2Rad * (_angle - TXRPlayer.Instance.PlayerHead.eulerAngles.y) + 1.57f; // 1.57 radians are 90 deg. without it 0 angle point towards X, with this offset we will use Z as forward.\
        Vector3 headPosition = TXRPlayer.Instance.PlayerHead.position;

        Vector3 circleCenter = headPosition;
        //// TODO: height is according to last hand height
        circleCenter.y = _heightOffsetType == HeightOffsetType.FromPlayer ? headPosition.y + heightOffset : heightOffset;
        Vector3 handPosition = isRightHand ? TXRPlayer.Instance.RightHand.position : TXRPlayer.Instance.LeftHand.position;

        //If hand is tracking
        bool isHandTracking = handPosition != _handPositionLastFrame;
        if (Vector3.Distance(handPosition, transform.position) < _minDistanceToControl)
        {
            // circleCenter.y = Mathf.Max(headPosition.y + _minHeightFromHead, handPosition.y);

            handPosition.y = circleCenter.y;    // normalizing y for angle calculations.
            Vector3 direction = (handPosition - circleCenter).normalized;
            //   Vector3 headForward = TXRPlayer.Instance.PlayerHead.forward;
            Vector3 headForward = TXRPlayer.Instance.transform.forward;
            headForward.y = direction.y;
            _angle = Vector3.SignedAngle(headForward, direction, Vector3.up) * -1f;
            _angle += _angleOffset;
            lerpSpeed = 20f;

        }
        else
        {
            lerpSpeed = 4f;
            print("HAND OUT OF TRACKING, angle: " + _angle);
        }
        _handPositionLastFrame = handPosition;
        _angle = GetAngleByPlayerGlobalLookDirection();
        // _angle is set in GetPositionNearHand according to hand position.
        float targetX = radius * Mathf.Cos(Mathf.Deg2Rad * _angle + 1.57f);
        float targetZ = radius * Mathf.Sin(Mathf.Deg2Rad * _angle + 1.57f);
        Vector3 targetPosition = circleCenter + new Vector3(targetX, 0, targetZ);

        return targetPosition;
    }

    private Quaternion GetTargetRotation(Vector3 targetPosition)
    {
        Vector3 headPosition = TXRPlayer.Instance.PlayerHead.position;
        Vector3 rotationAnchor = _shouldLookAtPlayer ? headPosition : headPosition + new Vector3(0, _heightOffset, 0);
        Quaternion targetRotation = Quaternion.LookRotation(rotationAnchor - targetPosition, Vector3.up);
        targetRotation.eulerAngles += _rotationOffset;
        return targetRotation;
    }

    private float GetAngleByPlayerGlobalLookDirection()
    {
        Vector3 playerLookProjectedOnZ = TXRPlayer.Instance.PlayerHead.forward;
        //Vector3 playerLookProjectedOnZ = TXRPlayer.Instance.transform.forward;
        playerLookProjectedOnZ.y = 0;
        float playerLookAngle = Vector3.SignedAngle(playerLookProjectedOnZ, Vector3.forward, Vector3.up);
        //print(playerLookAngle);

        if (playerLookAngle < 45f && playerLookAngle > -45f)
        {
            // point forward
            return 0f;
        }
        else if (playerLookAngle > 45f && playerLookAngle < 135f)
        {
            // point left
            return 90f;
        }
        else if ((playerLookAngle > 135f || playerLookAngle < -135f))
        {
            // point back
            return 180f;
        }
        else if ((playerLookAngle > -135f || playerLookAngle < -45f))
        {
            // point right
            return -90f;
        }
        else
        {
            return 0f;
        }
    }

    public Vector3 GetPositionNearHand()
    {
        Vector3 headPosition = TXRPlayer.Instance.PlayerHead.position;
        Vector3 handPosition = isRightHand ? TXRPlayer.Instance.RightHand.position : TXRPlayer.Instance.LeftHand.position;
        Vector3 anchor = headPosition;
        anchor.y = handPosition.y;
        Vector3 direction = (handPosition - anchor) * _radius;
        Vector3 targetPosition = anchor + direction + new Vector3(0, _heightOffset, 0);

        _angle = Vector3.SignedAngle(TXRPlayer.Instance.PlayerHead.forward, direction, Vector3.up);

        return targetPosition;
    }
}

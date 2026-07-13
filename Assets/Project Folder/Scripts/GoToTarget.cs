using Cysharp.Threading.Tasks;
using Sirenix.OdinInspector;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using UnityEngine.AI;

public class GoToTarget : MonoBehaviour
{
    [ReadOnly]
    public Transform player;
    //[ReadOnly]
    public Transform target;
    public float distanceFromPlayer = 3.0f;
    public float heightOffsetFromPlayer = -1.5f;
    private NavMeshPath path;
    private int currentSegmentEnd = 0;
    public float lerpSpeed = 3f;
    private bool isPathCalculated = false;
    private Vector3 nextPoint;

    private Vector3 closestPointToPlayer;
    private List<Vector3> spline = new List<Vector3>();
    public int segments = 10;
    private AudioSource audioSource;

    void Awake()
    {
        path = new NavMeshPath();
        
        audioSource = GetComponent<AudioSource>();
    }


    private void Start()
    {
        player = TXRPlayer.Instance.PlayerHead;
    }
    void Update()
    {
        // Calculate the path to the target


        // Move the arrow along the path
        if (spline.Count > 1)
        {

            (closestPointToPlayer, nextPoint) = findPlayerPointOnPathAndArrowPosition();
            Vector3 direction;
            if (currentSegmentEnd == spline.Count - 1)
            {
                //transform.LookAt(target);
                direction = (target.position - spline[spline.Count - 1]).normalized;
            }
            else
            {
                //transform.LookAt(spline[currentSegmentEnd]);
                direction = (spline[currentSegmentEnd] - spline[currentSegmentEnd - 1]).normalized;

            }
            Quaternion rotation = Quaternion.LookRotation(direction);
            transform.rotation = Quaternion.Slerp(transform.rotation, rotation, Time.deltaTime * lerpSpeed);
            //transform.position = nextPoint;
            transform.position = Vector3.Slerp(transform.position, nextPoint, Time.deltaTime * lerpSpeed);

        }
    }

    void OnDrawGizmos()
    {
        if (spline != null)
        {
            Gizmos.color = Color.red;
            for (int i = 0; i < spline.Count - 1; i++)
            {
                Gizmos.DrawLine(spline[i], spline[i + 1]);
                Gizmos.DrawSphere(spline[i], 0.05f);
            }

        }
        if (path != null)
        {
            Gizmos.color = Color.magenta;
            for (int i = 0; i < path.corners.Length - 1; i++)
            {
                Gizmos.DrawLine(path.corners[i], path.corners[i + 1]);
                Gizmos.DrawSphere(path.corners[i], 0.03f);
            }

        }
        // Draw the closest point to the player
        if (closestPointToPlayer != Vector3.zero)
        {
            Gizmos.color = Color.blue;
            Gizmos.DrawSphere(closestPointToPlayer, 0.1f);
        }

        // Draw the next point
        if (nextPoint != Vector3.zero)
        {
            Gizmos.color = Color.green;
            Gizmos.DrawSphere(nextPoint, 0.1f);
        }
    }

    [Button("Calculate Path")]
    void CalculatePath()
    {
        path.ClearCorners();
        spline.Clear();
        NavMeshHit hit;

        // Sample the closest point on the NavMesh within maxDistance
        if (NavMesh.SamplePosition(target.position, out hit, 100, NavMesh.AllAreas))
        {
            // Use hit.position as the target position
            Debug.Log("Closest point on NavMesh: " + hit.position);
        }
        else
        {
            Debug.LogWarning("Target is too far from the NavMesh.");
        }

        NavMesh.CalculatePath(player.position, hit.position, NavMesh.AllAreas, path);
        spline = CatmullRomSpline.GenerateCatmullRomSpline(path.corners.ToList(), segments);
        spline = SetPathHeight(spline);
        isPathCalculated = true;
    }

    private List<Vector3> SetPathHeight(List<Vector3> path)
    {
        float height = player.position.y + heightOffsetFromPlayer;

        for (int i = 0; i < path.Count; i++)
        {
            path[i] = new Vector3(path[i].x, path[i].y + 1, path[i].z);
        }
        return path;
    }

    public async UniTask ShowAndSetTarget(Transform newTarget, bool showInstruction)
    {
        Show();
        SetTarget(newTarget);
        CalculatePath();
        if (audioSource != null)
        {
            audioSource.Play();
        }
        await UniTask.WaitUntil(() => isPathCalculated);
    }

    public void Hide()
    {
        gameObject.SetActive(false);
    }

    public void Show()
    {
        gameObject.SetActive(true);
    }

    private void SetTarget(Transform newTarget)
    {
        target = newTarget;
    }

    [Button("Play Sound")]
    private void PlaySound()
    {
        if (audioSource != null)
        {
            audioSource.Play();
        }
    }


    (Vector3, Vector3) findPlayerPointOnPathAndArrowPosition()
    {
        Vector3 closestPointToPlayer = spline[0];
        float closestDistance = Vector3.Distance(player.position, closestPointToPlayer);
        Vector3 nextEndSegment = spline[0];
        int startSegmentIndex = 0;
        int endSegmentIndex = 0;
        float remainingDistance = distanceFromPlayer;


        for (int i = 0; i < spline.Count - 1; i++)
        {
            Vector3 segmentStart = spline[i];
            Vector3 segmentEnd = spline[i + 1];
            Vector3 closestPointOnSegment = PointProjection.ProjectPointOnLine(player.position, segmentStart, segmentEnd);//GetClosestPointOnSegment(playerPosition, segmentStart, segmentEnd);

            float distance = Vector3.Distance(player.position, closestPointOnSegment);
            if (distance < closestDistance)
            {
                closestDistance = distance;
                closestPointToPlayer = closestPointOnSegment;
                startSegmentIndex = i;
                endSegmentIndex = i + 1;
            }

        }
        // Calculate the arrow position which is distanceFromPlayer units away from the closest point
        Vector3 currentPoint = closestPointToPlayer;
        Vector3 arrowPosition = spline[spline.Count - 1];
        for (int i = startSegmentIndex; i < spline.Count - 1; i++)
        {

            Vector3 segmentStart = spline[i];
            Vector3 segmentEnd = spline[i + 1];
            Vector3 direction = (segmentEnd - segmentStart).normalized;
            float segmentLength = Vector3.Distance(segmentStart, segmentEnd);
            float distanceToEnd = Vector3.Distance(currentPoint, segmentEnd);

            if (remainingDistance <= distanceToEnd)
            {
                arrowPosition = currentPoint + direction * remainingDistance;
                currentSegmentEnd = i + 1;
                break;
            }
            else
            {
                remainingDistance -= distanceToEnd;
                currentPoint = segmentEnd;
                currentSegmentEnd = i + 1;
            }
        }
        return (closestPointToPlayer, arrowPosition);

    }



}
public class PointProjection
{
    // Function to project a point onto a line segment
    public static Vector3 ProjectPointOnLine(Vector3 point, Vector3 lineStart, Vector3 lineEnd)
    {
        // Calculate the direction vector of the line segment
        Vector3 lineDirection = lineEnd - lineStart;
        float lineLength = lineDirection.magnitude;
        lineDirection.Normalize();

        // Calculate the vector from the start point to the point to be projected
        Vector3 pointToStart = point - lineStart;

        // Project the point onto the line using the dot product
        float projectionLength = Vector3.Dot(pointToStart, lineDirection);
        projectionLength = Mathf.Clamp(projectionLength, 0, lineLength); // Clamp to ensure the projection is within the segment

        // Calculate the projected point
        Vector3 projectedPoint = lineStart + lineDirection * projectionLength;

        return projectedPoint;
    }
}
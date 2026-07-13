using System.Collections.Generic;
using UnityEngine;

public class CatmullRomSpline
{
    public static List<Vector3> GenerateCatmullRomSpline(List<Vector3> points, int segments)
    {
        List<Vector3> splinePoints = new List<Vector3>();

        // Add extra control points at the beginning and end
        List<Vector3> extendedPoints = new List<Vector3>(points);
        extendedPoints.Insert(0, points[0]); // Duplicate the first point
        extendedPoints.Add(points[points.Count - 1]); // Duplicate the last point

        for (int i = 0; i < extendedPoints.Count - 3; i++)
        {
            for (int j = 0; j < segments; j++)
            {
                float t = j / (float)segments;
                Vector3 point = CalculateCatmullRomPoint(t, extendedPoints[i], extendedPoints[i + 1], extendedPoints[i + 2], extendedPoints[i + 3]);
                splinePoints.Add(point);
            }
        }

        // Add the last point explicitly to ensure the spline ends at the last control point
        splinePoints.Add(points[points.Count - 1]);

        return splinePoints;
    }

    public static Vector3 CalculateCatmullRomPoint(float t, Vector3 p0, Vector3 p1, Vector3 p2, Vector3 p3)
    {
        float t2 = t * t;
        float t3 = t2 * t;

        float a0 = -0.5f * t3 + t2 - 0.5f * t;
        float a1 = 1.5f * t3 - 2.5f * t2 + 1.0f;
        float a2 = -1.5f * t3 + 2.0f * t2 + 0.5f * t;
        float a3 = 0.5f * t3 - 0.5f * t2;

        return a0 * p0 + a1 * p1 + a2 * p2 + a3 * p3;
    }
}

using Cysharp.Threading.Tasks;
using System;
using System.Collections.Generic;
using System.IO;
using Unity.Collections;
using UnityEngine;

public class TilesPositionExporter : MonoBehaviour
{

    private Renderer[] planeTileRenderers;
    [SerializeField, ReadOnly]
    private Dictionary<String, Renderer> tileRenderers = new Dictionary<String, Renderer>();

    private void Start()
    {
        planeTileRenderers = GetComponentsInChildren<Renderer>();

        foreach (var tileRenderer in planeTileRenderers)
        {
            String name = tileRenderer.transform.parent.gameObject.name;

            if (tileRenderer.name.Contains("Rectangle")) // ignore rectangle mesh renderers, use only the planes
                continue;

            if (!tileRenderers.ContainsKey(name))
            {
                tileRenderers[name] = tileRenderer;
            }
        }
        ExportTilesPositionAsync().Forget();
    }


    public static Vector3[] GetWorldCorners(Renderer renderer)
    {
        if (renderer == null) return null;

        Bounds bounds = renderer.bounds;

        Vector3 center = bounds.center;
        Vector3 extents = bounds.extents;

        // All 4 corners on the plane assuming it's lying flat (on XZ plane)
        return new Vector3[]
        {
        center + new Vector3(-extents.x, 0, -extents.z), // Bottom-left
        center + new Vector3(-extents.x, 0, extents.z),  // Top-left
        center + new Vector3(extents.x, 0, extents.z),   // Top-right
        center + new Vector3(extents.x, 0, -extents.z),  // Bottom-right
        };
    }

    public async UniTaskVoid ExportTilesPositionAsync()
    {
        string filePath = Path.Combine(Application.persistentDataPath, "TilePositions.csv");

        using (StreamWriter writer = new StreamWriter(filePath))
        {
            // Write header
            writer.WriteLine("name," +
                             "bottom-left_x,bottom-left_z," +
                             "top-left_x,top-left_z," +
                             "top-right_x,top-right_z," +
                             "bottom-right_x,bottom-right_z");

            foreach (var kvp in tileRenderers)
            {
                string tileName = kvp.Key;
                Renderer renderer = kvp.Value;
                Vector3[] corners = GetWorldCorners(renderer);

                if (corners == null || corners.Length != 4) continue;

                string row = $"{tileName}," +
                             $"{corners[0].x},{corners[0].z}," + // bottom-left
                             $"{corners[1].x},{corners[1].z}," + // top-left
                             $"{corners[2].x},{corners[2].z}," + // top-right
                             $"{corners[3].x},{corners[3].z}";   // bottom-right

                writer.WriteLine(row);
                await UniTask.Yield(PlayerLoopTiming.Update);
            }
        }

        Debug.Log($"Exported tile positions info to: {filePath.Replace("\\", "/")}");
    }

}

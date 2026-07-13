using Cysharp.Threading.Tasks;
using System.Collections.Generic;
using System.IO;
using UnityEngine;

public static class ArtPieceColliderExporter
{
    public static async UniTaskVoid ExportCollidersAsync(List<Piece> pieces)
    {
        string filePath = Path.Combine(Application.persistentDataPath, "ArtPieceColliders.csv");

        using (StreamWriter writer = new StreamWriter(filePath))
        {
            writer.WriteLine("name, pos_x, pos_y, pos_z, rot_x, rot_y, rot_z, bounds_x, bounds_y, bounds_z, bounds_size_x, bounds_size_y, bounds_size_z");

            foreach (Piece piece in pieces)
            {
                Collider imageCollider = piece.imageCollider;
                if (piece.gameObject.activeSelf && imageCollider != null && imageCollider.enabled)
                {
                    Transform t = imageCollider.transform;
                    Vector3 pos = t.position;
                    Vector3 rot = t.eulerAngles;
                    Bounds bounds = imageCollider.bounds;

                    writer.WriteLine($"{piece.name}," +
                                     $"{pos.x},{pos.y},{pos.z}," +
                                     $"{rot.x},{rot.y},{rot.z}," +
                                     $"{bounds.center.x},{bounds.center.y},{bounds.center.z}," +
                                     $"{bounds.size.x},{bounds.size.y},{bounds.size.z}");
                }
                else
                {
                    Debug.LogWarning("Can't record collider position! Collider is not enabled or the game object is not active: " + piece.name);
                }

                await UniTask.Yield(PlayerLoopTiming.Update);
            }
        }

        Debug.Log($"Exported collider info to: {filePath.Replace("\\", "/")}");

    }
}


using System.Reflection;
using UnityEditor;
using UnityEngine;
using UnityEngine.UI;

#if UNITY_EDITOR
public static class ImageResizeHelper
{

    public static void AdjustImageWidth(Texture2D origImage, RawImage imageToResize)
    {
        Texture2D texture = origImage;
        if (GetImageSize(texture, out int width, out int height))
        {
            Debug.Log($"Width: {width}, Height: {height}");
        }
        else
        {
            Debug.Log("Failed to get image size");
        }
        float aspectRatio = (float)width / height;
        float newWidth = (float)aspectRatio / height;

        imageToResize.rectTransform.sizeDelta = new Vector2(newWidth, height);
    }


    //https://forum.unity.com/threads/getting-original-size-of-texture-asset-in-pixels.165295/
    private static bool GetImageSize(Texture2D asset, out int width, out int height)
    {
        if (asset != null)
        {
            string assetPath = AssetDatabase.GetAssetPath(asset);
            TextureImporter importer = AssetImporter.GetAtPath(assetPath) as TextureImporter;

            if (importer != null)
            {
                object[] args = new object[2] { 0, 0 };
                MethodInfo mi = typeof(TextureImporter).GetMethod("GetWidthAndHeight", BindingFlags.NonPublic | BindingFlags.Instance);
                mi.Invoke(importer, args);

                width = (int)args[0];
                height = (int)args[1];

                return true;
            }
        }

        height = width = 0;
        return false;
    }
}
#endif // UNITY_EDITOR

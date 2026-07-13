using System.Reflection;
using UnityEditor;
using UnityEngine;
using UnityEngine.UI;

public class BinaryAnswer : MonoBehaviour
{


    public RawImage _image;
    public GameObject _colliders;
    public float imageFixedWidth = 0.5f;

    private float _imageToColliderScalar = 15f;
    //TODO: FIX FOR BUILDDDDDD
#if UNITY_EDITOR
    void Start()
    {
        ResizeImage();
        MatchCollidersSizeToImage();
    }


    public void SetImage(Texture2D image)
    {
        _image.texture = image;
        _image.color = Color.white;
        ResizeImage();
        MatchCollidersSizeToImage();
    }

    private void ResizeImage()
    {
        Texture2D texture = (Texture2D)_image.texture;
        if (GetImageSize(texture, out int width, out int height))
        {
            Debug.Log($"Width: {width}, Height: {height}");
        }
        else
        {
            Debug.Log("Failed to get image size");
        }
        float aspectRatio = (float)width / height;
        float newWidth = imageFixedWidth;
        float newHeight = (float)newWidth / aspectRatio;
        _image.rectTransform.sizeDelta = new Vector2(newWidth, newHeight);
    }



    private void MatchCollidersSizeToImage()
    {
        RectTransform imageRectTransform = (RectTransform)_image.transform;
        Vector3 newScale = new Vector3(imageRectTransform.rect.width * _imageToColliderScalar, imageRectTransform.rect.height * _imageToColliderScalar, _colliders.transform.localScale.z);
        _colliders.transform.localScale = newScale;
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


#endif
}

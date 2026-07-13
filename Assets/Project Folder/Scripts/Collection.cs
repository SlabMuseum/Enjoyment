
using Sirenix.OdinInspector;
using System.Collections;
using UnityEngine;
using UnityEngine.UI;

public class Collection : MonoBehaviour
{
    public float fadeDuration = 1.0f;

    private void Start()
    {

    }

    [Button("Fade In")]
    public void FadeIn()
    {
        TriggerFade(true);
    }

    public void FadeOut()
    {
        TriggerFade(false);
    }

    public void TriggerFade(bool fadeIn)
    {
        StartCoroutine(FadeAllChildren(fadeIn));
    }

    public void SetVisibilityImmediate(float alpha)
    {
        SetAlphaImmediate(alpha);
        SetColliderState(alpha > 0);
    }

    private void SetColliderState(bool enable)
    {
        Collider[] colliders = GetComponentsInChildren<Collider>(true);
        Collider2D[] colliders2D = GetComponentsInChildren<Collider2D>(true);

        foreach (Collider collider in colliders)
        {
            collider.enabled = enable;
        }

        foreach (Collider2D collider2D in colliders2D)
        {
            collider2D.enabled = enable;
        }
    }

    private IEnumerator FadeAllChildren(bool fadeIn)
    {
        Graphic[] graphics = GetComponentsInChildren<Graphic>();
        Renderer[] renderers = GetComponentsInChildren<Renderer>();
        float elapsedTime = 0f;

        float startAlpha = fadeIn ? 0f : 1f;
        float endAlpha = fadeIn ? 1f : 0f;

        // Set the initial collider state
        SetColliderState(fadeIn);

        // Set initial alpha
        SetAlphaImmediate(startAlpha);

        while (elapsedTime < fadeDuration)
        {
            elapsedTime += Time.deltaTime;
            float alpha = Mathf.Lerp(startAlpha, endAlpha, elapsedTime / fadeDuration);

            foreach (Graphic graphic in graphics)
            {
                SetAlpha(graphic, alpha);
            }

            foreach (Renderer renderer in renderers)
            {
                SetMaterialAlpha(renderer, alpha);
            }

            yield return null;
        }

        // Ensure final alpha is set correctly
        SetAlphaImmediate(endAlpha);

        // Finalize collider state
        SetColliderState(fadeIn);
    }

    private void SetAlpha(Graphic graphic, float alpha)
    {
        graphic.color = new Color(graphic.color.r, graphic.color.g, graphic.color.b, alpha);
    }

    private void SetMaterialAlpha(Renderer renderer, float alpha)
    {
        foreach (Material mat in renderer.materials)
        {
            if (mat.HasProperty("_Color"))
            {
                Color color = mat.color;
                color.a = alpha;
                mat.color = color;
            }
        }
    }

    private void SetAlphaImmediate(float alpha)
    {
        Graphic[] graphics = GetComponentsInChildren<Graphic>();
        Renderer[] renderers = GetComponentsInChildren<Renderer>();

        foreach (Graphic graphic in graphics)
        {
            SetAlpha(graphic, alpha);
        }

        foreach (Renderer renderer in renderers)
        {
            SetMaterialAlpha(renderer, alpha);
        }
    }


}

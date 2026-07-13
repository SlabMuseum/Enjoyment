using UnityEngine;

public class Glow : MonoBehaviour
{
    public float glowSpeed = 1.9f;
    public float minGlow = 0.1f; // Minimum alpha value
    public float maxGlow = 1.0f; // Maximum alpha value
    private float timeOffset;
    SpriteRenderer[] sprites;

    void Awake()
    {
        sprites = GetComponentsInChildren<SpriteRenderer>(true);
        glowSpeed = SceneReferencer.Instance.globalGlowSpeed;
        minGlow = SceneReferencer.Instance.globalMinGlow;
        maxGlow = SceneReferencer.Instance.globalMaxGlow;
    }

    private void OnEnable()
    {
        foreach (SpriteRenderer sprite in sprites)
        {
            sprite.gameObject.SetActive(true);
            // Set initial alpha to minGlow
            Color color = sprite.color;
            color.a = minGlow;
            sprite.color = color;
        }

        // Calculate the time offset to start the sine wave at the minimum value
        timeOffset = Time.time - Mathf.Asin(-1) / glowSpeed;
    }

    private void OnDisable()
    {
        foreach (SpriteRenderer sprite in sprites)
        {
            sprite.gameObject.SetActive(false);
        }
    }

    // Update is called once per frame
    void Update()
    {
        foreach (SpriteRenderer sprite in sprites)
        {
            Color color = sprite.color;
            float glow = Mathf.Sin((Time.time - timeOffset) * glowSpeed);
            // Transform the sine wave to fit between minGlow and maxGlow
            glow = Mathf.Lerp(minGlow, maxGlow, (glow + 1) / 2);
            color.a = glow;
            sprite.color = color;
        }
    }

    public void Activate()
    {
        gameObject.SetActive(true);
    }

    public void Deactivate()
    {
        gameObject.SetActive(false);
    }
}

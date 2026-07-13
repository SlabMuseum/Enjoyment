using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using DG.Tweening;
using Shapes;
using TMPro;

public class TextDisplayAnimator : MonoBehaviour
{
    private Tween _fadeTween;
    private Tween _scaleTween;

    private TextDisplayReferences _textDisplayReferences;

    [SerializeField] private float _fadeDuration = 0.5f;
    [SerializeField] private float _scaleChangeDuration = 0.5f;

    public void Init(TextDisplayReferences textDisplayReferences)
    {
        _textDisplayReferences = textDisplayReferences;
    }

    public void SetAppearance(bool state, bool useAnimation = true)
    {
        _fadeTween?.Kill();

        float targetAlpha = state ? 1f : 0f;

        if (!useAnimation)
        {
            _textDisplayReferences.TextUI.SetAlpha(targetAlpha);
            _textDisplayReferences.Background.SetAlpha(targetAlpha);
            return;
        }

        float currentAlpha = _textDisplayReferences.TextUI.color.a;
        _fadeTween = DOVirtual.Float(currentAlpha, targetAlpha, _fadeDuration, t =>
        {
            _textDisplayReferences.TextUI.SetAlpha(t);
            _textDisplayReferences.Background.SetAlpha(t);
        });
    }

    public void SetScale(Vector2 newTextScale, Vector2 newBackgroundScale)
    {
        _scaleTween?.Kill();

        Vector2 currentBackgroundScale = new(_textDisplayReferences.Background.Width, _textDisplayReferences.Background.Height);
        Vector2 currentTextScale = new(_textDisplayReferences.TextUI.rectTransform.sizeDelta.x,
            _textDisplayReferences.TextUI.rectTransform.sizeDelta.y);

        _scaleTween = DOVirtual.Float(0, 1, _scaleChangeDuration, t =>
        {
            float textXScale = Mathf.Lerp(currentTextScale.x, newTextScale.x, t);
            float textYScale = Mathf.Lerp(currentTextScale.y, newTextScale.y, t);
            _textDisplayReferences.TextUI.rectTransform.sizeDelta = new Vector2(textXScale, textYScale);

            _textDisplayReferences.Background.Width = Mathf.Lerp(currentBackgroundScale.x, newBackgroundScale.x, t);
            _textDisplayReferences.Background.Height = Mathf.Lerp(currentBackgroundScale.y, newBackgroundScale.y, t);
        });
    }
}
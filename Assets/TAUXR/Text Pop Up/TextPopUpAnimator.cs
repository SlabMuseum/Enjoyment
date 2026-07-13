using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using DG.Tweening;
using Shapes;
using TMPro;

public class TextPopUpAnimator : MonoBehaviour
{
    private Tween _fadeTween;
    private Tween _scaleTween;

    private TextPopUpReferences _textPopUpReferences;

    [SerializeField] private float _fadeDuration = 0.5f;
    [SerializeField] private float _scaleChangeDuration = 0.5f;

    public void Init(TextPopUpReferences textPopUpReferences)
    {
        _textPopUpReferences = textPopUpReferences;
    }

    public void SetAppearance(bool state, bool useAnimation = true)
    {
        _fadeTween?.Kill();

        float targetAlpha = state ? 1f : 0f;

        if (!useAnimation)
        {
            _textPopUpReferences.TextUI.SetAlpha(targetAlpha);
            _textPopUpReferences.Background.SetAlpha(targetAlpha);
            return;
        }

        float currentAlpha = _textPopUpReferences.TextUI.color.a;
        _fadeTween = DOVirtual.Float(currentAlpha, targetAlpha, _fadeDuration, t =>
        {
            _textPopUpReferences.TextUI.SetAlpha(t);
            _textPopUpReferences.Background.SetAlpha(t);
        });
    }

    public void SetScale(Vector2 newTextScale, Vector2 newBackgroundScale)
    {
        _scaleTween?.Kill();

        Vector2 currentBackgroundScale = new(_textPopUpReferences.Background.Width, _textPopUpReferences.Background.Height);
        Vector2 currentTextScale = new(_textPopUpReferences.TextUI.rectTransform.sizeDelta.x,
            _textPopUpReferences.TextUI.rectTransform.sizeDelta.y);

        _scaleTween = DOVirtual.Float(0, 1, _scaleChangeDuration, t =>
        {
            float textXScale = Mathf.Lerp(currentTextScale.x, newTextScale.x, t);
            float textYScale = Mathf.Lerp(currentTextScale.y, newTextScale.y, t);
            _textPopUpReferences.TextUI.rectTransform.sizeDelta = new Vector2(textXScale, textYScale);

            _textPopUpReferences.Background.Width = Mathf.Lerp(currentBackgroundScale.x, newBackgroundScale.x, t);
            _textPopUpReferences.Background.Height = Mathf.Lerp(currentBackgroundScale.y, newBackgroundScale.y, t);
        });
    }
}
using System;
using System.Collections;
using System.Collections.Generic;
using Shapes;
using UnityEngine;
using TMPro;

public class TextDisplayScaler : MonoBehaviour
{
    private const float DefaultTextFontSize = 0.34f;
    private const int ReferenceNumberOfLettersUntilLineWrap = 50;
    private const int ReferenceNumberOfLetters = 300;
    private const float ReferenceSquareMeters = 0.25f;
    private const float ReferenceLineHeight = 0.04f;

    private TextDisplayReferences _textDisplayReferences;

    [SerializeField] private float _fontSizeMultiplier = 1;
    [SerializeField] private Vector2 _backgroundPadding = new(0.3f, 0.1f);
    [SerializeField] private float _layoutRatio = 5.5f;
    [SerializeField] private float _scaleFactor = 1;
    [SerializeField] private bool _extendWidthOnly;
    [SerializeField] private bool _extendHeightOnly;
    [SerializeField] private bool _autoScaleWhenChangingTextInInspector = true;

    public bool AutoScaleWhenChangingTextInInspector => _autoScaleWhenChangingTextInInspector;

    [HideInInspector] public string Text;

    public void Init(TextDisplayReferences textDisplayReferences)
    {
        _textDisplayReferences = textDisplayReferences;
    }

    public void AutoScale(bool useAnimation = true)
    {
        _textDisplayReferences.TextUI.fontSize = DefaultTextFontSize * _fontSizeMultiplier;

        float xScale = Mathf.Sqrt(_layoutRatio * ReferenceSquareMeters);

        float heightAdditionFromExtraLineBreaks = GetNumberOfExtraLineBreaks() * ReferenceLineHeight;
        float yScale = Mathf.Sqrt(1 / _layoutRatio * ReferenceSquareMeters) + heightAdditionFromExtraLineBreaks;

        Vector2 scale = new Vector2(xScale, yScale) * _scaleFactor * _fontSizeMultiplier * GetNumberOfLettersScalingFactor();

        SetScale(scale, useAnimation);
    }

    public void SetScale(Vector2 textSize, bool useAnimation = true)
    {
        if (useAnimation)
        {
            _textDisplayReferences.TextDisplayAnimator.SetScale(textSize, textSize + _backgroundPadding);
            return;
        }

        _textDisplayReferences.TextUI.rectTransform.sizeDelta = textSize;
        _textDisplayReferences.Background.Width = textSize.x + _backgroundPadding.x;
        _textDisplayReferences.Background.Height = textSize.y + _backgroundPadding.y;
    }


    private Vector2 GetNumberOfLettersScalingFactor()
    {
        float squareMetersScalingFactor = (float)Text.Length / ReferenceNumberOfLetters;
        float newScaleX = 1;
        float newScaleY = 1;

        if (_extendWidthOnly)
        {
            newScaleX = squareMetersScalingFactor;
        }
        else if (_extendHeightOnly)
        {
            newScaleY = squareMetersScalingFactor;
        }
        else
        {
            newScaleX = Mathf.Sqrt(squareMetersScalingFactor);
            newScaleY = Mathf.Sqrt(squareMetersScalingFactor);
        }

        Vector2 newScale = new(newScaleX, newScaleY);

        return newScale;
    }

    private int GetNumberOfExtraLineBreaks()
    {
        return GetNumberOfLineBreaks() - GetNumberOfWrappingLineBreaksInText(Text);
    }

    private int GetNumberOfLineBreaks()
    {
        string[] paragraphs = Text.Split("\n");
        int manualLineBreaks = paragraphs.Length - 1;
        int wrappingLineBreaksInParagraph = 0;
        foreach (string paragraph in paragraphs)
        {
            wrappingLineBreaksInParagraph += GetNumberOfWrappingLineBreaksInText(paragraph);
        }

        return manualLineBreaks + wrappingLineBreaksInParagraph;
    }

    private int GetNumberOfWrappingLineBreaksInText(string text)
    {
        int numberOfLettersUntilLineWrap = (int)(ReferenceNumberOfLettersUntilLineWrap * (float)Text.Length / ReferenceNumberOfLetters);
        return text.Length / numberOfLettersUntilLineWrap;
    }

#if UNITY_EDITOR
    private void OnValidate()
    {
        if (Application.isPlaying)
        {
            return;
        }

        _textDisplayReferences = GetComponent<TextDisplayReferences>();
        if (AutoScaleWhenChangingTextInInspector)
        {
            AutoScale(false);
        }
    }
#endif
}
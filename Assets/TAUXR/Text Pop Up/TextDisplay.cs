using System;
using System.Collections;
using System.Collections.Generic;
using Cysharp.Threading.Tasks;
using NaughtyAttributes;
using Shapes;
using UnityEngine;
using UnityEditor;
using TMPro;

public class TextDisplay : MonoBehaviour
{
    public TextDataScriptableObject TextsData => _textsData;

    [SerializeField] private TextDisplayReferences _textDisplayReferences;
    [SerializeField] private ETextDisplayState _startingState;
    [TextArea(1, 10)] [SerializeField] private string _text;
    [SerializeField] private Vector2 _textAreaSize;
    [SerializeField] private string _textId;
    [SerializeField] private Vector2 _backgroundPadding = new(0.3f, 0.1f);
    [Expandable] [SerializeField] private TextDataScriptableObject _textsData;

    private void Awake()
    {
        _textDisplayReferences.TextDisplayAnimator.Init(_textDisplayReferences);
    }

    private void Start()
    {
        SetScale(_textAreaSize, false);
        SetText(_text);
        SetStartingState();
    }

    private void SetStartingState()
    {
        switch (_startingState)
        {
            case ETextDisplayState.Active:
                _textDisplayReferences.TextDisplayAnimator.SetAppearance(true, false);
                break;
            case ETextDisplayState.Appear:
                _textDisplayReferences.TextDisplayAnimator.SetAppearance(false, false);
                _textDisplayReferences.TextDisplayAnimator.SetAppearance(true);
                break;
            case ETextDisplayState.Hidden:
                _textDisplayReferences.TextDisplayAnimator.SetAppearance(false, false);
                break;
        }
    }

    public void Show(bool useAnimation = true)
    {
        _textDisplayReferences.TextDisplayAnimator.SetAppearance(true, useAnimation);
    }

    public void Hide(bool useAnimation = true)
    {
        _textDisplayReferences.TextDisplayAnimator.SetAppearance(false, useAnimation);
    }

    public void SetText(string newText)
    {
        _textDisplayReferences.TextUI.text = newText;
    }

    public void SetScale(Vector2 textAreaSize, bool useAnimation = true)
    {
        if (useAnimation)
        {
            _textDisplayReferences.TextDisplayAnimator.SetScale(textAreaSize, textAreaSize + _backgroundPadding);
            return;
        }

        _textDisplayReferences.TextUI.rectTransform.sizeDelta = textAreaSize;
        _textDisplayReferences.Background.Width = textAreaSize.x + _backgroundPadding.x;
        _textDisplayReferences.Background.Height = textAreaSize.y + _backgroundPadding.y;
    }

    public void SetTextFromConfiguration(string textId, bool useAnimation = true)
    {
        TextData textConfiguration = _textsData.GetTextConfiguration(textId);
        if (textConfiguration == null)
        {
            Debug.LogWarning("Text id: " + textId + " not found, did not set text");
            return;
        }

        SetText(textConfiguration.Text);
        SetScale(textConfiguration.TextAreaSize, useAnimation);
    }

    public void SetLanguageToEnglish()
    {
        _textDisplayReferences.TextUI.isRightToLeftText = false;
        _textDisplayReferences.TextUI.alignment = TextAlignmentOptions.Left;
    }

    public void SetLanguageToHebrew()
    {
        _textDisplayReferences.TextUI.isRightToLeftText = true;
        _textDisplayReferences.TextUI.alignment = TextAlignmentOptions.Right;
    }
#if UNITY_EDITOR
    public void SetVisibilityState(bool newState)
    {
        _textDisplayReferences.TextDisplayAnimator.Init(_textDisplayReferences);
        _textDisplayReferences.TextDisplayAnimator.SetAppearance(newState, Application.isPlaying);
    }

    public void SaveTextData(string textId)
    {
        TextData textData = new(textId, _text, _textAreaSize);
        _textsData.AddOrReplace(textData);
    }

    public void SetPropertiesByTextData(string textId)
    {
        TextData textData = _textsData.GetTextConfiguration(textId);
        if (textData == null) return;
        _textId = textId;
        _text = textData.Text;
        _textAreaSize = textData.TextAreaSize;
        EditorUtility.SetDirty(this);
    }

#endif
}
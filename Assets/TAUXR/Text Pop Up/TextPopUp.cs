using TMPro;
using UnityEngine;

public class TextPopUp : MonoBehaviour
{
    [SerializeField] private TextPopUpReferences _textPopUpReferences;
    [SerializeField] private ETextPopUpState _startingState;
    [TextArea(1, 10)][SerializeField] private string _text;

    [SerializeField] private TextPopUpTextsConfigurationsScriptableObject _textConfigurations;

    private void Awake()
    {
        _textPopUpReferences.TextPopUpScaler.Init(_textPopUpReferences);
        _textPopUpReferences.TextPopUpAnimator.Init(_textPopUpReferences);
    }

    private void Start()
    {
        SetStartingState();
    }

    private void SetStartingState()
    {
        switch (_startingState)
        {
            case ETextPopUpState.Active:
                _textPopUpReferences.TextPopUpAnimator.SetAppearance(true, false);
                break;
            case ETextPopUpState.Appear:
                _textPopUpReferences.TextPopUpAnimator.SetAppearance(false, false);
                _textPopUpReferences.TextPopUpAnimator.SetAppearance(true);
                break;
            case ETextPopUpState.Disabled:
                _textPopUpReferences.TextPopUpAnimator.SetAppearance(false, false);
                break;
        }
    }

    public void Show(bool useAnimation = true)
    {
        _textPopUpReferences.TextPopUpAnimator.SetAppearance(true, useAnimation);
    }

    public void Hide(bool useAnimation = true)
    {
        _textPopUpReferences.TextPopUpAnimator.SetAppearance(false, useAnimation);
    }

    public void SetText(string newText)
    {
        _textPopUpReferences.TextUI.text = newText;
    }

    public void SetTextAndAutoScale(string newText, bool useAnimation = true)
    {
        _textPopUpReferences.TextUI.text = newText;
        _textPopUpReferences.TextPopUpScaler.Text = newText;
        _textPopUpReferences.TextPopUpScaler.AutoScale(useAnimation);
    }

    public void SetTextAndScale(string newText, Vector2 textSize, bool useAnimation = true)
    {
        _textPopUpReferences.TextUI.text = newText;
        _textPopUpReferences.TextPopUpScaler.Text = newText;
        _textPopUpReferences.TextPopUpScaler.SetScale(textSize, useAnimation);
    }

    public void SetTextFromConfiguration(string textId, bool useAnimation = true)
    {
        TextPopUpTextConfiguration textConfiguration = _textConfigurations.GetTextConfiguration(textId);
        if (textConfiguration == null)
        {
            return;
        }

        SetTextAndScale(textConfiguration.Text, textConfiguration.TextRectSize, useAnimation);
    }

    public void SetLanguageToEnglish()
    {
        _textPopUpReferences.TextUI.isRightToLeftText = false;
        _textPopUpReferences.TextUI.alignment = TextAlignmentOptions.Left;
    }

    public void SetLanguageToHebrew()
    {
        _textPopUpReferences.TextUI.isRightToLeftText = true;
        _textPopUpReferences.TextUI.alignment = TextAlignmentOptions.Right;
    }

    public string GetText()
    {
        return _textPopUpReferences.TextUI.text;
    }
#if UNITY_EDITOR
    public void GetTextFromComponent()
    {
        _text = _textPopUpReferences.TextUI.text;
    }

    public void SetTextAndAutoScale()
    {
        _textPopUpReferences.TextPopUpScaler.Init(_textPopUpReferences);
        _textPopUpReferences.TextPopUpAnimator.Init(_textPopUpReferences);
        SetTextAndAutoScale(_text, false);
    }

    public void SetTextAndScale(Vector2 textSize)
    {
        _textPopUpReferences.TextPopUpScaler.Init(_textPopUpReferences);
        _textPopUpReferences.TextPopUpAnimator.Init(_textPopUpReferences);
        SetTextAndScale(_text, textSize, false);
    }

    public void SetActiveState(bool newState)
    {
        _textPopUpReferences.TextPopUpAnimator.Init(_textPopUpReferences);
        _textPopUpReferences.TextPopUpAnimator.SetAppearance(newState, false);
    }


#endif
}
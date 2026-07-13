using UnityEngine;
using DG.Tweening;
using TMPro;

public class TXRButtonVisuals : MonoBehaviour
{
    protected TXRButtonState _state;
    protected Shapes.Rectangle _backface;
    protected Shapes.Rectangle _stroke;
    protected TextMeshPro _text;
    protected ButtonVisualsConfigurations _configurations;
    protected TXRButtonReferences _references;

    protected Sequence _backfaceColorSequence;
    protected Sequence _backfaceGradientSequence;
    protected Sequence _backfaceZValueSequence;
    protected Sequence _strokeThicknessSequence;
    protected Sequence _textOpacitySequence;

    protected float _strokeExtraSize = 0.005f;  // the amount of which stroke is bigger than backface

    protected Color _activeColor;
    protected Color _pressedColor;
    protected Color _disabledColor;
    protected Color _hoverColor;

    public virtual void Init(TXRButtonReferences references)
    {
        _backface = references.Backface;
        _stroke = references.Stroke;
        _text = references.Text;
        _configurations = references.Configurations;
        _references = references;
        UpdateColorsFromReferences();
    }

    public void SetState(TXRButtonState state)
    {
        print("SET STATE: " + state);
        switch (state)
        {
            case TXRButtonState.Active:
                Active();
                break;
            case TXRButtonState.Pressed:
                Press();
                break;
            case TXRButtonState.Hidden:
                Hide();
                break;
            case TXRButtonState.Disabled:
                Disabled();
                break;
            case TXRButtonState.Hover:
                Hover();
                break;
        }

        _state = state;
    }

    public void UpdateColorsFromReferences()
    {
        _activeColor = _references.ActiveColor;
        _pressedColor = _references.PressedColor;
        _disabledColor = _references.DisabledColor;
        _hoverColor = _references.HoverGradientColor;
    }

    protected virtual void Active()
    {
        SetBackfaceColor(_activeColor, _configurations.activeDuration);
        SetBackfaceZ(_configurations.backfaceZPositionActive);
        SetHoverGradient(false);
        SetStrokeThickness(_configurations.strokeThicknessActive);
        SetTextOpacity(1);
    }

    protected virtual void Hide()
    {
        Color backFaceHideColor = _backface.FillColorEnd;
        backFaceHideColor.a = 0;
        SetBackfaceColor(backFaceHideColor, _configurations.hideDuration);
        SetHoverGradient(false);
        SetStrokeThickness(0);
        SetTextOpacity(0);
    }

    protected virtual void Hover()
    {
       // SetBackfaceColor(_activeColor, _configurations.activeDuration);
        SetHoverGradient(true);
        SetBackfaceZ(_configurations.backfadeZPositionHover);
        SetStrokeThickness(_configurations.strokeThicknessHover);
        SetTextOpacity(1);
    }

    protected virtual void Press()
    {
        SetBackfaceZ(_configurations.backfadeZPositionPress);
        SetHoverGradient(true);
        SetBackfaceColor(_pressedColor);
        SetStrokeThickness(_configurations.strokeThicknessPress);
        SetTextOpacity(1);
    }

    protected virtual void Disabled()
    {
        SetHoverGradient(false);
        SetBackfaceZ(_configurations.backfaceZPositionActive);
        SetBackfaceColor(_disabledColor);
        SetStrokeThickness(_configurations.strokeThicknessDisabled);
        SetTextOpacity(_configurations.textOpacityDisabled);
    }

    public void SetBackfaceColor(TXRButtonState state, Color color, float duration = 0.25f)
    {
        switch (state)
        {
            case TXRButtonState.Active:
                _activeColor = color;
                break;
            case TXRButtonState.Pressed:
                _pressedColor = color;
                break;
            case TXRButtonState.Disabled:
                _disabledColor = color;
                break;
        }

        // update color change if changed the color of current state
        if (_state == state)
        {
            SetState(state);
        }
    }

    public Color GetColor(TXRButtonState state)
    {
        switch (state)
        {
            case TXRButtonState.Active:
                return _activeColor;
            case TXRButtonState.Pressed:
                return _pressedColor;
            case TXRButtonState.Disabled:
                return _disabledColor;
        }

        Debug.LogError("No color defined for state: " + state + ", Returning solid black");
        return Color.black;
    }

    protected virtual void SetHoverGradient(bool isOn, float duration = 0.25f)
    {
        float gradientRadius = isOn ? _configurations.backfaceGradientRadiusHover : 0;

        _backfaceGradientSequence.Kill();

        _backfaceGradientSequence = DOTween.Sequence();
        _backfaceGradientSequence.Append(DOVirtual.Float(_backface.FillRadialRadius, gradientRadius, duration,
            t => { _backface.FillRadialRadius = t; }));
        _backfaceGradientSequence.Join(DOVirtual.Color(_backface.FillColorStart, _hoverColor, duration,
            t => { _backface.FillColorStart = t; }));
    }

    protected virtual void SetBackfaceZ(float zValue, float duration = 0.25f)
    {
        Vector3 backfaceLocalPosition = _backface.transform.localPosition;
        backfaceLocalPosition.z = zValue;

        _backfaceZValueSequence.Kill();
        _backfaceZValueSequence = DOTween.Sequence();
        _backfaceZValueSequence.Append(_backface.transform.DOLocalMove(backfaceLocalPosition, duration));
    }

    protected virtual void SetStrokeThickness(float thickness, float duration = 0.25f)
    {
        _strokeThicknessSequence.Kill();
        _strokeThicknessSequence = DOTween.Sequence();
        _strokeThicknessSequence.Append(DOVirtual.Float(_stroke.Thickness, thickness, duration, t => { _stroke.Thickness = t; }));
    }

    protected virtual void SetBackfaceColor(Color backfaceColor, float duration = 0.25f)
    {
        _backfaceColorSequence.Kill();
        _backfaceColorSequence = DOTween.Sequence();
        _backfaceColorSequence.Append(
            DOVirtual.Color(_backface.FillColorEnd, backfaceColor, duration, t => { _backface.FillColorEnd = t; }));
    }

    protected virtual void SetTextOpacity(float targetOpacity, float duration = 0.25f)
    {
        Color targetColor = _text.color;
        targetColor.a = targetOpacity;
        _textOpacitySequence.Kill();
        _textOpacitySequence = DOTween.Sequence();
        _textOpacitySequence.Append(
            DOVirtual.Color(_text.color, targetColor, duration, t => { _text.color = t; }));
    }
}
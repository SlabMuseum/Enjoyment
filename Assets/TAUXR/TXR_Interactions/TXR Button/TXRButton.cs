using NaughtyAttributes;
using System;
using System.Threading.Tasks;
using UnityEngine;
using UnityEngine.Events;

public class TXRButton : MonoBehaviour
{
    public TXRButtonState State => _state;
    public bool ShouldPlaySounds = true;
    public bool IsInteractable => _isInteractable;

    private bool _isInteractable = true;
    [SerializeField] private TXRButtonState _state = TXRButtonState.Active;

    public UnityEvent Pressed;
    public UnityEvent Released;
    public UnityEvent HoverEnter;
    public UnityEvent HoverExit;

    [SerializeField] protected ButtonColliderResponse ResponseHoverEnter;
    [SerializeField] protected ButtonColliderResponse ResponseHoverExit;
    [SerializeField] protected ButtonColliderResponse ResponsePress;
    [SerializeField] protected ButtonColliderResponse ResponseRelease;

    protected TXRButtonInput _input;
    protected TXRButtonVisuals _visuals;

    public Action<Transform> PressTransform;
    public TXRButtonReferences References;

    public Transform ActiveToucher => _input.MainToucher;

    protected virtual void Awake()
    {
        Init();
    }

    protected virtual void Init()
    {
        //References.ActiveColor = References.Backface.FillColorEnd;
        _visuals = References.ButtonVisuals;
        _visuals.Init(References);

        _input = References.ButtonInput;
        _input.Init(References);
        SetState(_state);
    }

    [Button]
    public void SetState()
    {
        SetState(_state);
    }

    public void SetState(TXRButtonState state)
    {
        _visuals.SetState(state);
        _state = state;
    }
    public void SetInteractable(bool isInteractable)
    {
        _isInteractable = isInteractable;
    }

    public void SetColor(TXRButtonState state, Color color, float duration = 0.25f)
    {
        _visuals.SetBackfaceColor(state, color, duration);
    }

    public Color GetColor(TXRButtonState state)
    {
        return _visuals.GetColor(state);
    }

    protected void PlaySound(AudioSource sound)
    {
        if (sound == null || !ShouldPlaySounds) return;
        sound.Stop();
        sound.Play();
    }

    // used for external scripts that want to manipulate buttons regardless of touchers.
    public virtual void TriggerButtonEventFromCode(ButtonEvent buttonEvent, ButtonColliderResponse response)
    {
        switch (buttonEvent)
        {
            case ButtonEvent.HoverEnter:
                DelegateInteralExtenralResponses(response, OnHoverEnterInternal, HoverEnter);
                break;

            case ButtonEvent.HoverExit:
                DelegateInteralExtenralResponses(response, OnHoverExitInternal, HoverExit);
                break;

            case ButtonEvent.Pressed:
                DelegateInteralExtenralResponses(response, OnPressedInternal, Pressed);
                break;

            case ButtonEvent.Released:
                DelegateInteralExtenralResponses(response, OnReleasedInternal, Released);
                break;
        }
    }

    // called from input manager
    public virtual void TriggerButtonEventFromInput(ButtonEvent buttonEvent)
    {
        if (!_isInteractable) return;

        switch (buttonEvent)
        {
            case ButtonEvent.HoverEnter:
                DelegateInteralExtenralResponses(ResponseHoverEnter, OnHoverEnterInternal, HoverEnter);
                break;

            case ButtonEvent.HoverExit:
                DelegateInteralExtenralResponses(ResponseHoverExit, OnHoverExitInternal, HoverExit);
                break;

            case ButtonEvent.Pressed:
                DelegateInteralExtenralResponses(ResponsePress, OnPressedInternal, Pressed);
                break;

            case ButtonEvent.Released:
                DelegateInteralExtenralResponses(ResponseRelease, OnReleasedInternal, Released);
                break;
        }
    }

    protected void DelegateInteralExtenralResponses(ButtonColliderResponse response, Action internalAction, UnityEvent externalEvent)
    {
        switch (response)
        {
            case ButtonColliderResponse.None:
                break;
            case ButtonColliderResponse.Both:
                internalAction();
                externalEvent.Invoke();
                break;
            case ButtonColliderResponse.Internal:
                internalAction();
                break;
            case ButtonColliderResponse.External:
                externalEvent.Invoke();
                break;
        }
    }

    protected virtual void OnHoverEnterInternal()
    {
        _visuals.SetBackfaceColor(TXRButtonState.Hover, References.ActiveColor);
        _visuals.SetState(TXRButtonState.Hover);
    }

    protected virtual void OnHoverExitInternal()
    {
        _visuals.SetState(TXRButtonState.Active);
    }



    protected virtual void OnReleasedInternal()
    {
        PlaySound(References.SoundRelease);
        _visuals.SetState(TXRButtonState.Active);
    }

    #region Noa's editions

    public void SetText(String text)
    {
        References.Text.text = text;
    }

    private TaskCompletionSource<bool> _buttonPressedTcs;
    public Task WaitForButtonPress()
    {
        _buttonPressedTcs = new TaskCompletionSource<bool>();
        return _buttonPressedTcs.Task;
    }

    protected virtual void OnPressedInternal()
    {
        PlaySound(References.SoundPress);
        _visuals.SetState(TXRButtonState.Pressed);
        // Complete the task after button pressed
        if (_buttonPressedTcs != null && !_buttonPressedTcs.Task.IsCompleted)
        {
            _buttonPressedTcs.SetResult(true);
        }
    }


    #endregion



}

public enum ButtonColliderResponse
{
    Both,
    Internal,
    External,
    None
}

public enum ButtonEvent
{
    HoverEnter,
    Pressed,
    Released,
    HoverExit
}

public enum TXRButtonState
{
    Hidden,
    Active,
    Hover,
    Pressed,
    Disabled,
}
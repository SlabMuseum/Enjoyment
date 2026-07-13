using System.Linq;
using System.Collections.Generic;
using UnityEngine;
using System;

public enum ButtonInputState
{
    Idle,
    Hover,
    Press,
    Release
}

public class TXRButtonInput : MonoBehaviour
{
    public ButtonInputState State;
    public Transform MainToucher => _mainToucher;

    private TXRButtonReferences _references;
    private TXRButton _btn;

    private Transform _buttonSurface;
    private List<Transform> _touchers = new List<Transform>();
    private Transform _mainToucher;
    private const float PRESS_DISTANCE = .005f;

    public void Init(TXRButtonReferences references)
    {
        _references = references;
        _btn = references.ButtonBehavior;
        _buttonSurface = references.ButtonSurface;
        State = ButtonInputState.Idle;
    }

    private void OnTriggerEnter(Collider other)
    {
        if (!other.CompareTag("Toucher")) return;

        _touchers.Add(other.transform);

        if (_touchers.Count == 1)
            _mainToucher = _touchers[0];
    }

    private void Update()
    {
        if (_mainToucher == null) // no toucher around
        {
            ClearStateBackToIdle();
            return;
        }

        Vector3 closestPointOnBtn = GetClosestPointOnSurface(_mainToucher.position, _buttonSurface, _references.Backface.Width,
            _references.Backface.Height);

        Vector3 toucherToBtn = _mainToucher.transform.position - closestPointOnBtn;
        float toucherDistance = toucherToBtn.magnitude;
        bool isToucherInFrontOfButton = Vector3.Dot(toucherToBtn.normalized, _references.ButtonSurface.forward) > 0;
        bool isToucherPressing = toucherDistance < PRESS_DISTANCE;

        if (isToucherPressing)
        {
            if (State == ButtonInputState.Hover) // Press
            {
                State = ButtonInputState.Press;
                _btn.PressTransform?.Invoke(_mainToucher);
        
                _btn.TriggerButtonEventFromInput(ButtonEvent.Pressed);
            }
        }
        else
        {
            if (State == ButtonInputState.Press) // Release
            {
                if (!isToucherInFrontOfButton) return; // prevent press release when pressing the btn too "deep"

                _btn.TriggerButtonEventFromInput(ButtonEvent.Released);
                State = ButtonInputState.Release;
            }
            else if (State == ButtonInputState.Release || State == ButtonInputState.Idle) // Hover Enter
            {
                if (!isToucherInFrontOfButton) return; // prevent button activation from behind

                _btn.TriggerButtonEventFromInput(ButtonEvent.HoverEnter);
                State = ButtonInputState.Hover;
            }
        }
    }

    private void ClearStateBackToIdle()
    {
        if (State == ButtonInputState.Hover) // Hover Exit
        {
            _btn.TriggerButtonEventFromInput(ButtonEvent.HoverExit);
            State = ButtonInputState.Idle;
        }

        if (State == ButtonInputState.Press) // Exit collider from deep pressing all the way
        {
            _btn.TriggerButtonEventFromInput(ButtonEvent.Released);
            State = ButtonInputState.Idle;
        }
    }

    private void OnTriggerExit(Collider other)
    {
        if (!other.CompareTag("Toucher")) return;
        _touchers.Remove(other.transform);

        if (_touchers.Count > 0)
        {
            _mainToucher = _touchers.Last();
        }
        else
        {
            _mainToucher = null;
        }
    }

    private Vector3 GetClosestPointOnSurface(Vector3 target, Transform pivot, float width, float height)
    {
        Vector3 localSpaceTargetPosition = pivot.InverseTransformPoint(target);

        float closestX = Mathf.Clamp(localSpaceTargetPosition.x, -width / 2f, width / 2f);
        float closestY = Mathf.Clamp(localSpaceTargetPosition.y, -height / 2f, height / 2f);
        float closestZ = 0;

        Vector3 localClosestPoint = new Vector3(closestX, closestY, closestZ);
        return pivot.TransformPoint(localClosestPoint);
    }
}
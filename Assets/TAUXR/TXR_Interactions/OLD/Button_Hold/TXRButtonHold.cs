using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Events;

public class TXRButtonHold : MonoBehaviour
{
    [SerializeField] private ToucherDetector _touchDetector;
    [SerializeField] private float holdDuration = 1.5f;

    public UnityEvent ButtonActivated;

    private float holdTime = 0;
    private bool _isActive = true;
    private List<Transform> _activeTouchers;
    private bool _isHandInButton = false;
    void Start()
    {
        _activeTouchers = new List<Transform>();
        _touchDetector.ToucherEnter.AddListener(OnHandEnterButton);
        _touchDetector.ToucherExited.AddListener(OnHandLeavesButton);
    }

    void Update()
    {
        if (_isActive)
        {
            UpdateHoldingTimeIfTouched();
        }
    }

    private void UpdateHoldingTimeIfTouched()
    {
        if (_isHandInButton)
        {
            holdTime += Time.deltaTime;
            if (holdTime >= holdDuration)
            {
                ButtonActivated.Invoke();
                _isActive= false;
                return;
            }
        }
    }

    private void OnHandEnterButton(Transform toucher)
    {
        _isHandInButton = true;
        _activeTouchers.Add(toucher);
    }

    private void OnHandLeavesButton(Transform toucher)
    {
        _activeTouchers.Remove(toucher);

        // ignore a hand going out of button if the other is still there
        if (_activeTouchers.Count == 0)
        {
            _isHandInButton = false;
        }
        else
        {
            return;
        }


    }
}

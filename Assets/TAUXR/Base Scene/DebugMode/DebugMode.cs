using System.Collections;
using System.Collections.Generic;
using Cysharp.Threading.Tasks;
using UnityEngine;

public class DebugMode : MonoBehaviour
{
    private PinchingInputManager pinchingInputManager;

    private bool _waitingForPinchingInputsInARow;
    [SerializeField] private bool _inDebugMode;
    [SerializeField] private int _numberOfPinchesToEnterDebugMode = 3;
    [SerializeField] private bool _debugEyeData = true;
    [SerializeField] private EyeDataDebugger _eyeDataDebugger;

    private bool _wasInDebugMode;


    private void Start()
    {
        if (_debugEyeData)
        {
            _eyeDataDebugger.gameObject.SetActive(true);
        }

        pinchingInputManager = TXRPlayer.Instance.PinchingInputManager;
    }

    // Update is called once per frame
    private void Update()
    {
        HandleDebugModeState();

        bool leftDebugMode = _wasInDebugMode && !_inDebugMode;
        if (leftDebugMode)
        {
            _eyeDataDebugger.RevertChanges();
            _wasInDebugMode = false;
        }

        if (!_inDebugMode)
        {
            return;
        }

        if (_debugEyeData)
        {
            _eyeDataDebugger.DebugEyeData();
        }
    }

    private void HandleDebugModeState()
    {
        if (!pinchingInputManager.IsInputPressedThisFrame(HandType.Any) || _waitingForPinchingInputsInARow) return;

        _waitingForPinchingInputsInARow = true;
        HandType nextHand = pinchingInputManager.IsLeftHeld() ? HandType.Right : HandType.Left;
        pinchingInputManager.WaitForPressesInARow(_numberOfPinchesToEnterDebugMode, 1, ToggleDebugModeState,
            () => _waitingForPinchingInputsInARow = false, true, nextHand).Forget();
    }

    private void ToggleDebugModeState()
    {
        _waitingForPinchingInputsInARow = false;
        _wasInDebugMode = _inDebugMode;
        _inDebugMode = !_inDebugMode;

        string consoleMessage = _inDebugMode ? "Debug mode activated" : "Debug mode disabled";
        Debug.Log(consoleMessage);
    }
}
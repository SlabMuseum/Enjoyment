using Cysharp.Threading.Tasks;
using System;
using TMPro;
using UnityEngine;

public class ArtPieceProximityDetector : MonoBehaviour
{

    Piece _piece;
    bool _isActive = false;
    bool _isPlayerInsideCollider = false;
    bool _waitingForGaze = false;
    bool _waitingForExit = false;
    public TextMeshPro _debugText;
    private void Awake()
    {
        _piece = GetComponentInParent<Piece>();
        _debugText = SceneReferencer.Instance.debugText;
        _debugText.text = "waiting for detection";
    }

    private void OnTriggerEnter(Collider other)
    {
        if (_isActive)
        {
            if (other.CompareTag("PlayerHead"))
            {
                _isPlayerInsideCollider = true;
                _waitingForGaze = true;
                ShowDebugText("Player in collider, waiting for gaze", Color.black).Forget();
            }

        }
    }

    private void OnTriggerStay(Collider other)
    {
        if (_isActive)
        {
            if (_isPlayerInsideCollider && _waitingForGaze)
            {
                if (TXRPlayer.Instance.FocusedObject == _piece.imageCollider.transform)
                {
                    if (other.CompareTag("PlayerHead"))
                    {
                        TXRDataManager.Instance.LogLineToFile("Player entered the zone of " + _piece.gameObject.name + ", zone radius in cm: " + transform.localScale.x);
                        Debug.Log("Player entered the zone of " + _piece.gameObject.name + ", zone radius in cm: " + transform.localScale.x);
                        _isPlayerInsideCollider = true;
                        _waitingForGaze = false;
                        _waitingForExit = true;
                        ShowDebugText("Player entered the zone of " + _piece.gameObject.name, Color.green).Forget();
                    }
                }
            }
        }
    }


    private void OnTriggerExit(Collider other)
    {
        if (_isPlayerInsideCollider && _waitingForExit)
        {
            if (other.CompareTag("PlayerHead"))
            {
                TXRDataManager.Instance.LogLineToFile("Player exited the zone of " + _piece.gameObject.name + ", zone radius in cm: " + transform.localScale.x);
                Debug.Log("Player exited the zone of " + _piece.gameObject.name + ", zone radius in cm: " + transform.localScale.x);
                _isPlayerInsideCollider = false;
                _waitingForExit = false;
                ShowDebugText("Player exited the zone of " + _piece.gameObject.name, Color.red).Forget();
            }
        }
    }

    public void Activate()
    {
        _isActive = true;
    }
    public void Deactivate()
    {
        _isActive = false;
    }

    async UniTask ShowDebugText(string text, Color color)
    {
        if (_debugText != null)
        {
            _debugText.text = text;
            _debugText.color = color;
            await UniTask.Delay(TimeSpan.FromSeconds(3));
        }


        _debugText.text = "";
    }
}



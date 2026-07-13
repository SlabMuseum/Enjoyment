using Cysharp.Threading.Tasks;
using System;
using System.Buffers;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

public enum HandType { Left, Right, None, Any }
public enum FingerType { Thumb = 19, Index = 20, Middle = 21, Ring = 22, Pinky = 23 }

public class TXRHand : MonoBehaviour
{
	public HandType HandType;

	private bool _isActive = true;

	private OVRSkeleton _ovrSkeleton;
	private List<HandCollider> _handColliders;

	private Pincher _pincher;
	
	private PinchManager _pinchManager;
	public Pincher Pincher => _pincher;
	public PinchManager PinchManager => _pinchManager;
	[SerializeField] private PinchingConfiguration _pinchingConfiguration;

	public void Init()
	{
		_ovrSkeleton = GetComponentInChildren<OVRSkeleton>();
		_pincher = GetComponentInChildren<Pincher>();

		_handColliders = GetComponentsInChildren<HandCollider>().ToList();
		foreach (HandCollider hc in _handColliders)
		{
			hc.Init(_ovrSkeleton);
		}

		_pinchManager = new PinchManager(this, _pinchingConfiguration);
		_pincher.Init(_ovrSkeleton, _pinchManager);
	}

	public void UpdateHand()
	{
		if (!_isActive || !_ovrSkeleton.IsDataHighConfidence) return;

		foreach (HandCollider hc in _handColliders)
		{
			hc.UpdateHandCollider();
		}
			
		_pinchManager.HandlePinching();
	}
	
	public Transform GetFingerCollider(FingerType fingerType)
	{
		foreach (HandCollider hc in _handColliders)
		{
			if (hc.fingerIndex == (int)fingerType)
			{
				return hc.transform;
			}
		}

		return null;
	}

	public void SetHandVisibility(bool state)
	{
		//  _isActive = state;
		_ovrSkeleton.gameObject.SetActive(state);

		// if hand is disabled then enable invisible collider
		//_invisibleHandCollider.SetActive(!state);
	}
}


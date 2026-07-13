using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using System;

public class PinchManager
{
	public Action<PinchManager> PinchEnter, PinchExit;
	private readonly List<APinchable> _pinchablesInRange = new();
	[HideInInspector] public APinchable PinchedObject;

	private bool _isPinching = false;
	private bool _wasPinchingLastFrame = false;
	private bool _pinchOccuredThisFrame => !_wasPinchingLastFrame && _isPinching;

	private float _timeSinceLastPinch;

	public PinchingConfiguration Configuration => _configuration;
	private PinchingConfiguration _configuration;
	public Pincher Pincher => _pincher;
	private readonly Pincher _pincher;
	public HandType HandType => _handType;
	private readonly HandType _handType;

	public PinchManager(TXRHand hand, PinchingConfiguration pinchingConfiguration)
	{
		_handType = hand.HandType;
		_pincher = hand.Pincher;
		_configuration = pinchingConfiguration;
		_timeSinceLastPinch = _configuration.MinimumTimeBetweenPinches;
	}

	public void HandlePinching()
	{
		//Prevent double pinching
		if (_timeSinceLastPinch < _configuration.MinimumTimeBetweenPinches)
		{
			_timeSinceLastPinch += Time.deltaTime;
		}

		_pincher.UpdatePincher();

		HandlePinchEvents();

		foreach (APinchable pinchable in _pinchablesInRange)
		{
			pinchable.OnHoverStay(this);
		}

		if (_pinchOccuredThisFrame && PinchedObject == null)
		{
			APinchable objectToPinch = ChooseObjectToPinch();

			if (objectToPinch != null)
			{
				PinchObject(objectToPinch);
			}
		}

		if (PinchedObject != null && _pincher.Strength <= PinchedObject.PinchExitThreshold)
		{
			PinchedObject.OnPinchExit();
		}	
	}
	
	private void HandlePinchEvents()
	{
		_wasPinchingLastFrame = _isPinching;
		if (!_isPinching)
		{
			bool nextPinchReady = _timeSinceLastPinch >= _configuration.MinimumTimeBetweenPinches;
			if (_pincher.Strength > _configuration.PinchEnterThreshold && nextPinchReady)
			{
				_timeSinceLastPinch = 0;
				_isPinching = true;
				PinchEnter?.Invoke(this);
			}
		}
		else
		{
			if (_pincher.Strength < _configuration.PinchExitThreshold)
			{
				_isPinching = false;
				PinchExit?.Invoke(this);
			}
		}
	}

	public APinchable ChooseObjectToPinch()
	{
		foreach (APinchable pinchable in _pinchablesInRange)
		{
			if (pinchable.CanBePinched(this))
			{
				return pinchable;
			}
		}

		return null;
	}

	public APinchable ChooseInteractablePinchable()
	{
		foreach (APinchable pinchable in _pinchablesInRange)
		{
			if (pinchable.ShouldEffectBeActiveOnHover(this) && pinchable.IsUsedByPinchMeIndicator)
			{
				return pinchable;
			}
		}

		return null;
	}

	private void PinchObject(APinchable objectToPinch)
	{
		objectToPinch.OnPinchEnter(this);
	}

	public void AddPinchableInRange(APinchable pinchable)
	{
		_pinchablesInRange.Add(pinchable);

		//If sort becomes expensive, do it in a more optimized way (priority queue?)
		_pinchablesInRange.Sort();
	}

	public void RemovePinchableInRange(APinchable pinchable)
	{
		_pinchablesInRange.Remove(pinchable);
	}

	//Called from pinchables, that want to know if a certain other pinchable is in range.
	public APinchable FindPinchableByType(Type pinchableType)
	{
		foreach (APinchable pinchable in _pinchablesInRange)
		{
			if (pinchable.GetType() == pinchableType)
			{
				return pinchable;
			}
		}

		return null;
	}

	public bool IsPlayerPinchingThisFrame()
	{
		return _isPinching;
	}
}

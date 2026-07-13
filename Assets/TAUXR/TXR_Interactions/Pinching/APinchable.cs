using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

public abstract class APinchable : MonoBehaviour, IComparable<APinchable>
{
	public PinchManager PinchingHandPinchManager { get; set; }

	public virtual bool IsUsedByPinchMeIndicator => true;
	public virtual float PinchExitThreshold => 0.97f;
	public virtual int Priority => 0;
	public virtual Vector3 PinchMeIndicatorLineStartPosition { get; set; }

	protected int _numberOfPinchersInside = 0;
	protected AHoverEffect _hoverEffect;

	private void Awake()
	{
		_hoverEffect = GetComponent<AHoverEffect>();
		DoOnAwake();
	}

	protected virtual void DoOnAwake()
	{

	}

	public virtual void OnHoverEnter(PinchManager pinchManager)
	{
		_numberOfPinchersInside++;
	}

	public virtual void OnHoverStay(PinchManager pinchManager)
	{
		ToggleHoverEffectState(pinchManager, ShouldEffectBeActiveOnHover(pinchManager));
	}

	public virtual bool ShouldEffectBeActiveOnHover(PinchManager pinchManager)
	{
		return true;
	}

	protected void ToggleHoverEffectState(PinchManager pinchManager, bool shouldStartEffect)
	{
		if (_hoverEffect == null)
		{
			return;
		}

		if (shouldStartEffect)
		{
			_hoverEffect.Activate(pinchManager);
		}
		else
		{
			_hoverEffect.Deactivate(pinchManager);
		}
	}

	public virtual void OnHoverExit(PinchManager pinchManager)
	{
		_numberOfPinchersInside--;
		ToggleHoverEffectState(pinchManager, _numberOfPinchersInside > 0);
	}

	public virtual bool CanBePinched(PinchManager pinchManager)
	{
		return true;
	}

	public virtual void OnPinchEnter(PinchManager pinchManager)
	{
		PinchingHandPinchManager = pinchManager;
		pinchManager.PinchedObject = this;
	}

	public virtual void OnPinchExit()
	{
		PinchingHandPinchManager.PinchedObject = null;
		PinchingHandPinchManager = null;
	}

	public virtual void UpdatePinchMeIndicatorLineStartPosition()
	{
		PinchMeIndicatorLineStartPosition = transform.position;
	}

	public int CompareTo(APinchable other)
	{
		//Using int.CompareTo - which is different than IComparable CompareTo method
		return other.Priority.CompareTo(Priority);
	}

	protected bool IsOtherHand(PinchManager pinchManager)
	{
		return PinchingHandPinchManager != null && PinchingHandPinchManager != pinchManager;
	}
}

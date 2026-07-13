using System.Collections;
using System.Collections.Generic;
using Shapes;
using TMPro;
using UnityEngine;

public class TextPopUpReferences : MonoBehaviour
{
    public Rectangle Background => _background;
    public TextMeshPro TextUI => _textUI;
    public TextPopUpScaler TextPopUpScaler => _textPopUpScaler;
    public TextPopUpAnimator TextPopUpAnimator => _textPopUpAnimator;

    [SerializeField] private Rectangle _background;
    [SerializeField] private TextMeshPro _textUI;
    [SerializeField] private TextPopUpScaler _textPopUpScaler;
    [SerializeField] private TextPopUpAnimator _textPopUpAnimator;
}
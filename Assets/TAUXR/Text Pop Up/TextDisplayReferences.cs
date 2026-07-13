using System.Collections;
using System.Collections.Generic;
using Shapes;
using TMPro;
using UnityEditor;
using UnityEngine;

[System.Serializable]
public class TextDisplayReferences
{
    public Rectangle Background => _background;
    public TextMeshPro TextUI => _textUI;
    public TextDisplayAnimator TextDisplayAnimator => _textDisplayAnimator;

    [SerializeField] private Rectangle _background;
    [SerializeField] private TextMeshPro _textUI;
    [SerializeField] private TextDisplayAnimator _textDisplayAnimator;
}
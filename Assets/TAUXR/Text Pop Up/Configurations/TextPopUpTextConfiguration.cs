using System.Collections;
using System.Collections.Generic;
using UnityEngine;

[System.Serializable]
public class TextPopUpTextConfiguration
{
    public string Id;
    [TextArea] public string Text;
    public Vector2 TextRectSize;
}
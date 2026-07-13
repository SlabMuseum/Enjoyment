using System.Collections;
using System.Collections.Generic;
using UnityEngine;

[System.Serializable]
public class TextData
{
    public string Id;
    [TextArea(1, 10)] public string Text;
    public Vector2 TextAreaSize;

    public TextData(string id, string text, Vector2 textAreaSize)
    {
        Id = id;
        Text = text;
        TextAreaSize = textAreaSize;
    }
}
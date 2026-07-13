using Sirenix.OdinInspector;
using Sirenix.Serialization;
using System;
using UnityEngine;


[Serializable]
[ShowOdinSerializedPropertiesInInspector]
public class SerializedMultichoiceQuestion
{
    [OdinSerialize]
    public string Question;
    [OdinSerialize]
    public string Answer1;
    [OdinSerialize]
    public string Answer2;
    [OdinSerialize]
    public string Answer3;

    public float size_x;
    public float size_y;
}


[Serializable]
public class TextAndScaleTuple
{
    [TextArea(3, 10)]
    public string text;

    [FoldoutGroup("Options")]
    [HorizontalGroup("Options/Split")]
    [VerticalGroup("Options/Split/Left")]
    [BoxGroup("Options/Split/Left/Scale")]
    public float scale_x;
    [BoxGroup("Options/Split/Left/Scale")]
    public float scale_y;


    [VerticalGroup("Options/Split/Right")]
    [BoxGroup("Options/Split/Right/Show only in")]
    [PropertyTooltip("Checking none of the options is equal to checking all of them")]
    public bool active, semi, passive;

}


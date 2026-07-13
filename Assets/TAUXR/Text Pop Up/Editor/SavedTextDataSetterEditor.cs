using System;
using System.Collections;
using System.Collections.Generic;
using UnityEditor;
using UnityEngine;

[CustomEditor(typeof(SavedTextDataSetter))]
public class SavedTextDataSetterEditor : Editor
{
    private SerializedProperty _textId;
    private TextDisplay _textDisplay;
    private static int _currentTextDataIndex = 0;

    private void OnEnable()
    {
        _textId = serializedObject.FindProperty("_textId");
    }

    public override void OnInspectorGUI()
    {
        SavedTextDataSetter savedTextDataSetter = (SavedTextDataSetter)target;
        if (_textDisplay == null)
        {
            _textDisplay = savedTextDataSetter.GetComponent<TextDisplay>();
        }

        serializedObject.Update();
        _currentTextDataIndex = _textDisplay.TextsData.GetTextIndexById(_textId.stringValue);


        EditorGUILayout.PropertyField(_textId);
        if (GUILayout.Button("Set Text By Id"))
        {
            _textDisplay.SetPropertiesByTextData(_textId.stringValue);
            _textDisplay.SetTextFromConfiguration(_textId.stringValue, Application.isPlaying);
        }

        EditorGUILayout.Space(10);
        EditorGUILayout.LabelField("Change Text:", EditorStyles.boldLabel);
        EditorGUILayout.BeginHorizontal();
        if (GUILayout.Button("Previous"))
        {
            _currentTextDataIndex = _currentTextDataIndex <= 0 ? _textDisplay.TextsData.TextsData.Count - 1 : _currentTextDataIndex - 1;
            _textId.stringValue = _textDisplay.TextsData.TextsData[_currentTextDataIndex].Id;
            _textDisplay.SetPropertiesByTextData(_textId.stringValue);
            _textDisplay.SetTextFromConfiguration(_textId.stringValue, Application.isPlaying);
        }

        if (GUILayout.Button("Next"))
        {
            _currentTextDataIndex = _currentTextDataIndex >= _textDisplay.TextsData.TextsData.Count - 1 ? 0 : _currentTextDataIndex + 1;
            _textId.stringValue = _textDisplay.TextsData.TextsData[_currentTextDataIndex].Id;
            _textDisplay.SetPropertiesByTextData(_textId.stringValue);
            _textDisplay.SetTextFromConfiguration(_textId.stringValue, Application.isPlaying);
        }

        EditorGUILayout.EndHorizontal();

        serializedObject.ApplyModifiedProperties();
    }
}
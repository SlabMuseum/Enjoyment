using System.Collections;
using System.Collections.Generic;
using UnityEditor;
using UnityEngine;

[CustomEditor(typeof(TextPopUp))]
public class TextPopUpEditor : Editor
{
    private Vector2 _textSize;
    private readonly int _spacingBetweenSections = 5;
    private TextPopUp _textPopUp;

    public override void OnInspectorGUI()
    {
        base.OnInspectorGUI();
        _textPopUp = (TextPopUp)target;

        AddGetTextSection();
        EditorGUILayout.Space(_spacingBetweenSections);
        AddScalingSection();
        EditorGUILayout.Space(_spacingBetweenSections);
        AddStateSection();
        EditorGUILayout.Space(_spacingBetweenSections);
        AddLanguageSection();
    }

    private void AddGetTextSection()
    {
        if (GUILayout.Button("Get text from component"))
        {
            _textPopUp.GetTextFromComponent();
        }
    }

    private void AddScalingSection()
    {
        EditorGUILayout.LabelField("Scaling", EditorStyles.boldLabel);
        if (GUILayout.Button("Set text and auto scale"))
        {
            _textPopUp.SetTextAndAutoScale();
        }

        EditorGUILayout.Space(_spacingBetweenSections);

        _textSize = EditorGUILayout.Vector2Field("Text size", _textSize);
        if (GUILayout.Button("Set text and scale"))
        {
            _textPopUp.SetTextAndScale(_textSize);
        }
    }

    private void AddStateSection()
    {
        EditorGUILayout.LabelField("Set state in editor", EditorStyles.boldLabel);
        GUILayout.BeginHorizontal();
        if (GUILayout.Button("Enabled"))
        {
            _textPopUp.SetActiveState(true);
        }

        if (GUILayout.Button("Disabled"))
        {
            _textPopUp.SetActiveState(false);
        }

        GUILayout.EndHorizontal();
    }

    private void AddLanguageSection()
    {
        EditorGUILayout.LabelField("Set language", EditorStyles.boldLabel);
        GUILayout.BeginHorizontal();
        if (GUILayout.Button("English"))
        {
            _textPopUp.SetLanguageToEnglish();
        }

        if (GUILayout.Button("Hebrew"))
        {
            _textPopUp.SetLanguageToHebrew();
        }

        GUILayout.EndHorizontal();
    }
}
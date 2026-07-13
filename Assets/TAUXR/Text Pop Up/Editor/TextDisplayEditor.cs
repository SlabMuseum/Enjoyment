using System;
using System.Collections;
using System.Collections.Generic;
using NaughtyAttributes;
using UnityEditor;
using UnityEngine;

[CustomEditor(typeof(TextDisplay))]
public class TextDisplayEditor : Editor
{
    private readonly int _spacingBetweenSections = 10;
    private TextDisplay _textDisplay;
    private static int _languageToggleValue;
    private static bool _isSettingsFoldoutGroupOpen = false;
    private static bool _isTextDataFoldoutGroupOpen = false;

    private SerializedProperty _textDisplayReferences;
    private SerializedProperty _startingState;
    private SerializedProperty _text;
    private SerializedProperty _textAreaSize;
    private SerializedProperty _textId;
    private SerializedProperty _backgroundPadding;
    private SerializedProperty _textsData;

    private void OnEnable()
    {
        _textDisplayReferences = serializedObject.FindProperty("_textDisplayReferences");
        _startingState = serializedObject.FindProperty("_startingState");
        _text = serializedObject.FindProperty("_text");
        _textAreaSize = serializedObject.FindProperty("_textAreaSize");
        _textId = serializedObject.FindProperty("_textId");
        _backgroundPadding = serializedObject.FindProperty("_backgroundPadding");
        _textsData = serializedObject.FindProperty("_textsData");
    }

    public override void OnInspectorGUI()
    {
        _textDisplay = (TextDisplay)target;
        serializedObject.Update();

        DrawInspector();
        serializedObject.ApplyModifiedProperties();

        //TODO: figure out how to only do this if there was a change
        //Begin/End change check and hasModifiedProperties does not work
        _textDisplay.SetText(_text.stringValue);
        _textDisplay.SetScale(_textAreaSize.vector2Value, false);
    }

    private void DrawInspector()
    {
        EditorGUILayout.Space(_spacingBetweenSections / 2);

        DrawGeneralSettingsFoldoutGroup();
        EditorGUILayout.Space(_spacingBetweenSections);
        DrawTextSettingsFoldoutGroup();

        EditorGUILayout.Space(_spacingBetweenSections / 2);
    }

    private void DrawGeneralSettingsFoldoutGroup()
    {
        _isSettingsFoldoutGroupOpen = EditorGUILayout.Foldout(_isSettingsFoldoutGroupOpen, "General Settings", EditorStyles.foldoutHeader);
        if (_isSettingsFoldoutGroupOpen)
        {
            EditorGUILayout.Space(_spacingBetweenSections);
            EditorGUILayout.PropertyField(_textDisplayReferences);
            EditorGUILayout.Space(_spacingBetweenSections);
            EditorGUILayout.PropertyField(_startingState);

            EditorGUILayout.Space(_spacingBetweenSections);
            DrawChangeVisibilityStateSection();
            EditorGUILayout.Space(_spacingBetweenSections);
            DrawAddLanguageSection();

            EditorGUILayout.Space(_spacingBetweenSections);
            EditorGUILayout.PropertyField(_backgroundPadding);
        }
    }


    private void DrawChangeVisibilityStateSection()
    {
        EditorGUILayout.LabelField("Set visibility state:", EditorStyles.boldLabel);
        GUILayout.BeginHorizontal();
        if (GUILayout.Button("Show"))
        {
            _textDisplay.SetVisibilityState(true);
            SceneView.RepaintAll();
        }

        if (GUILayout.Button("Hide"))
        {
            _textDisplay.SetVisibilityState(false);
            SceneView.RepaintAll();
        }

        GUILayout.EndHorizontal();
    }

    private void DrawAddLanguageSection()
    {
        EditorGUILayout.LabelField("Language:", EditorStyles.boldLabel);
        int previousLanguageToggleValue = _languageToggleValue;
        _languageToggleValue = GUILayout.SelectionGrid(_languageToggleValue, new[] { "English", "Hebrew" }, 2, EditorStyles.radioButton);

        if (_languageToggleValue == previousLanguageToggleValue)
            return;

        Action changeLanguageMethod = _languageToggleValue == 0 ? _textDisplay.SetLanguageToEnglish : _textDisplay.SetLanguageToHebrew;
        changeLanguageMethod.Invoke();
        SceneView.RepaintAll();
    }

    private void DrawTextSettingsFoldoutGroup()
    {
        _isTextDataFoldoutGroupOpen =
            EditorGUILayout.Foldout(_isTextDataFoldoutGroupOpen, "Text Settings", EditorStyles.foldoutHeader);
        if (_isTextDataFoldoutGroupOpen)
        {
            EditorGUILayout.Space(_spacingBetweenSections);
            DrawTextSettingsSection();
            EditorGUILayout.LabelField("", GUI.skin.horizontalSlider);
            DrawTextDataSection();
        }
    }

    private void DrawTextSettingsSection()
    {
        EditorGUILayout.PropertyField(_text);
        EditorGUILayout.PropertyField(_textAreaSize);
    }


    private void DrawTextDataSection()
    {
        EditorGUILayout.PropertyField(_textId);
        if (GUILayout.Button("Save Text Data"))
        {
            _textDisplay.SaveTextData(_textId.stringValue);
        }

        EditorGUILayout.Space(_spacingBetweenSections);
        EditorGUILayout.PropertyField(_textsData);
    }
}
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

[CreateAssetMenu(fileName = "TextDisplayData", menuName = "ScriptableObjects/Configurations/TextDisplayData")]
public class TextDataScriptableObject : ScriptableObject
{
    public List<TextData> TextsData;

    public TextData GetTextConfiguration(string textId)
    {
        TextData textData =
            TextsData.Find((textData) => textData.Id == textId);

        if (textData == null)
        {
            Debug.LogWarning("No text configuration with id: " + textId + " found");
        }

        return textData;
    }

    public void AddOrReplace(TextData textData)
    {
        int existingTextIndex = GetTextIndexById(textData.Id);
        if (existingTextIndex != -1)
        {
            TextsData[existingTextIndex] = textData;
            return;
        }

        TextsData.Add(textData);
    }

    public int GetTextIndexById(string textId)
    {
        return TextsData.FindIndex((data) => data.Id == textId);
    }
}
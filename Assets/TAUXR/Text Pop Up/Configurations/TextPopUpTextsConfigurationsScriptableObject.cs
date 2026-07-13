using System.Collections;
using System.Collections.Generic;
using UnityEngine;

[CreateAssetMenu(fileName = "TextPopUpTextConfigurations", menuName = "ScriptableObjects/Configurations/TextPopUpTextsConfigurations")]
public class TextPopUpTextsConfigurationsScriptableObject : ScriptableObject
{
    public List<TextPopUpTextConfiguration> TextConfigurations;

    public TextPopUpTextConfiguration GetTextConfiguration(string textId)
    {
        TextPopUpTextConfiguration textConfiguration =
            TextConfigurations.Find((textConfiguration) => textConfiguration.Id == textId);

        if (textConfiguration == null)
        {
            Debug.LogWarning("No text configuration with id: " + textId + " found");
        }

        return textConfiguration;
    }
}
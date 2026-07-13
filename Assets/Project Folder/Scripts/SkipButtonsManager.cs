using TMPro;
using UnityEngine;
public class SkipButtonsManager : MonoBehaviour
{
    public TextMeshPro stateText;
    public GameObject[] skipButtons;
    private State state;

    void Start()
    {
        state = State.Disabled;
        DisableButtons();
        SetText();
    }
    private void DisableButtons()
    {
        foreach (GameObject button in skipButtons)
        {
            button.SetActive(false);
        }
    }

    private void EnableButtons()
    {
        foreach (GameObject button in skipButtons)
        {
            button.SetActive(true);
        }
    }

    private void SetText()
    {
        stateText.text = "Skip " + state.ToString();
    }

    public void ToggleState()
    {
        if (state == State.Disabled)
        {
            state = State.Enabled;
            EnableButtons();
        }
        else
        {
            state = State.Disabled;
            DisableButtons();
        }
        SetText();
    }


    enum State
    {
        Disabled,
        Enabled
    }


}

using UnityEngine;
using UnityEngine.Events;

public class MultichoiceAnswer : MonoBehaviour
{

    public string answerText;
    public TXRButton button;

    public static UnityEvent<string> OnAnswerSelected = new UnityEvent<string>();

    private void Start()
    {
        Init();
    }

    void Init()
    {
        button = GetComponentInChildren<TXRButton>(true);
        button.Pressed.AddListener(() => SelectAnswer(answerText));
    }


    void SelectAnswer(string selectedAnswer)
    {
        OnAnswerSelected.Invoke(selectedAnswer);
        button.Pressed.RemoveListener(() => SelectAnswer(answerText));
    }

    internal void SetText(string answer)
    {
        Init();

        button.SetText(answer);
        answerText = answer;
    }

    public void OnEnable()
    {
        Init();
        button.SetInteractable(true);
        button.SetState(TXRButtonState.Active);
    }
}


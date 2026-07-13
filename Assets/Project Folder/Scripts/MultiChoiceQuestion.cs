using Cysharp.Threading.Tasks;
using Sirenix.OdinInspector;
using System;
using System.Collections.Generic;
using UnityEngine;

public class MultiChoiceQuestion : MonoBehaviour, Question
{
    [SerializeField]
    private TextPopUp board;
    [SerializeField]
    private List<MultichoiceAnswer> _answers;
    private UniTaskCompletionSource<string> answerCompletionSource;

    private string _question;
    private string _answer1;
    private string _answer2;
    private string _answer3;

    private void InitAnswers()
    {
        _answers = new List<MultichoiceAnswer>();
        _answers.AddRange(GetComponentsInChildren<MultichoiceAnswer>());
    }

    private void Start()
    {
        InitAnswers();
        MultichoiceAnswer.OnAnswerSelected.AddListener(ProcessAnswer);

    }

    [Button("Answer (Debug)")]
    void ProcessAnswer(string selectedAnswer)
    {

        // Complete the UniTask when an answer is selected
        answerCompletionSource?.TrySetResult(selectedAnswer);


        Debug.Log("Selected answer: " + selectedAnswer);
        TXRDataManager.Instance.ReportMultichoiceAnswer(board.GetText(), _answer1, _answer2, _answer3, selectedAnswer);
    }

    private void SetAnswers(string answer1, string answer2, string answer3)
    {
        _answers[0].SetText(answer1);
        _answers[1].SetText(answer2);
        _answers[2].SetText(answer3);

        _answer1 = answer1;
        _answer2 = answer2;
        _answer3 = answer3;

    }

    public void setQuestionWithAutoScale(string question, string answer1, string answer2, string answer3)
    {
        board.SetTextAndAutoScale(question);

        _answers[0].SetText(answer1);
        _answers[1].SetText(answer2);
        _answers[2].SetText(answer3);

        _question = question;
        _answer1 = answer1;
        _answer2 = answer2;
        _answer3 = answer3;
    }

    public void setQuestionAndScale(string question, string answer1, string answer2, string answer3, float scale_x, float scale_y)
    {
        board.SetTextAndScale(question, new Vector2(scale_x, scale_y));

        _answers[0].SetText(answer1);
        _answers[1].SetText(answer2);
        _answers[2].SetText(answer3);

        _question = question;
        _answer1 = answer1;
        _answer2 = answer2;
        _answer3 = answer3;
    }


    public async UniTask WaitForAnswer()
    {
        // Create a new UniTaskCompletionSource
        answerCompletionSource = new UniTaskCompletionSource<string>();

        // Wait until an answer is selected
        string selectedAnswer = await answerCompletionSource.Task;

        // Clean up
        answerCompletionSource = null;

        Hide();

    }

    public async UniTask SetQuestionAndWaitForAnswer(string question, string answer1, string answer2, string answer3)
    {
        Show();
        InitAnswers();
        setQuestionWithAutoScale(question, answer1, answer2, answer3);
        await UniTask.Delay(TimeSpan.FromSeconds(2));
        await WaitForAnswer();

        Hide();
    }

    public async UniTask SetQuestionAndScaleAndWaitForAnswer(string question, string answer1, string answer2, string answer3, float scale_x, float scale_y)
    {
        Show();
        InitAnswers();
        setQuestionAndScale(question, answer1, answer2, answer3, scale_x, scale_y);
        await UniTask.Delay(TimeSpan.FromSeconds(2));
        await WaitForAnswer();

        Hide();
    }

    public async UniTask SetAnswersAndAndWaitForAnswer(string answer1, string answer2, string answer3)
    {
        Debug.Log("MultiChoiceQuestion.cs : SetAnswersAndAndWaitForAnswer()");
        Show();
        InitAnswers();
        SetAnswers(answer1, answer2, answer3);
        Debug.Log("MultiChoiceQuestion.cs : SetAnswersAndAndWaitForAnswer() : SetAnswers() done");
        await UniTask.Delay(TimeSpan.FromSeconds(1));
        await WaitForAnswer();
        Debug.Log("MultiChoiceQuestion.cs : SetAnswersAndAndWaitForAnswer() : WaitForAnswer() done");
        Hide();
    }

    public void Hide()
    {
        gameObject.SetActive(false);
    }
    public void Show()
    {
        gameObject.SetActive(true);
    }

}

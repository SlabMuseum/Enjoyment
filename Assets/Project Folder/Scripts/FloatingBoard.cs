using Cysharp.Threading.Tasks;
using UnityEngine;

public class FloatingBoard : MonoBehaviour
{
    [SerializeField]
    private TextPopUp board;
    [SerializeField]
    private TXRButton ContinueButton;

    //AutoScale: Text will be scaled to fit the board
    public async UniTask ShowTextUntilContinue(string text)
    {
        SetText(text);
        await ShowUntilContinuePressed();
    }

    private void SetText(string text)
    {
        board.SetTextAndAutoScale(text);
    }

    //ManualScale
    public async UniTask ShowTextAndScaleUntilContinue(TextAndScaleTuple tup)
    {
        SetTextWithCustomScale(tup);
        await ShowUntilContinuePressed();
    }
    private void SetTextWithCustomScale(TextAndScaleTuple tup)
    {
        board.SetTextAndScale(tup.text, new Vector2(tup.scale_x, tup.scale_y));
    }



    private async UniTask ShowUntilContinuePressed()
    {
        board.Show();
        ContinueButton.gameObject.SetActive(true);
        //ContinueButton.SetState(ButtonState.Interactable);

        await ContinueButton.WaitForButtonPress();

        //await UniTask.Delay(TimeSpan.FromSeconds(1));

        board.Hide();
        ContinueButton.gameObject.SetActive(false);
        //ContinueButton.SetState(ButtonState.Hidden);
    }



}

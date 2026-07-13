using Sirenix.OdinInspector;
using System.Collections;
using UnityEngine;

public class testTextPopUp : MonoBehaviour
{
    // Start is called before the first frame update
    void Start()
    {

    }

    // Update is called once per frame
    void Update()
    {

    }

    [Button]

    public void testShowHide()
    {
        StartCoroutine(ShowAndHide());
    }

    IEnumerator ShowAndHide()
    {
        TextPopUp popUp = GetComponent<TextPopUp>();
        popUp.Show();
        yield return StartCoroutine(DelaySeconds(3));
        popUp.Hide();
    }

    [Button]
    public void testShow()
    {
        TextPopUp popUp = GetComponent<TextPopUp>();
        popUp.Show();
    }
    [Button]
    public void testHide()
    {
        TextPopUp popUp = GetComponent<TextPopUp>();
        popUp.Hide();
    }

    IEnumerator DelaySeconds(float delayInSeconds)
    {
        Debug.Log("Waiting for " + delayInSeconds + " seconds...");
        yield return new WaitForSeconds(delayInSeconds);
    }

}

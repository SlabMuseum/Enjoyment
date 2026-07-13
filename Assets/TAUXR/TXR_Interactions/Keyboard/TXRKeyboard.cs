using Cysharp.Threading.Tasks;
using Sirenix.OdinInspector;
using TMPro;
using UnityEngine;

public class TXRKeyboard : MonoBehaviour
{
    [SerializeField] private TextMeshPro _typedText;
    public Transform InputFieldTransform;
    private string _inputText;
    [SerializeField] bool _isTyping = true;
    private Animator animator;
    private float _timeSinceLastChar = 0;
    private Transform _lastTypingToucher;
    [SerializeField] private AudioSource _showSound;
    [SerializeField] private AudioSource _hideSound;
    [SerializeField] private AudioSource _typingSound;
    private void Start()
    {
        animator = GetComponent<Animator>();
    }
    void Update()
    {
        if (_isTyping && _typedText.text != _inputText)
        {
            _typedText.text = _inputText;
        }
    }

    public void CharPressed(string c, Transform toucher)
    {
        if (!IsValidTyping(toucher)) return;
        _inputText += c;
        PlayTypingSound();
    }

    private bool IsValidTyping(Transform typingToucher)
    {
        if (_lastTypingToucher == null)
        {
            _lastTypingToucher = typingToucher;
            _timeSinceLastChar = Time.time;
            return true;
        }

        if (_lastTypingToucher == typingToucher && Time.time - _timeSinceLastChar < .25f) return false;

        // if we got here its a valid typing.
        _lastTypingToucher = typingToucher;
        _timeSinceLastChar = Time.time;

        return true;
    }

    public void DeleteLast()
    {
        if (_inputText.Length < 1) return;
        _inputText = _inputText.Remove(_inputText.Length - 1);
    }

    public void DonePressed()
    {
        PlayTypingSound();
        _isTyping = false;
    }

    public async UniTask OpenKeyboardAndWaitForInput(TextMeshPro textToDisplay)
    {
        if (_typedText != null) _typedText.gameObject.SetActive(false); // for testing text to disappear.

        _isTyping = true;
        _typedText = textToDisplay;
        _inputText = textToDisplay.text;
        Show();
        while (_isTyping)
        {
            await UniTask.Yield();
        }

        _typedText = null;
        Hide();

    }

    [Button]
    private void Show()
    {
        animator.SetTrigger("Fade In");
        _showSound.Stop();
        _showSound.Play();
    }

    private void Hide()
    {
        animator.SetTrigger("Fade Out");
    }

    private void PlayTypingSound()
    {
        if (_typingSound == null) return;
        _typingSound.Stop();
        _typingSound.Play();
    }
}

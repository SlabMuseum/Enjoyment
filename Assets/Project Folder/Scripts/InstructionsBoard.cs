using Cysharp.Threading.Tasks;
using System;
using UnityEngine;

public class InstructionsBoard : MonoBehaviour
{
    [SerializeField]
    private TXRButton _continueButton;
    [SerializeField]
    private AudioClip _audioClip;
    [SerializeField]
    bool _disableOnAwake;

    private Animator _animator;
    private AudioSource _audioSource;

    private String _hideAnimationName = "HideBoard";

    private void Awake()
    {
        _animator = GetComponent<Animator>();
        _audioSource = GetComponent<AudioSource>();
        _audioSource.playOnAwake = false;
        _audioSource.clip = _audioClip;
        _continueButton.gameObject.SetActive(false);
        if (_disableOnAwake)
        {
            gameObject.SetActive(false);
        }
    }


    public void Show(bool WithButton)
    {
        gameObject.SetActive(true);
        if (WithButton)
        {
            _continueButton.gameObject.SetActive(true);
        }
        TXRDataManager.Instance.LogLineToFile("Instructions board shown: " + gameObject.name);
    }
    private void Disable()
    {
        _continueButton.gameObject.SetActive(false);
        gameObject.SetActive(false);
    }
    public async UniTask HideAndWaitForAnimation()
    {
        _animator.SetTrigger("Hide");
        await UniTask.WaitUntil(() => _animator.GetCurrentAnimatorStateInfo(0).IsName(_hideAnimationName));
        await UniTask.WaitWhile(() => _animator.GetCurrentAnimatorStateInfo(0).IsName(_hideAnimationName));
        TXRDataManager.Instance.LogLineToFile("Instructions board hidden " + gameObject.name);
        Disable();
    }

    public async UniTask ShowUntilContinuePressed()
    {
        Show(true);
        _audioSource.Play();
        await _continueButton.WaitForButtonPress();
        await HideAndWaitForAnimation();
    }

    public async UniTask ShowUntilAudioEnds()
    {
        Show(false);
        _audioSource.Play();
        await UniTask.Delay(TimeSpan.FromSeconds(_audioClip.length));
        await HideAndWaitForAnimation();
    }

}

using Cysharp.Threading.Tasks;
using Sirenix.OdinInspector;
using UnityEngine;

public enum AudioGuideState { Started, Finished }



public class AudioGuideButton : MonoBehaviour
{
    private Piece _piece;
    private AudioSource _audioGuideSource;
    private TXRButton _txrButtonTouch;
    private bool _isPlaying = false;
    private AudioTimeLeft _audioTimeLeft;
    private Glow _glow;
    private bool _shouldButtonGlow;


    private GoToTarget _directionArrow;


    private void Awake()
    {
        _audioGuideSource = GetComponent<AudioSource>();
        _txrButtonTouch = GetComponent<TXRButton>();
        _piece = GetComponentInParent<Piece>();
        _audioTimeLeft = GetComponentInChildren<AudioTimeLeft>();
        _glow = GetComponentsInChildren<Glow>()[0];
        _glow.Deactivate();
        _shouldButtonGlow = SceneReferencer.Instance.shouldButtonGlow;

    }

    private void Start()
    {

        _audioTimeLeft.gameObject.SetActive(false);
        _audioGuideSource.clip = _piece.audioGuideClip;
        _directionArrow = SceneReferencer.Instance.DirectionArrow;
        _txrButtonTouch.Pressed.AddListener(Play);

    }

    [Button("Play")]
    public void Play()
    {
        // If the audio guide is not playing, play it
        if (!_isPlaying)
        {
            //PlayAudioAsync().Forget();
            _audioGuideSource.Play();
            TXRDataManager.Instance.ReportAudioGuideTiming(_piece.name, AudioGuideState.Started.ToString());

            _isPlaying = true;
            _audioTimeLeft.gameObject.SetActive(true);
            _directionArrow.Hide();
            _piece.arrow.Hide();
        }
    }

    //private async UniTask PlayAudioAsync()
    //{
    //    _audioGuideSource.Play();
    //    await UniTask.Yield();
    //}

    // Skip the audio guide, for debug only!!!
    [Button("Skip")]
    public void Skip()
    {
        _audioGuideSource.time = _audioGuideSource.clip.length - 2f;
    }


    public async UniTask WaitForAudioGuideToFinish()
    {
        if (_shouldButtonGlow)
        {
            _glow.Activate();
        }

        //wait for player to hit play
        Debug.Log("Waiting for audio to start...");
        await new WaitUntil(() => _audioGuideSource.isPlaying == true);

        if (_shouldButtonGlow)
        {
            _glow.Deactivate();
        }
        // wait for audio guide to finish
        Debug.Log("Waiting for audio to finish...");
        await new WaitUntil(() => _audioGuideSource.isPlaying == false);
        _audioTimeLeft.gameObject.SetActive(false);

        TXRDataManager.Instance.ReportAudioGuideTiming(_piece.name, AudioGuideState.Finished.ToString());

    }

    public async UniTask waitForPress()
    {
        if (_shouldButtonGlow)
        {
            _glow.Activate();
        }
        //wait for player to hit play
        await new WaitUntil(() => _audioGuideSource.isPlaying == true);
        if (_shouldButtonGlow)
        {
            _glow.Deactivate();
        }
    }

}


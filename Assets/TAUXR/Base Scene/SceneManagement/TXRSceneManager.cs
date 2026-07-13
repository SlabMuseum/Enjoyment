using UnityEditor;
using UnityEngine;
using Cysharp.Threading.Tasks;
using UnityEngine.SceneManagement;

public class TXRSceneManager : TXRSingleton<TXRSceneManager>
{

    [Header("All scenes")]      // declare by name each scene and make it public so it can be accessed easily from other scripts.
    [SerializeField] public string BaseSceneName = "Base Scene";
    [SerializeField] public string FirstLoadedSceneName = "TAUXR Entry Scene";

    private float FADETOBLACKDURATION = 2.5f;
    private float FADETOCLEARDURATION = 1.5f;

    private string currentSceneName;
    public string CurrentSceneName => currentSceneName;

    bool _shouldRepositionPlayer;
    // gets isProjectUsingCalibration to know whether to use PlayerRepositioner or not.
    public void Init(bool isProjectUsingCalibration)
    {
        // if project is being calibrated to a space then moving it to a PlayerRepositioner will ruin calibration.
        _shouldRepositionPlayer = !isProjectUsingCalibration;

        // the script assumes that Base Scene is always the first in the build order.
        if (Application.isEditor)
        {
            InitializeInEditor();
        }
        else
        {
            InitializeInBuild();
        }
    }

    private void InitializeInEditor()
    {
        // do nothing if scene count is not bigger than 1
        if (SceneManager.sceneCount < 2)
        {
            Debug.LogWarning("Scene count is less than 2, no scene initialization");
            return;
        }

        RepositionPlayerIfNeeded();

        // we assume that when played in editor we'll be in the right scene combination.
        for (int i = 0; i < SceneManager.sceneCount; i++)
        {
            // Get the scene at the specified index
            Scene scene = SceneManager.GetSceneAt(i);

            if (scene.name != BaseSceneName)
            {
                currentSceneName = scene.name;
                return;
            }

        }
        // if we got here it means we only have the base scene (for 1 scene projects) and it should be the current
        currentSceneName = BaseSceneName;
    }

    private void InitializeInBuild()
    {
        TXRPlayer.Instance.FadeViewToColor(Color.black, 0).Forget();
        currentSceneName = BaseSceneName;
        // make sure to launch your starting scene here
        LoadActiveScene(FirstLoadedSceneName).Forget();
    }

    async private UniTask LoadActiveScene(string sceneName)
    {
        if (currentSceneName == sceneName)
        {
            Debug.LogWarning($"Tried to load {sceneName} scene but its already loaded");
            return;
        }

        await SceneManager.LoadSceneAsync(sceneName, LoadSceneMode.Additive);
        currentSceneName = sceneName;

        // reposition player accordingly to new scene
        RepositionPlayerIfNeeded();

        await TXRPlayer.Instance.FadeViewToColor(Color.clear, FADETOCLEARDURATION);
    }

    async public UniTask SwitchActiveScene(string sceneName)
    {
        if (currentSceneName == sceneName)
        {
            Debug.LogWarning($"Tried to load {sceneName} scene but its already loaded");
            return;
        }

        await UnloadActiveScene();

        await LoadActiveScene(sceneName);

    }

    async private UniTask UnloadActiveScene()
    {
        await TXRPlayer.Instance.FadeViewToColor(Color.black, FADETOBLACKDURATION);

        await SceneManager.UnloadSceneAsync(currentSceneName);
    }


    private void RepositionPlayerIfNeeded()
    {
        // if project is being calibrated to a space then moving it to a PlayerRepositioner will ruin calibration.
        if (!_shouldRepositionPlayer) return;

        PlayerRepositioner repositioner = FindObjectOfType<PlayerRepositioner>();
        if (repositioner == null) return;
        TXRPlayer.Instance.RepositionPlayer(repositioner);
    }
}

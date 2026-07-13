
using Cysharp.Threading.Tasks;
using UnityEngine;

public class ProjectInitializer : MonoBehaviour
{
    [SerializeField] private bool _shouldProjectUseCalibration;     // true if project should be calibrated into a physical space.
    [SerializeField] private bool _shouldCalibrateOnEditor;

    private void Start()
    {
        StartTAUXRExperience().Forget();
    }

    private async UniTask StartTAUXRExperience()
    {
        bool shouldCalibrateOnBuild = !Application.isEditor && _shouldProjectUseCalibration;
        bool shouldCalibrateOnEditor = _shouldCalibrateOnEditor && Application.isEditor && _shouldProjectUseCalibration;

        if (shouldCalibrateOnBuild || shouldCalibrateOnEditor)
        {
            // trigger calibration on BaseScene
            await EnvironmentCalibrator.Instance.CalibrateRoom();
        }

        // after environment was calibrated- load first scene
        TXRSceneManager.Instance.Init(_shouldProjectUseCalibration);
    }

}

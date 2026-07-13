using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using Cysharp.Threading.Tasks;

public class RoundManager : TXRSingleton<RoundManager>
{
    [SerializeField] private Trial[] _trials;
    private int _currentTrial = 0;
    private Round _currentRound;

    public async UniTask RunRoundFlow(Round round)
    {
        _currentRound = round;
        StartRound();

        while (_currentTrial < _trials.Length)
        {
            await TrialManager.Instance.RunTrialFlow(_trials[_currentTrial]);
            await BetweenTrialsFlow();
            _currentTrial++;
        }

        EndRound();
    }

    private void StartRound()
    {
        // setup round initial conditions.
    }


    private void EndRound()
    {
        // setup end round conditions
    }

    private async UniTask BetweenTrialsFlow()
    {
        await UniTask.Yield();

    }
}
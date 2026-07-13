using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using System;
using Sirenix.OdinInspector;
using Sirenix.Serialization;

public class FlowManagersCreator : MonoBehaviour
{
    [Range(2, 3)] [SerializeField] private int _numberOfFlowUnits = 2;

    [Button]
    public void CreateFlowManagers()
    {
        CreateFlowManager(typeof(TrialManager));
        CreateFlowManager(typeof(RoundManager));

        if (_numberOfFlowUnits > 2)
        {
            CreateFlowManager(typeof(SessionManager));
        }
    }

    private void CreateFlowManager(Type componentType)
    {
        GameObject flowManager = new GameObject();
        flowManager.transform.parent = transform;
        flowManager.AddComponent(componentType);
        flowManager.name = componentType.ToString();
    }
}
#if UNITY_EDITOR
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class ChildrenRenamer : MonoBehaviour
{
    [SerializeField] private string _objectBaseName;

    public void RenameTopLevelChildren()
    {
        int numberReduceAmount = 0;
        for (int i = 0; i < transform.childCount; i++)
        {
            if (!transform.GetChild(i).name.Contains(_objectBaseName))
            {
                transform.GetChild(i).name = _objectBaseName + " " + (i + 1 - numberReduceAmount);
            }
            else
            {
                numberReduceAmount++;
            }
        }
    }
}

#endif
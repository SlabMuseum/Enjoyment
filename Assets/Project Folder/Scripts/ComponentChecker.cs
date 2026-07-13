using UnityEngine;

public class ComponentChecker : MonoBehaviour
{
    // The component type you want to check for
    public Component targetComponent;

    // Recursive function to search for the component in children
    public static T GetComponentInAllChildren<T>(Transform parent) where T : Component
    {
        // Check if the parent has the target component
        T component = parent.GetComponent<T>();
        if (component != null)
            return component;

        // Recursively check all children
        foreach (Transform child in parent)
        {
            T childComponent = GetComponentInAllChildren<T>(child);
            if (childComponent != null)
                return childComponent;
        }

        return null;
    }

}
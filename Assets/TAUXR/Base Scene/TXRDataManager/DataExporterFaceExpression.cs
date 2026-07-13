using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using System.IO;

public class DataExporterFaceExpression : MonoBehaviour
{
    public string FileName = "";
    OVRFaceExpressions OVRFace;

    float[] AllWeights;     // updates every frame with the weights of all blendshapes

    StreamWriter writer;
    string path;

    public void Init()
    {
        OVRFace = TXRPlayer.Instance.OVRFace;

        if (OVRFace == null)
        {
            Debug.LogError("Tried to export face tracking data but OVRFace is not assigned");
            return;
        }

        // init array length to total amount of face expressions
        AllWeights = new float[(int)OVRFaceExpressions.FaceExpression.Max];

        // get all blendshapes names
        string[] blendShapesNames = System.Enum.GetNames(typeof(OVRFaceExpressions.FaceExpression));

        // write first line with face expressions index
        string firstLine = "TimeFromStart";
        foreach (string str in blendShapesNames)
            firstLine += $",{str}";

        // init Path
        path = getPath();
        print(path);
        // check if directory exists, if not - create it
        string dir = Path.GetDirectoryName(path);
        if (!Directory.Exists(dir))
            Directory.CreateDirectory(dir);

        // init StreamWriter
        writer = new StreamWriter(path, true);
        writer.WriteLine(firstLine);
    }

    public void CollectWriteDataToFile()
    {
        if (OVRFace == null)
        {
            Debug.LogError("Tries to export face tracking data but OVRFace is not assigned");
            return;
        }

        if(!OVRFace.ValidExpressions)
        {
            Debug.LogWarning("Can't log face expression data because OVRFace data is not valid");
            return;
        }

        // get expressions value
        OVRFace.CopyTo(AllWeights);

        // capture frame time
        string nextLine = $"{Time.time}";

        // write all weights to line
        for (int i = 0; i < AllWeights.Length; i++)
            nextLine += $",{AllWeights[i]}";

        // write to file
        writer.WriteLine(nextLine);
    }

    public void Close()
    {
        if (writer == null)
            return;

        writer.Flush();
        writer.Close();
    }

    private string getPath()
    {
        string str = $"{Application.persistentDataPath}/";
        str += $"{FileName}_FaceExpressionData_{TAUXRUtilities.GetFormattedDateTime(true)}.csv";
        print(str);
        return str;
    }
}
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Text;
using UnityEngine;

public class DataContinuousWriter : MonoBehaviour
{
    List<Transform> transformsToRecord;
    public float logFrequency = 0f; // Log frequency in seconds. 0 for logging every frame
    public string fileName = "ContinuousData"; // The name of the file to write to

    [Header("Default Transforms. Auto-fill if you have a TAUXRPlayer")]
    public Transform Head;
    public Transform RightHand;
    public Transform LeftHand;

    bool IsEyeTrackingEnabled;
    public Transform RightEye;
    public Transform LeftEye;

    [Header("Drag here any additional transform to record")]
    public Transform[] AdditionalTransforms;

    private string[] columnNames;
    private float lastLogTime = 0f;
    private int frameCount = 0;

    private string filePath;
    private StreamWriter writer;
    private StringBuilder rowBuilder = new StringBuilder();

    private TXRPlayer TAUXRPlayer;

    public void Init(bool ShouldRecordEyeTracking)
    {
        IsEyeTrackingEnabled= ShouldRecordEyeTracking;

        TAUXRPlayer = TXRPlayer.Instance;

        if (TAUXRPlayer != null)
        {
            TXRPlayer player = TXRPlayer.Instance;
            Head = player.PlayerHead;
            RightHand = player.RightHand;
            LeftHand = player.LeftHand;
            RightEye = player.RightEye;
            LeftEye = player.LeftEye;
        }

        AddAllTransformsToList();

        //setup file
        filePath = Path.Combine(Application.persistentDataPath, $"{fileName}_{TAUXRUtilities.GetFormattedDateTime(true)}.csv");
        writer = new StreamWriter(filePath);

        WriteColumnNames();
    }

    private void AddAllTransformsToList()
    {
        transformsToRecord = new List<Transform>();

        AddToTransformsToRecord(Head);
        AddToTransformsToRecord(RightHand);
        AddToTransformsToRecord(LeftHand);
        AddToTransformsToRecord(RightEye);
        AddToTransformsToRecord(LeftEye);

        foreach (Transform t in AdditionalTransforms)
            AddToTransformsToRecord(t);
    }

    private void AddToTransformsToRecord(Transform trans)
    {
        if (trans == null) return;
        transformsToRecord.Add(trans);

    }

    private void WriteColumnNames()
    {
        // 1 time + 6 head, 6 for each arm. +6* each transform in additional transforms.
        int columnCount = 1 + 6 + 12 + 6 * AdditionalTransforms.Length;
        if (IsEyeTrackingEnabled)
        {
            //+4 each eye (pitch and yaw) +1 focused object + 3 hit point world position
            columnCount += 8;
        }

        columnNames = new string[columnCount];
        columnNames[0] = "Time";
        int i = 1;

        if (Head != null)
        {
            columnNames[i++] = "Head_Position_x";
            columnNames[i++] = "Head_Height";
            columnNames[i++] = "Head_Position_Z";
            columnNames[i++] = "Gaze_Pitch";
            columnNames[i++] = "Gaze_Yaw";
            columnNames[i++] = "Gaze_Roll";
        }

        if (IsEyeTrackingEnabled)
        {
            columnNames[i++] = "FocusedObject";

            columnNames[i++] = "EyeGazeHitPosition_X";
            columnNames[i++] = "EyeGazeHitPosition_Y";
            columnNames[i++] = "EyeGazeHitPosition_Z";

            columnNames[i++] = "RightEye_Pitch";
            columnNames[i++] = "RightEye_Yaw";

            columnNames[i++] = "LeftEye_Pitch";
            columnNames[i++] = "LeftEye_Yaw";
        }


        foreach (Transform t in transformsToRecord)
        {
            if (t == Head || t == RightEye || t == LeftEye) continue;

            columnNames[i++] = t.name + "_Position_X";
            columnNames[i++] = t.name + "_Height";
            columnNames[i++] = t.name + "_Position_Z";
            columnNames[i++] = t.name + "_Pitch";
            columnNames[i++] = t.name + "_Yaw";
            columnNames[i++] = t.name + "_Roll";
        }

        Debug.Log(string.Join(",", columnNames));
        writer.WriteLine(string.Join(",", columnNames));
    }

    public void RecordContinuousData()
    {
        // TODO: Move logging frequency to TAUXRDataManager
        if (logFrequency == 0 || Time.time - lastLogTime >= logFrequency)
        {
            lastLogTime = Time.time;
            frameCount++;

            // Build the CSV row for this frame
            rowBuilder.Length = 0;
            rowBuilder.Append(Time.time.ToString("F4"));

            // write Head position and rotations
            rowBuilder.AppendFormat(",{0:F4},{1:F4},{2:F4},{3:F4},{4:F4},{5:F4}",
                    Head.position.x, Head.position.y, Head.position.z,
                    Head.eulerAngles.x, Head.eulerAngles.y, Head.eulerAngles.z);

            if (IsEyeTrackingEnabled)
            {
                if (TAUXRPlayer != null)
                {
                    if (TAUXRPlayer.FocusedObject != null)
                    {
                        rowBuilder.Append("," + TAUXRPlayer.FocusedObject.name);
                    }
                    else
                    {
                        rowBuilder.Append(",None");
                    }

                    rowBuilder.Append("," + TAUXRPlayer.EyeGazeHitPosition.x.ToString("F4"));
                    rowBuilder.Append("," + TAUXRPlayer.EyeGazeHitPosition.y.ToString("F4"));
                    rowBuilder.Append("," + TAUXRPlayer.EyeGazeHitPosition.z.ToString("F4"));

                    rowBuilder.Append("," + TAUXRPlayer.RightEye.localEulerAngles.x.ToString("F4"));
                    rowBuilder.Append("," + TAUXRPlayer.RightEye.localEulerAngles.y.ToString("F4"));
                    rowBuilder.Append("," + TAUXRPlayer.LeftEye.localEulerAngles.x.ToString("F4"));
                    rowBuilder.Append("," + TAUXRPlayer.LeftEye.localEulerAngles.y.ToString("F4"));
                }
            }

            for (int i = 0; i < transformsToRecord.Count; i++)
            {
                Transform t = transformsToRecord[i];

                // skip head and eyes because they are saved separately
                if (t == Head || t == RightEye || t == LeftEye) continue;

                // write transform data
                rowBuilder.AppendFormat(",{0:F4},{1:F4},{2:F4},{3:F4},{4:F4},{5:F4}",
                    t.position.x, t.position.y, t.position.z,
                    t.eulerAngles.x, t.eulerAngles.y, t.eulerAngles.z);
            }

            // Write the row to the CSV file
            writer.WriteLine(rowBuilder.ToString());
        }
    }

    public void Close()
    {
        if (writer == null) return;

        Debug.Log($"Logged {frameCount} frames to CSV file.");

        // Close the file stream
        writer.Flush();
        writer.Close();

        // Reset the frame count
        frameCount = 0;
    }
}
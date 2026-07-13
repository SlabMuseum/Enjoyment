using System;
using UnityEngine;


#region Analytics Data Classes
public interface AnalyticsDataClass
{
    string TableName { get; }
}

[Serializable]
public class AnalyticsLogLine : AnalyticsDataClass
{
    public string TableName => "TAUXR_Logs";
    public float LogTime;
    public string LogText;

    public AnalyticsLogLine(string line)
    {
        LogTime = Time.time;
        LogText = line;
    }
}

// Declare here new AnalyticsDataClasses for every table file output you desire.

[Serializable]
public class AudioGuideTimingData : AnalyticsDataClass
{
    public string TableName => "AudioGuideTiming";
    public float LogTime;
    public string AudioGuideName;
    public String State;

    public AudioGuideTimingData(string audioGuideName, String state)
    {
        LogTime = Time.time;
        AudioGuideName = audioGuideName;
        State = state;
    }

}
[Serializable]
public class QuestionsData : AnalyticsDataClass
{
    public string TableName => "QuestionsData";
    public float LogTime;
    public string Question;
    public string Answer1;
    public string Answer2;
    public string Answer3;
    public string ChosenAnswer;

    public QuestionsData(string question, string answer1, string answer2, string answer3, string chosenAnswer)
    {
        LogTime = Time.time;
        Question = question;
        Answer1 = answer1;
        Answer2 = answer2;
        Answer3 = answer3;
        ChosenAnswer = chosenAnswer;
    }
}

#endregion

public class TXRDataManager : TXRSingleton<TXRDataManager>
{
    // updated from TAUXRPlayer
    private bool exportEyeTracking = false;
    private bool exportFaceTracking = false;

    // automatically switched to true if not in editor.
    [SerializeField]
    private bool shouldExport = false;


    private AnalyticsWriter analyticsWriter;
    private DataContinuousWriter continuousWriter;
    private DataExporterFaceExpression faceExpressionWriter;

    #region Analytics Data Classes
    // declare pointers for all experience-specific analytics classes
    private AnalyticsLogLine logLine;
    private AudioGuideTimingData audioGuideTimingData;
    // write additional events here..


    #endregion

    #region Project Specific Analytics Reporters
    // Write here all the functions you'll want to use to report relevant data.
    public void ReportAudioGuideTiming(string audioGuideName, String state)
    {
        WriteAnalyticsToFile(new AudioGuideTimingData(audioGuideName, state));
    }
    public void ReportMultichoiceAnswer(string question, string answer1, string answer2, string answer3, string chosenAnswer)
    {
        WriteAnalyticsToFile(new QuestionsData(question, answer1, answer2, answer3, chosenAnswer));
    }


    // log a new string line with the time logged to TAUXR_Logs file.
    public void LogLineToFile(string line)
    {
        // creates a new instance of AnalyticsLogLine data class. In it's constructor, it gets the line and automatically assign Time.time to the log time.
        logLine = new AnalyticsLogLine(line);

        // tells the analytics writer to write a new line in file.
        WriteAnalyticsToFile(logLine);
    }

    #endregion

    private void WriteAnalyticsToFile(AnalyticsDataClass analyticsDataClass)
    {
        if (!shouldExport) return;

        analyticsWriter.WriteAnalyticsDataFile(analyticsDataClass);
    }

    void Start()
    {
        Init();
    }

    private void Init()
    {
        shouldExport = ShouldExportData();
        if (!shouldExport) return;

        exportEyeTracking = TXRPlayer.Instance.IsEyeTrackingEnabled;
        exportFaceTracking = TXRPlayer.Instance.IsFaceTrackingEnabled;

        analyticsWriter = new AnalyticsWriter();

        // for now, instead of making the whole interface in the datamanager, it will split between the different scripts.
        continuousWriter = GetComponent<DataContinuousWriter>();
        continuousWriter.Init(exportEyeTracking);

        if (exportFaceTracking)
        {
            faceExpressionWriter = GetComponent<DataExporterFaceExpression>();
            faceExpressionWriter.Init();
        }
    }

    // default data export on false in editor. always export on build.
    private bool ShouldExportData()
    {
        if (Application.isEditor && !shouldExport)
        {
            Debug.Log("Data Manager won't export data because it is running in editor. To export, manually enable ShouldExport");
        }
        return shouldExport || !Application.isEditor;
    }

    void FixedUpdate()
    {
        if (!shouldExport) return;

        continuousWriter.RecordContinuousData();

        if (exportFaceTracking)
        {
            faceExpressionWriter.CollectWriteDataToFile();
        }
    }

    private void OnApplicationQuit()
    {
        if (!shouldExport) return;

        analyticsWriter.Close();
        continuousWriter.Close();
        faceExpressionWriter.Close();
    }

}

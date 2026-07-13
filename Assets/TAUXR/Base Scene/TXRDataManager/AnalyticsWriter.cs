using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEngine;

// write analytics tables to separate csv files for each analytic type. Used in TAUXRDataManager.
public class AnalyticsWriter
{
    private Dictionary<string, StreamWriter> csvFiles = new Dictionary<string, StreamWriter>();
    private string dataPath;

    public AnalyticsWriter()
    {
        // Set the CSV folder path
        dataPath = Application.persistentDataPath;
        //dataPath = Path.Combine(Application.persistentDataPath, "AnalyticsEvents_" + TAUXRUtilities.GetFormattedDateTime(true));

        #region Create a new folder for all analytics events. Currenly not neccessary.
        /*
          // Create the folder for the CSV files if it doesn't exist
          if (!Directory.Exists(dataPath))
          {
              Directory.CreateDirectory(dataPath);
              Debug.Log($"Created a new data folder in: {dataPath}");
          }

          // Set permissions for the CSV folder
          try
          {
              string filePath = Path.Combine(dataPath, "permission_test.txt");
              using (StreamWriter writer = new StreamWriter(filePath))
              {
                  writer.WriteLine("test");
              }
              File.Delete(filePath);
          }
          catch (IOException ex)
          {
              Debug.LogError("Error setting permissions for CSV folder: " + ex.Message);
          }*/

        #endregion
    }

    // called from TAUXRDataManager on OnApplicationQuit
    public void Close()
    {
        // Close all the CSV files
        foreach (StreamWriter writer in csvFiles.Values)
        {
            writer.Close();
        }
    }

    // Called from TAUXRDataManager every time a new line is logged into a Analytics Table.
    public void WriteAnalyticsDataFile(AnalyticsDataClass dataClass)
    {

        string tableName = dataClass.TableName;

        // Check if a CSV file already exists for this event name
        if (!csvFiles.ContainsKey(tableName))
        {
            CreateNewDataFile(dataClass);
        }

        WriteLineInFile(dataClass);
    }

    private void CreateNewDataFile(AnalyticsDataClass dataClass)
    {
        string fileName = dataClass.TableName;

        // Create a new CSV file for this event name and add the field keys to the first line
        string csvFilePath = Path.Combine(dataPath, fileName + $"_{TAUXRUtilities.GetFormattedDateTime(true)}.csv");

        StreamWriter writer = new StreamWriter(csvFilePath, true);
        csvFiles[fileName] = writer;

        // keys are the members' name in the data class. All implement AnalyticsDataClass interface, therefore should have TableName member. We want to delete it because it won't appear as a field name.
        List<string> fieldNames = TAUXRUtilities.SerializeObject(dataClass).Keys.ToList();
        if (fieldNames.Contains("TableName"))       // -> ? maybe can just call fieldNames["TableName"]!=null ? would be more efficient? or maybe simply removing?
        {
            fieldNames.Remove("TableName");
        }
        else
        {
            Debug.LogError($"Tried to remove TableName from a data class but couldn't find a member with TableName name. Look at your Analytics Data classes under TAUXRDataManager and make sure they all have a string member called TableName");
        }

        string fieldLine = string.Join(",", fieldNames);

        writer.WriteLine(fieldLine);
        Debug.Log($"Created a new analytics table: {fileName}, fields are: {fieldLine}");
    }

    private void WriteLineInFile(AnalyticsDataClass dataClass)
    {
        string fileName = dataClass.TableName;

        // Add the field values to the corresponding CSV file
        Dictionary<string, string> lineData = TAUXRUtilities.SerializeObject(dataClass);
        if (lineData.ContainsKey("TableName"))
        {
            lineData.Remove("TableName");
        }
        else
        {
            Debug.LogError($"Tried to remove TableName from a data class but couldn't find a member with TableName name. Look at your Analytics Data classes under TAUXRDataManager and make sure they all have a string member called TableName");
        }

        string[] fieldValues = lineData.Values.ToArray();
        string fieldValuesLine = string.Join(",", fieldValues);

        csvFiles[fileName].WriteLine(fieldValuesLine);
        Debug.Log($"Line Added to {fileName}: {fieldValuesLine}");

        // flush every time to make sure the data is saved on the file.
        csvFiles[fileName].Flush();
    }

}
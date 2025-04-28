import pandas as pd
import glob
import os
import numpy as np

# Paths
continuous_data_folder = '/Users/yanasklar/Documents/TAU/Data/Continuous/'
logs_data_folder = "/Users/yanasklar/Documents/TAU/Data/Logs/"

# Define objects of interest
objects_of_interest = ["Braque", "Janco", "Klimt", "Picasso", "Pollock", "de Chirico", "van Dongen"]

# Get all participant files
file_list = glob.glob(os.path.join(continuous_data_folder, '*.csv'))
file_list.sort()  # Ensure consistent ordering of participants

# Sampling rate (assumed 60 Hz)
sampling_rate = 1 / 60  # Each row represents 1/60th of a second

def calculate_saccades(gaze_data):
    """Calculates saccade frequency based on sudden gaze shifts."""
    if len(gaze_data) < 2:
        return 0.0  # Avoid errors for very small segments
    gaze_shifts = np.sqrt(np.diff(gaze_data['Gaze_Yaw'])**2 + np.diff(gaze_data['Gaze_Pitch'])**2)
    saccade_count = np.sum(gaze_shifts > 2)  # Threshold for saccade detection
    total_time = len(gaze_data) * sampling_rate
    return round(saccade_count / total_time, 2)  # Saccades per second rounded to 2 decimal places

def interpret_engagement(saccade_rate):
    """Interprets engagement level based on saccade rate."""
    if saccade_rate <= 0.5:
        return "High Engagement"
    elif saccade_rate <= 1.5:
        return "Moderate Engagement"
    else:
        return "Low Engagement"

all_results = []

for file in file_list:
    try:
        # Load the participant's Continuous file
        df = pd.read_csv(file)
        participant_id = os.path.basename(file).split(".csv")[0][-3:]  # Extract participant ID
        
        # Load the corresponding Logs file
        logs_file_path = glob.glob(os.path.join(logs_data_folder, f"*{participant_id}.csv"))
        if not logs_file_path:
            print(f"No logs file found for participant {participant_id}. Skipping...")
            continue
        logs_df = pd.read_csv(logs_file_path[0], names=["LogTime", "LogText", "Extra"], dtype=str, engine="python", skiprows=1)

        # Extract timestamps from the logs
        if participant_id == "109":
            experiment_start_time = 129.0    
        experiment_start_time = logs_df.loc[logs_df['LogText'] == "Instructions board hidden Lets start the tour Instructions", 'LogTime'].astype(float).values
        demo_3_switch = logs_df.loc[logs_df['LogText'] == "Player exited the zone of van Dongen", 'LogTime'].astype(float).values
        demo_2_switch = logs_df.loc[logs_df['LogText'] == "Player exited the zone of de Chirico", 'LogTime'].astype(float).values

        # Ensure we have valid values
        experiment_start_time = experiment_start_time[0] if len(experiment_start_time) > 0 else None
        demo_3_switch = demo_3_switch[0] if len(demo_3_switch) > 0 else float('inf')
        demo_2_switch = demo_2_switch[0] if len(demo_2_switch) > 0 else float('inf')

        if experiment_start_time is None:
            print(f"Experiment start time not found for participant {participant_id}. Skipping...")
            continue

        # Filter the Continuous data to keep only data collected after experiment_start_time
        df["Time"] = df["Time"].astype(float)
        df = df[df["Time"] >= experiment_start_time]

        # Replace demo object names based on Time conditions
        df.loc[df["FocusedObject"] == "Demo Piece 4", "FocusedObject"] = "Janco"
        df.loc[df["FocusedObject"] == "Demo Piece 1", "FocusedObject"] = "Klimt"

        df.loc[(df["FocusedObject"] == "Demo Piece 3") & (df["Time"] < demo_3_switch), "FocusedObject"] = "van Dongen"
        df.loc[(df["FocusedObject"] == "Demo Piece 3") & (df["Time"] >= demo_3_switch), "FocusedObject"] = "de Chirico"

        df.loc[(df["FocusedObject"] == "Demo Piece 2") & (df["Time"] < demo_2_switch), "FocusedObject"] = "Braque"
        df.loc[(df["FocusedObject"] == "Demo Piece 2") & (df["Time"] >= demo_2_switch), "FocusedObject"] = "Picasso"

    except Exception as e:
        print(f"Error processing file {file}: {e}")
        continue

    # Initialize data storage for this participant
    participant_data = {}

    # Process each object separately
    for obj in objects_of_interest:
        obj_df = df[df['FocusedObject'] == obj]
        duration = round(len(obj_df) * sampling_rate, 2) if not obj_df.empty else 0.0
        saccade_rate = calculate_saccades(obj_df) if not obj_df.empty else 0.0
        engagement_level = interpret_engagement(saccade_rate)

        participant_data[f"{obj}_Duration"] = duration
        participant_data[f"{obj}_SaccadeRate"] = saccade_rate
        participant_data[f"{obj}_Engagement"] = engagement_level

    all_results.append((participant_id, participant_data))

    print(f"Participant {participant_id} processed successfully.")  # Confirmation message

# Convert to DataFrame
results_df = pd.DataFrame.from_dict(dict(all_results), orient='index')
results_df.index.name = "ID"

# Rank focus durations for each object
for obj in objects_of_interest:
    results_df[f"{obj}_Rank"] = results_df[f"{obj}_Duration"].rank(ascending=False, method="min").astype(int)

# Reorder columns to maintain grouping
ordered_columns = []
for obj in objects_of_interest:
    ordered_columns.extend([f"{obj}_Duration", f"{obj}_Rank", f"{obj}_SaccadeRate", f"{obj}_Engagement"])
results_df = results_df[ordered_columns]

# Save to CSV
results_df.to_csv("Eye_movements.csv")

print("Results saved to Eye_movements.csv")

import pandas as pd
import glob
import os

# Folder containing facial expression data
facial_data_folder = "/Users//yanasklar/Documents/TAU/Data/FaceExpression/"
logs_data_folder = "/Users//yanasklar/Documents/TAU/Data/Logs/"

# Get list of all CSV files in the facial expression folder
file_list = glob.glob(os.path.join(facial_data_folder, "*.csv"))

# Define emotion-to-AU mapping with weights
emotion_to_aus = {
    "joy": {'CheekRaiserL': 2.0, 'CheekRaiserR': 2.0, 'LipCornerPullerL': 2.5, 'LipCornerPullerR': 2.5},
    "sadness": {'InnerBrowRaiserL': 1.2, 'InnerBrowRaiserR': 1.2, 'BrowLowererL': 0.5, 'BrowLowererR': 0.5, 'LipCornerDepressorL': 3.0, 'LipCornerDepressorR': 3.0},
    "anger": {'BrowLowererL': 1.5, 'BrowLowererR': 1.5, 'LidTightenerL': 1.8, 'LidTightenerR': 1.8},
    "disgust": {'NoseWrinklerL': 2.0, 'NoseWrinklerR': 2.0, 'LipCornerDepressorL': 1.0, 'LipCornerDepressorR': 1.0},
    "surprise": {'JawDrop': 3.0, 'UpperLidRaiserL': 2.0, 'UpperLidRaiserR': 2.0, 'InnerBrowRaiserL': 1.2, 'InnerBrowRaiserR': 1.2}
}

# Function to calculate weighted emotion intensity
def calculate_intensity_weighted(max_values, aus_weights, min_threshold=0.1):
    intensity_sum = 0
    weight_sum = 0
    for au, weight in aus_weights.items():
        if au in max_values and max_values[au] > min_threshold:
            intensity_sum += max_values[au] * weight
            weight_sum += weight
    return round((intensity_sum / weight_sum) * 100, 2) if weight_sum > 0 else 0

all_results = []

# Process each file
for file in file_list:
    try:
        facial_data = pd.read_csv(file, on_bad_lines='skip', dtype=str)
        participant_id = file.split("/")[-1].split(".csv")[0][-3:]  # Extract participant ID
    except Exception as e:
        print(f"Error reading file {file}: {e}")
        continue

    logs_file_pattern = os.path.join(logs_data_folder, f"*{participant_id}.csv")
    logs_path = glob.glob(logs_file_pattern)
    if not logs_path:
        continue
    logs_path = logs_path[0]
    logs_data = pd.read_csv(logs_path, names=["LogTime", "LogText", "Extra"], dtype=str, engine="python", skiprows=1)

    entered_zone_logs = logs_data[logs_data['LogText'].str.contains(r"^(Player entered the zone of|Player is inside the zone of)", na=False, case=False, regex=True)]
    entered_zone_logs["Painter"] = entered_zone_logs["LogText"].str.replace("Player entered the zone of ", "", regex=False)
    entered_zone_logs["Painter"] = entered_zone_logs["Painter"].str.split(",").str[0]
    first_entry_per_painter = entered_zone_logs.groupby("Painter")["LogTime"].min().reset_index()
    first_entry_per_painter["LogTime"] = first_entry_per_painter["LogTime"].astype(float)
    first_entry_per_painter = first_entry_per_painter[~first_entry_per_painter["Painter"].str.contains("Demo Piece", case=False)]

    results = {"ID": participant_id}
    
    for _, row in first_entry_per_painter.iterrows():
        painting_name = row["Painter"]
        start_time = row["LogTime"]
        end_time = start_time + 2

        try:
            filtered_data = facial_data.loc[
                (facial_data['TimeFromStart'].astype(float) >= start_time) &
                (facial_data['TimeFromStart'].astype(float) <= end_time)
            ]
        except Exception as e:
            print(f"Error processing data for {file}: {e}")
            continue

        if filtered_data.empty:
            continue

        numeric_columns = filtered_data.iloc[:, 1:].apply(pd.to_numeric, errors='coerce')
        max_action_units = numeric_columns.max()

        emotion_intensities = {
            emotion: calculate_intensity_weighted(max_action_units, aus_weights)
            for emotion, aus_weights in emotion_to_aus.items()
        }

        positive_total = emotion_intensities["joy"] + emotion_intensities["surprise"]
        negative_total = emotion_intensities["sadness"] + emotion_intensities["anger"] + emotion_intensities["disgust"]
        valence = round(((positive_total - negative_total) / 100) * 50, 2)
        valence = max(min(valence, 50), -50)  # Ensure the result is in [-50, 50]

        clean_painting_name = painting_name.replace("Player entered the zone of ", "").replace("Player is inside the zone of ", "").strip()
        for emotion, intensity in emotion_intensities.items():
            results[f"{clean_painting_name} - {emotion}"] = intensity
        results[f"{clean_painting_name} - valence"] = valence

    all_results.append(results)
    print(f"Participant {participant_id} processed successfully.")

# Convert results to DataFrame
results_df = pd.DataFrame(all_results)

# Save results to CSV
results_df.to_csv("emotion_analysis_full.csv", index=False)
filtered_df = results_df.loc[:, ["ID"] + [col for col in results_df.columns if "valence" in col]]
filtered_df["ID"] = pd.to_numeric(filtered_df["ID"], errors='coerce')
filtered_df = filtered_df.sort_values(by="ID").reset_index(drop=True)
filtered_df.to_csv("emotion_analysis_valence.csv", index=False)

print("Emotion analysis completed. Results saved to emotion_analysis_results.csv")
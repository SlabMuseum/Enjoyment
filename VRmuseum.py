import pandas as pd

# Load the datasets
facial_data_path = "/Users//yanasklar/Documents/TAU/Data/FaceExpression/_FaceExpressionData_109.csv"
logs_data_path = "/Users//yanasklar/Documents/TAU/Data/Logs/TAUXR_Logs_109.csv"

facial_data = pd.read_csv(facial_data_path)
logs_data = pd.read_csv(logs_data_path, names=["LogTime", "LogText", "Extra"], dtype=str, engine="python", skiprows=1)

# Extract relevant log entries where the player entered a painter's zone
entered_zone_logs = logs_data[
    logs_data['LogText'].str.contains(r"^(Player entered the zone of|Player is inside the zone of)", na=False, case=False, regex=True)
]

# Extract the painter's name from the log text
entered_zone_logs["Painter"] = entered_zone_logs["LogText"].str.replace("Player entered the zone of ", "", regex=False)
entered_zone_logs["Painter"] = entered_zone_logs["Painter"].str.split(",").str[0]  # Remove extra info like zone radius

# Keep only the first instance of each painting being viewed
first_entry_per_painter = entered_zone_logs.groupby("Painter")["LogTime"].min().reset_index()

# Convert LogTime to numeric
first_entry_per_painter["LogTime"] = first_entry_per_painter["LogTime"].astype(float)

# Remove demo pieces from the dataset
first_entry_per_painter = first_entry_per_painter[~first_entry_per_painter["Painter"].str.contains("Demo Piece", case=False)]

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

# Process each painting seen
results = {}
for _, row in first_entry_per_painter.iterrows():
    painting_name = row["Painter"]
    start_time = row["LogTime"]
    end_time = start_time + 2  # 2-second window

    # Filter facial expression data within the viewing window
    filtered_data = facial_data.loc[
        (facial_data['TimeFromStart'] >= start_time) &
        (facial_data['TimeFromStart'] <= end_time)
    ]

    if filtered_data.empty:
        continue  # Skip paintings with no expression data

    # Convert numeric columns
    numeric_columns = filtered_data.iloc[:, 1:].apply(pd.to_numeric, errors='coerce')
    max_action_units = numeric_columns.max()

    # Compute weighted emotion intensities
    emotion_intensities = {
        emotion: calculate_intensity_weighted(max_action_units, aus_weights)
        for emotion, aus_weights in emotion_to_aus.items()
    }

    # Compute total emotion intensity as the maximum detected emotion (instead of sum)
    max_emotion_intensity = max(emotion_intensities.values())
    strongest_emotion = max(emotion_intensities, key=emotion_intensities.get)

    # Compute valence
    valence = round(50 + (max_emotion_intensity / 100) * 50 if strongest_emotion == "joy" else 50 - (max_emotion_intensity / 100) * 50, 2)

    # Store results
    for emotion, intensity in emotion_intensities.items():
        results[f"{painting_name} - {emotion}"] = intensity
    results[f"{painting_name} - valence"] = valence

# Convert results to DataFrame
results_df = pd.DataFrame([results])

# Save results to CSV
results_df.to_csv("emotion_analysis_results.csv", index=False)

print("Emotion analysis completed. Results saved to emotion_analysis_results.csv")
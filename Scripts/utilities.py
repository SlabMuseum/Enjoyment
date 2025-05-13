import os
import glob
import pandas as pd
import numpy as np

def assign_tiles(df):
    # Define bounding boxes in pixel coordinates: (xmin, xmax, ymin, ymax)
    # Each tuple = (x_min, x_max, y_min, y_max)
    tiles = {
        "Pollock":    (398, 774, 324, 691),
        "van Dongen": (388, 694, 892, 1200),
        "de Chirico": (388, 694, 1295, 1600),
        "Klimt":      (305, 686, 1873, 2243),
        "Braque":     (790, 1100, 892, 1200),
        "Picasso":    (790, 1100, 1295, 1600),
        "Janco":      (890, 1210, 1902, 2206),
    }

    # Initialize a column for tile labels
    df["tile_label"] = "None"

    # Assign tiles based on (x_pix, y_pix) falling within bounding boxes
    for label, (xmin, xmax, ymin, ymax) in tiles.items():
        condition = (df["x_pix"] >= xmin) & (df["x_pix"] <= xmax) & \
                    (df["y_pix"] >= ymin) & (df["y_pix"] <= ymax)
        df.loc[condition, "tile_label"] = label

    return df

def add_pixels(df, pixel_size):
    origin_x = df["Head_Position_x"].iloc[0]
    origin_y = df["Head_Position_Z"].iloc[0]
    anchor_x = 755
    anchor_y = 1800
    df["x_pix"] = anchor_x - ((df["Head_Position_x"] - origin_x) / pixel_size)
    df["y_pix"] = ((df["Head_Position_Z"] - origin_y) / pixel_size) + anchor_y
    return df

def deal_with_demo(file):
    logs_data_folder = "/Users/yanasklar/Documents/TAU/Data/Logs/"
    df = pd.read_csv(file, sep=",", engine="python")
    participant_id = os.path.basename(file).split(".csv")[0][-3:]  # Extract participant ID
    if participant_id == "143":
        print(df)


    # Load the corresponding Logs file
    logs_file_path = glob.glob(os.path.join(logs_data_folder, f"*{participant_id}.csv"))
    if not logs_file_path:
        print(f"No logs file found for participant {participant_id}. Skipping...")
    logs_df = pd.read_csv(logs_file_path[0], names=["LogTime", "LogText", "Extra"], dtype=str, engine="python", skiprows=1)

    # Extract timestamps from the logs
    if participant_id == "109":
        experiment_start_time = 129.0
    else:    
        experiment_start_time = logs_df.loc[logs_df['LogText'] == "Instructions board hidden Lets start the tour Instructions", 'LogTime'].astype(float).values
        experiment_start_time = experiment_start_time[0] if len(experiment_start_time) > 0 else None
    demo_3_switch = logs_df.loc[logs_df['LogText'] == "Player exited the zone of van Dongen", 'LogTime'].astype(float).values
    demo_2_switch = logs_df.loc[logs_df['LogText'] == "Player exited the zone of de Chirico", 'LogTime'].astype(float).values

    # Ensure we have valid values
    demo_3_switch = demo_3_switch[0] if len(demo_3_switch) > 0 else float('inf')
    demo_2_switch = demo_2_switch[0] if len(demo_2_switch) > 0 else float('inf')

    if experiment_start_time is None:
        print(f"Experiment start time not found for participant {participant_id}. Skipping...")
    
    # Filter the Continuous data to keep only data collected after experiment_start_time
    df["Time"] = df["Time"].astype(float)
    origin_row = df.iloc[[0]]
    filtered_rows = df[df["Time"] >= experiment_start_time]
    df = pd.concat([origin_row, filtered_rows], ignore_index=True)

    # Replace demo object names based on Time conditions
    df.loc[df["FocusedObject"] == "Demo Piece 4", "FocusedObject"] = "Janco"
    df.loc[df["FocusedObject"] == "Demo Piece 1", "FocusedObject"] = "Klimt"

    df.loc[(df["FocusedObject"] == "Demo Piece 3") & (df["Time"] < demo_3_switch), "FocusedObject"] = "van Dongen"
    df.loc[(df["FocusedObject"] == "Demo Piece 3") & (df["Time"] >= demo_3_switch), "FocusedObject"] = "de Chirico"

    df.loc[(df["FocusedObject"] == "Demo Piece 2") & (df["Time"] < demo_2_switch), "FocusedObject"] = "Braque"
    df.loc[(df["FocusedObject"] == "Demo Piece 2") & (df["Time"] >= demo_2_switch), "FocusedObject"] = "Picasso"
    return df, participant_id

# ========== EMOTIONS - FIRST IMPRESSION ========== #


def compute_weighted_emotion(df, weights_dict):
    return sum(df[au].max() * w for au, w in weights_dict.items() if au in df.columns)

def compute_fi_from_segment(segment):
    emotion_weights = {
        "joy": {'CheekRaiserL': 2.0, 'CheekRaiserR': 2.0, 'LipCornerPullerL': 2.5, 'LipCornerPullerR': 2.5},
        "sadness": {'InnerBrowRaiserL': 1.2, 'InnerBrowRaiserR': 1.2, 'BrowLowererL': 0.5, 'BrowLowererR': 0.5,
                    'LipCornerDepressorL': 3.0, 'LipCornerDepressorR': 3.0},
        "anger": {'BrowLowererL': 1.5, 'BrowLowererR': 1.5, 'LidTightenerL': 1.8, 'LidTightenerR': 1.8},
        "disgust": {'NoseWrinklerL': 2.0, 'NoseWrinklerR': 2.0, 'LipCornerDepressorL': 1.0, 'LipCornerDepressorR': 1.0},
        "surprise": {'JawDrop': 3.0, 'UpperLidRaiserL': 2.0, 'UpperLidRaiserR': 2.0, 'InnerBrowRaiserL': 1.2, 'InnerBrowRaiserR': 1.2}
    }
    joy = compute_weighted_emotion(segment, emotion_weights["joy"])
    surprise = compute_weighted_emotion(segment, emotion_weights["surprise"])
    sadness = compute_weighted_emotion(segment, emotion_weights["sadness"])
    anger = compute_weighted_emotion(segment, emotion_weights["anger"])
    disgust = compute_weighted_emotion(segment, emotion_weights["disgust"])
    
    pos = joy + surprise
    neg = sadness + anger + disgust
    fi = round(((pos - neg) / (pos + neg + 1e-6)) * 50, 2)
    return np.clip(fi, -50, 50)

def extract_valid_face_segment(face_df, cont_df, painting, sampling_rate, window_sec):
    cont_df = cont_df[cont_df["FocusedObject"] == painting].sort_values("Time").reset_index(drop=True)
    required_len = int(window_sec * sampling_rate)

    for start_idx in range(len(cont_df) - required_len + 1):
        segment = cont_df.iloc[start_idx:start_idx + required_len]
        if segment["Time"].iloc[-1] - segment["Time"].iloc[0] >= window_sec - (1 / sampling_rate):
            start_time = segment["Time"].iloc[0]
            end_time = start_time + window_sec
            face_segment = face_df[(face_df["Time"] >= start_time) & (face_df["Time"] <= end_time)]
            if not face_segment.empty:
                return face_segment
    return None

def rm_columns(df):
    return df.drop(columns=["Unnamed: 0"], errors="ignore")

def add_logs_col(df, subject_id, logs_path):
    logs_file = glob.glob(os.path.join(logs_path, f"*{subject_id}.csv"))
    if not logs_file:
        raise FileNotFoundError(f"No log file found for subject {subject_id}")
    logs_df = pd.read_csv(logs_file[0], names=["LogTime", "LogText", "Extra"], dtype=str, engine="python", skiprows=1)
    logs_df = logs_df.dropna()
    logs_df["LogTime"] = logs_df["LogTime"].astype(float)
    logs_df = logs_df.sort_values("LogTime")
    df["Time"] = df["Time"].astype(float)
    df = pd.merge_asof(df.sort_values("Time"), logs_df.sort_values("LogTime"), left_on="Time", right_on="LogTime", direction="backward")
    return df

# ========== SACCADE RATE ========== #


def interpret_engagement(saccade_rate):
    if saccade_rate <= 0.5:
        return "High Engagement"
    elif saccade_rate <= 1.5:
        return "Moderate Engagement"
    else:
        return "Low Engagement"

def calculate_saccades(gaze_data, sampling_rate):
    if len(gaze_data) < 2:
        return 0.0
    gaze_shifts = np.sqrt(np.diff(gaze_data['Gaze_Yaw'])**2 + np.diff(gaze_data['Gaze_Pitch'])**2)
    saccade_count = np.sum(gaze_shifts > 2)
    total_time = len(gaze_data) * (1 / sampling_rate)
    return round(saccade_count / total_time, 2) if total_time > 0 else 0.0

# ========== EMOTIONS ========== #


def analyze_dominant_emotions_by_tile(participant_id, sampling_rate=60, segment_duration=2):
    # Load data
    face_path = os.path.join(face_expression_folder, f"_FaceExpressionData_{participant_id}.csv")
    cont_path = f"/Users/yanasklar/Documents/TAU/Data/Trajectory/{participant_id}_processed.csv"
    if not os.path.exists(face_path) or not os.path.exists(cont_path):
        print(f"Missing data for participant {participant_id}.")
        return {}

    face_df = pd.read_csv(face_path, engine="python", on_bad_lines='skip')
    cont_df = pd.read_csv(cont_path)
    face_df["Time"] = face_df["TimeFromStart"].astype(float)
    cont_df["Time"] = cont_df["Time"].astype(float)

    # Define emotion-to-AU mapping
    emotion_to_aus = {
        "joy": {'CheekRaiserL': 2.0, 'CheekRaiserR': 2.0, 'LipCornerPullerL': 2.5, 'LipCornerPullerR': 2.5},
        "sadness": {'InnerBrowRaiserL': 1.2, 'InnerBrowRaiserR': 1.2, 'BrowLowererL': 0.5, 'BrowLowererR': 0.5, 'LipCornerDepressorL': 3.0, 'LipCornerDepressorR': 3.0},
        "anger": {'BrowLowererL': 1.5, 'BrowLowererR': 1.5, 'LidTightenerL': 1.8, 'LidTightenerR': 1.8},
        "disgust": {'NoseWrinklerL': 2.0, 'NoseWrinklerR': 2.0, 'LipCornerDepressorL': 1.0, 'LipCornerDepressorR': 1.0},
        "surprise": {'JawDrop': 3.0, 'UpperLidRaiserL': 2.0, 'UpperLidRaiserR': 2.0, 'InnerBrowRaiserL': 1.2, 'InnerBrowRaiserR': 1.2}
    }

    # Compute emotion scores
    for emotion, aus in emotion_to_aus.items():
        face_df[emotion] = face_df[list(aus.keys())].mul(pd.Series(aus), axis=1).sum(axis=1)

    # Compute bipolar valence
    face_df["valence"] = face_df["joy"] + face_df["surprise"] - (face_df["sadness"] + face_df["anger"] + face_df["disgust"])
    face_df["valence"] = face_df["valence"].clip(-100, 100).apply(lambda x: round((x / 100) * 50, 2))  # scale to [-50, 50]

    # Merge face data with tile data
    merged = pd.merge_asof(face_df.sort_values("Time"), cont_df.sort_values("Time"), on="Time", direction="backward")
    merged = merged[merged["tile_label"].notna()]

    tiles = merged["tile_label"].unique()
    segment_length = segment_duration * sampling_rate
    emotion_summary = {}

    for tile in tiles:
        tile_df = merged[merged["tile_label"] == tile]
        n_segments = int(np.ceil(len(tile_df) / segment_length))
        dominant_emotions = []

        for i in range(n_segments):
            segment = tile_df.iloc[i * segment_length: (i + 1) * segment_length]
            if segment.empty:
                continue

            emotion_means = segment[["joy", "sadness", "anger", "disgust", "surprise"]].mean()
            if emotion_means.max() < 0.5:  # Threshold for 'neutral'
                dominant_emotions.append("neutral")
            else:
                dominant_emotions.append(emotion_means.idxmax())

        emotion_summary[tile] = dominant_emotions
    return emotion_summary

def process_subject(df, participant_id, image_path, pixel_size, rect_w, rect_h, sampling_rate):
    df = rm_columns(df)
    df = add_logs_col(df, participant_id, "/Users/yanasklar/Documents/TAU/Data/Logs/")
    df = add_pixels(df, pixel_size)
    df = assign_tiles(df)

    df = df.drop(columns=["CoinPicked", "Trial"], errors="ignore")
    df.to_csv(os.path.join(save_path, f"{participant_id}_processed.csv"), index=False)

    # Tile-based metrics
    tiles = ["Pollock", "van Dongen", "de Chirico", "Klimt", "Braque", "Picasso", "Janco"]
    metrics = {}
    for tile in tiles:
        tile_df = df[df["tile_label"] == tile]
        gaze_df = tile_df[tile_df["FocusedObject"] == tile]
        duration_presence = round(len(tile_df) / sampling_rate, 2)
        duration_gaze = round(len(gaze_df) / sampling_rate, 2)
        saccade_rate = calculate_saccades(gaze_df, sampling_rate) if not gaze_df.empty else 0.0
        engagement = interpret_engagement(saccade_rate)

        metrics[f"{tile}_presence"] = duration_presence
        metrics[f"{tile}_gaze"] = duration_gaze
        metrics[f"{tile}_saccade_rate"] = saccade_rate
        metrics[f"{tile}_engagement"] = engagement

    # Add facial valence scores
    # valence_metrics = analyze_valence_by_tile(participant_id)
    valence_metrics = analyze_dominant_emotions_by_tile(participant_id)
    metrics.update(valence_metrics)
    return df, df["Time"].iloc[0], df["Time"].iloc[-1], metrics, valence_metrics

# ========== VISUALIZATION FUNCTIONS ========== #

def plot_trajectory_with_tiles_and_speed(df, image_path, save_path, id, emotion_summary, window_size=5, sampling_rate=60):
    background = Image.open(image_path)
    x = df["x_pix"].values
    y = df["y_pix"].values
    dx = np.diff(x)
    dy = np.diff(y)
    distances = np.sqrt(dx**2 + dy**2)
    speed = distances * sampling_rate
    smoothed_speed = convolve1d(speed, np.ones(window_size) / window_size, mode='reflect')

    points = np.array([x, y]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)

    norm = Normalize(vmin=np.percentile(smoothed_speed, 2), vmax=np.percentile(smoothed_speed, 98))
    cmap = plt.get_cmap('plasma')
    colors = cmap(norm(smoothed_speed))

    fig, ax = plt.subplots(figsize=(12, 8))
    ax.imshow(background)
    ax.add_collection(LineCollection(segments, colors=colors, linewidth=2))
    ax.scatter(x[0], y[0], color="green", label="Start", zorder=5)
    ax.scatter(x[-1], y[-1], color="blue", label="End", zorder=5)

    tiles = {
        "Pollock":    (398, 774, 324, 691),
        "van Dongen": (388, 694, 892, 1200),
        "de Chirico": (388, 694, 1295, 1600),
        "Klimt":      (305, 686, 1873, 2243),
        "Braque":     (790, 1100, 892, 1200),
        "Picasso":    (790, 1100, 1295, 1600),
        "Janco":      (890, 1210, 1902, 2206),
    }

    durations = df["tile_label"].value_counts() * (1 / sampling_rate)
    for label, (xmin, xmax, ymin, ymax) in tiles.items():
        ax.plot([xmin, xmax, xmax, xmin, xmin], [ymin, ymin, ymax, ymax, ymin], color="black", linewidth=1)
        duration = durations.get(label, 0.0)
        ax.text((xmin + xmax) / 2, ymax + 15, f"{duration:.1f}s", fontsize=10, color="black", ha="center", va="top")

    ax.set_title(f"Trajectory - Subject {id} (Colored by Smoothed Speed)")
    ax.axis("off")

    fi_df = pd.read_csv("emotion_analysis_valence.csv") # to get first impression 

    # Legend with gaze durations
    legend_labels = []
    participant_id_str = str(id)
    fi_row = None
    if fi_df is not None and participant_id_str in fi_df["ID"].astype(str).values:
        fi_row = fi_df[fi_df["ID"].astype(str) == participant_id_str].iloc[0]

    for label in tiles.keys():
        tile_df = df[df["tile_label"] == label]
        gaze_df = tile_df[tile_df["FocusedObject"] == label]
        gaze_duration = len(gaze_df) * (1 / sampling_rate)

        fi_columns = [col for col in fi_row.index if label in col]
        if fi_row is not None and fi_columns:
            fi_value = fi_row[fi_columns[0]]
            presence_duration = durations.get(label, 0.0)
            percentage = (gaze_duration / presence_duration) * 100 if presence_duration else 0
            label_text = f"{label}: {percentage:.0f}% gaze | FI: {fi_value}"
        else:
            presence_duration = durations.get(label, 0.0)
            percentage = (gaze_duration / presence_duration) * 100 if presence_duration else 0
            label_text = f"{label}: {percentage:.0f}% gaze | FI: {fi_value}"

        legend_labels.append(label_text)

    handles = [
        Line2D([0], [0], color='green', marker='o', linestyle='None', label='Start'),
        Line2D([0], [0], color='blue', marker='o', linestyle='None', label='End')
    ] + [Line2D([0], [0], color='none', label=label) for label in legend_labels]

    ax.legend(handles=handles, loc='upper right', fontsize=9, framealpha=0.3)

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, orientation="vertical", shrink=0.8)
    cbar.set_label("Speed (pixels/sec)")

     # ========== HEATMAP STRIP FOR EMOTIONS ==========
    if emotion_summary is not None:
        emotion_to_color = {
            "joy": "#2ca02c",
            "surprise": "#98df8a",
            "neutral": "#ffffff",
            "sadness": "#d62728",
            "anger": "#ff9896",
            "disgust": "#c93030"
        }

        for tile, (xmin, xmax, ymin, ymax) in tiles.items():
            if tile not in emotion_summary:
                continue
            emotions = emotion_summary[tile]
            segment_width = (xmax - xmin) / max(len(emotions), 1)
            heatmap_height = 13  
            heatmap_spacing = heatmap_height  # one full bar height as gap
            heatmap_y = ymax + heatmap_spacing

            for i, emotion in enumerate(emotions):
                color = emotion_to_color.get(emotion, "#ffffff")
                rect = plt.Rectangle(
                    (xmin + i * segment_width, heatmap_y),
                    segment_width,
                    heatmap_height,
                    linewidth=0,
                    edgecolor=None,
                    facecolor=color
                )
                ax.add_patch(rect)

    ax.set_title(f"Trajectory + Emotion Heatmap - Subject {id}")
    ax.axis("off")

    output_file = os.path.join(save_path, f"Subject_{id}_trajectory_smoothed_speed_tiles.png")
    plt.savefig(output_file, bbox_inches='tight')
    plt.close()
    print(f"Saved full plot for subject {id}")
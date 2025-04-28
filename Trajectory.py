import os
import glob
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from utilities import assign_tiles, add_pixels, deal_with_demo
from scipy.ndimage import convolve1d
from matplotlib.collections import LineCollection
from matplotlib.colors import Normalize
from matplotlib.lines import Line2D

# ========== PREPROCESSING FUNCTIONS ========== #

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

"""
def analyze_valence_by_tile(participant_id):
    face_path = f"/Users/yanasklar/Documents/TAU/Data/FaceExpression/_FaceExpressionData_{participant_id}.csv"
    cont_path = f"/Users/yanasklar/Documents/TAU/Data/Trajectory/{participant_id}_processed.csv"
    if not os.path.exists(face_path) or not os.path.exists(cont_path):
        print(f"Missing data for participant {participant_id}.")
        return {}

    face_df = pd.read_csv(face_path, engine="python", on_bad_lines='skip')
    cont_df = pd.read_csv(cont_path)
    face_df["Time"] = face_df["TimeFromStart"].astype(float)
    cont_df["Time"] = cont_df["Time"].astype(float)

    # Compute joy and surprise intensities
    face_df["joy"] = face_df[["CheekRaiserL", "CheekRaiserR", "LipCornerPullerL", "LipCornerPullerR"]].sum(axis=1)
    face_df["surprise"] = face_df[["InnerBrowRaiserL", "InnerBrowRaiserR", "OuterBrowRaiserL", "OuterBrowRaiserR", "JawDrop"]].sum(axis=1)

    # Compute valence based on joy
    face_df["valence"] = face_df["joy"].apply(lambda x: round(50 + (x / 100) * 50, 2))

    merged = pd.merge_asof(face_df.sort_values("Time"), cont_df.sort_values("Time"), on="Time", direction="backward")
    merged = merged[merged["tile_label"] != "None"]

    tiles = merged["tile_label"].unique()
    tiles = [t for t in merged["tile_label"].unique() if pd.notna(t)]
    output = {"ID": int(participant_id)}

    for tile in tiles:
        tile_df = merged[merged["tile_label"] == tile]
        output[f"{tile} - joy"] = round(tile_df["joy"].mean(), 2)
        output[f"{tile} - surprise"] = round(tile_df["surprise"].mean(), 2)
        output[f"{tile} - valence"] = round(tile_df["valence"].mean(), 2)

    return output
"""

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

        fi_columns = [col for col in fi_row.index if label in col and 'valence' in col.lower()]
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

# ========== MAIN SCRIPT ========== #

continuous_data_folder = '/Users/yanasklar/Documents/TAU/Data/Continuous/'
face_expression_folder = '/Users/yanasklar/Documents/TAU/Data/FaceExpression/'
logs_data_folder = "/Users/yanasklar/Documents/TAU/Data/Logs/"
save_path = '/Users/yanasklar/Documents/TAU/Data/Trajectory/'
image_path = 'top_view.png'
emotions = 'emotion_analysis_valence.csv'
pixel_size = 0.008660925 / 2.5
rectangle_width = 70
rectangle_height = 70.5
sampling_rate = 60

file_list = glob.glob(os.path.join(continuous_data_folder, '*.csv'))
file_list.sort()

all_metrics = []

audio_durations = {
    "Klimt": 87, "van Dongen": 81, "Braque": 75,
    "Pollock": 87, "de Chirico": 48, "Janco": 65, "Picasso": 60
}

fi_df = pd.read_csv("emotion_analysis_valence.csv") # to get first impression 

for file_path in file_list:
    try:
        df, participant_id = deal_with_demo(file_path)
        df, start_time, end_time, metrics, emotion_summary = process_subject(
            df, participant_id, image_path, pixel_size,
            rectangle_width, rectangle_height, sampling_rate
        )
        plot_trajectory_with_tiles_and_speed(df, image_path, save_path, id=participant_id, emotion_summary=emotion_summary)
        metrics["ID"] = participant_id
        for tile in audio_durations.keys():
            presence = metrics.get(f"{tile}_presence", 0.0)
            gaze = metrics.get(f"{tile}_gaze", 0.0)
            presence_audio = (presence / audio_durations[tile]) * 100 if audio_durations[tile] else 0
            gaze_percent = (gaze / presence) * 100 if presence else 0

            participant_row = fi_df[fi_df["ID"].astype(str) == str(participant_id)]
            if not participant_row.empty:
                matching_cols = [col for col in participant_row.columns if tile in col and 'valence' in col.lower()]
                if matching_cols:
                    metrics[f"{tile}_valence"] = round(float(participant_row.iloc[0][matching_cols[0]]), 2)
                else:
                    metrics[f"{tile}_valence"] = None
            else:
                metrics[f"{tile}_valence"] = None
            
            metrics[f"{tile}_emotions"] = ",".join(emotion_summary.get(tile, []))
            metrics[f"{tile}_presence_audio"] = round(presence_audio, 2)
            metrics[f"{tile}_gaze_percent"] = round(gaze_percent, 2)

        all_metrics.append(metrics)
        print(f"Participant {participant_id} processed successfully.")

    except Exception as e:
        print(f"Error processing participant {participant_id}: {e}")

tiles_order = ["Klimt", "van Dongen", "Braque", "Pollock", "de Chirico", "Janco", "Picasso"]
column_suffixes = [
    "presence", "presence_audio", "gaze", "gaze_percent",
    "saccade_rate", "engagement", "valence", "emotions"
]
final_column_order = ["ID"]
for tile in tiles_order:
    for suffix in column_suffixes:
        final_column_order.append(f"{tile}_{suffix}")

# Create and save DataFrame
summary_df = pd.DataFrame(all_metrics)

# Add missing columns if any were skipped
for col in final_column_order:
    if col not in summary_df.columns:
        summary_df[col] = None

summary_df = summary_df[final_column_order]
summary_df.to_csv(os.path.join(save_path, "Tile_Gaze_Engagement_Summary.csv"), index=False)
summary_df.to_csv("Tile_Gaze_Engagement_Summary.csv", index=False)
print("Saved summary CSV of gaze durations and engagement.")

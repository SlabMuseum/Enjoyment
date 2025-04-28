import pandas as pd
from scipy.stats import spearmanr
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# === Load the data ===
gaze_df = pd.read_csv("Tile_Gaze_Engagement_Summary.csv")
questionnaire_df = pd.read_csv("Questionnaire.csv")
gaze2 = gaze_df.copy()
gaze2.set_index("ID", inplace=True)
gaze2 = gaze2.T
gaze2.reset_index(inplace=True)
gaze2.rename(columns={"index": "Metric"}, inplace=True)
gaze2.to_csv("columns.csv", index=False)

# === Merge on participant ID ===
merged_df = pd.merge(gaze_df, questionnaire_df, on="ID", how="inner")

# === Define tiles and emotion weights ===
tiles = ["Klimt", "van Dongen", "Braque", "Pollock", "de Chirico", "Janco", "Picasso"]
metrics_to_correlate = ["presence_audio", "gaze_percent", "valence", "saccade_rate", "emotions"]

emotion_weights = {
    "joy": 1,
    "surprise": 1,
    "neutral": 0,
    "sadness": -0.5,
    "anger": -0.5,
    "disgust": -1
}

# === Compute correlations ===
results = []

for tile in tiles:
    row = {"Tile": tile}
    liking = merged_df[tile]  # Self-reported liking

    for metric in metrics_to_correlate:
        if metric == "emotions":
            # Extract dominant emotion and map to score
            emotion_series = merged_df[f"{tile}_emotions"].fillna("")
            dominant_emotions = emotion_series.apply(
                lambda s: max(s.split(","), key=s.split(",").count) if s else "neutral"
            )
            scores = dominant_emotions.map(emotion_weights).fillna(0)
        else:
            scores = merged_df[f"{tile}_{metric}"]

        # Compute Spearman correlation
        r, p = spearmanr(scores, liking)
        row[f"{metric}_r"] = round(r, 2) if not np.isnan(r) else None
        row[f"{metric}_p"] = round(p, 4) if not np.isnan(p) else None

    results.append(row)

# === Convert to DataFrame and display ===
correlation_df = pd.DataFrame(results)

# Prepare a matrix of p-values only (excluding emotions column headers)
pval_columns = [col for col in correlation_df.columns if col.endswith("_p")]
heatmap_data = correlation_df.set_index("Tile")[pval_columns]

# Create a custom color map: dark red for p ~ 0, red for p ~ 0.05, white for p > 0.1
from matplotlib.colors import LinearSegmentedColormap

colors = [(0.4, 0, 0), (1, 0, 0), (1, 1, 1)]  # dark red → red → white
pval_cmap = LinearSegmentedColormap.from_list("pval_red", colors, N=100)

# Plot heatmap
plt.figure(figsize=(10, 6))
sns.heatmap(
    heatmap_data,
    cmap=pval_cmap,
    vmin=0,
    vmax=0.1,
    annot=True,
    fmt=".3f",
    cbar_kws={"label": "p-value"},
    linewidths=0.5,
    linecolor='gray'
)

plt.title("Heatmap of p-values for VR Metrics vs Liking")
plt.ylabel("Tile")
plt.xlabel("VR Metric")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.show()

correlation_df.to_csv("VR_Liking_Correlations.csv", index=False)

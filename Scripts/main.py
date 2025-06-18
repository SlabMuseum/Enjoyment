import logging
import os
import pickle
from pathlib import Path
from typing import Dict, Any
from logger_config import configure_logging
from participant_data import *
from questionnaire_loader import load_questionnaire_data
from visualizations import *
import pandas as pd
from scipy.stats import spearmanr
from sklearn.tree import DecisionTreeClassifier, export_text, plot_tree
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt

# ---------------------configuration-------------------

# Set up logging configuration
logging_level = logging.INFO  # Set to DEBUG to see all messages, or INFO for less verbosity

# path configs - change accordingly                         # TODO set to relaive paths with known structure
root_data_path = r"/Users/yanasklar/Documents/TAU/Data" 
# root_data_path = r"/Users/yanasklar/Documents/TAU/TestData"  #3 participants
questionnaire_csv_path = r"/Users/yanasklar/GitHub/Enjoyment/res.csv" 

# ----------- main function - entry point --------------

def main() -> None:
    
    configure_logging(logging_level)

    participants = load_all_participants(root_data_path,  use_pkl=True)
    logging.info(f"Loaded {len(participants)} participants successfully.")

    questionnaire_df = load_questionnaire_data(questionnaire_csv_path)
    add_questionnaire_data_to_each_participant(participants, questionnaire_df)
    logging.info("Added questionnaire data to participants.")

    # summary table with all the stats per painting
    all_summaries = []
    for participant in participants.values():
        df = participant.generate_painting_summary()

        all_summaries.append(df)

    final_df = pd.concat(all_summaries, ignore_index=True)
    final_df.to_csv("Per_Painting_Summary.csv", index=False)

    # summary table with all the stats per participant
    participant_summary_list = []
    for participant in participants.values():
        summary = participant.generate_participant_summary(still_speed_threshold=0.01)
        participant_summary_list.append(summary)

    summary_df = pd.concat(participant_summary_list, ignore_index=True)
    summary_df = summary_df.sort_values(by="ParticipantID").reset_index(drop=True)
    summary_df.to_csv("Per_Participant_Summary.csv", index=False)


    # ---- visualizations ----
    """
    for participant_id, participant_data in participants.items():
        logging.info(f"Visualizing participant {participant_id}...")

        plot_trajectory_over_image_dual_view(participant_data, r"Top views/top_view_no_tiles_no_grid_isometric.png", save_file=True
                                    ,sampling_rate=60, window_size=5, close_plot=False)
        plot_trajectory_over_image(participant_data, r"Top views/top_view_no_tiles_no_grid_isometric.png", save_file=True
                                   ,sampling_rate=60, window_size=5, close_plot=False)
        logging.info(f"Visualization for participant {participant_id} completed.")


    plot_mean_trajectories_by_type(participants, image_path=r"Top views/top_view_no_tiles_no_grid_isometric.png")
    plot_gaze_per_painting(participants)
    plot_gaze_percent_per_painting(participants)
    plot_group_avg_emotions_bar(participants)
    plot_temporal_emotion_lines_by_painting(participants)
    """

    # ------ Analysis -------
    

    # Load the per-painting summary
    df = pd.read_csv("all_participant_painting_summary.csv")

    # Filter to only numeric columns (excluding ParticipantID)
    numeric_cols = df.select_dtypes(include='number').columns.tolist()
    numeric_cols = [col for col in numeric_cols if col != "ParticipantID"]
    subset = df[numeric_cols].dropna()
    target = "SelfReportedLiking"

    correlations = []     # Compute Spearman correlation
    for col in numeric_cols:
        if col == target:
            continue
        rho, p = spearmanr(subset[target], subset[col])
        correlations.append({
            "Feature": col,
            "SpearmanRho": round(rho, 3),
            "p_value": round(p, 4)
        })

    corr_df = pd.DataFrame(correlations)
    corr_df = corr_df.sort_values(by="SpearmanRho", key=abs, ascending=False)
    corr_df.to_csv("correlation_with_liking.csv", index=False)
    print("✅ Saved correlation results to correlation_with_liking.csv")

 # ------ Decision Tree Classifier -------

    # Load both summaries
    per_painting = pd.read_csv("all_participant_painting_summary.csv")
    per_participant = pd.read_csv("Per_Participant_Summary.csv")

    # Merge on ParticipantID
    merged = per_painting.merge(per_participant, on="ParticipantID", suffixes=("", "_Participant"))

    # Create binary target: Liked = 1 if SelfReportedLiking ≥ 6
    merged["Liked"] = (merged["SelfReportedLiking"] >= 6).astype(int)

    # Define columns to exclude
    exclude_columns = [
        "ParticipantID", "Painting", "SelfReportedLiking",
        "Audio_EmotionSequence", "FI_MaxEmotion", "Audio_DominantEmotion",
        "EngagementLevel"
    ]

    # Drop excluded and keep only numeric input features
    X = merged.drop(columns=[col for col in exclude_columns if col in merged.columns])
    X = X.select_dtypes(include="number").drop(columns=["Liked"], errors="ignore")
    y = merged["Liked"]

    # Split train/test
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Train decision tree
    clf = DecisionTreeClassifier(max_depth=5, random_state=42)
    clf.fit(X_train, y_train)
   
    # Compute feature importances
    importances = clf.feature_importances_
    features = X.columns
    importance_df = pd.DataFrame({
        "Feature": features,
        "Importance": importances
    }).sort_values(by="Importance", ascending=True)

    # Plot as horizontal bar chart
    plt.figure(figsize=(10, 8))
    plt.barh(importance_df["Feature"], importance_df["Importance"], color="skyblue")
    plt.xlabel("Importance")
    plt.title("Feature Importances (Decision Tree Classifier)")
    plt.grid(axis="x", linestyle="--", alpha=0.7)
    plt.tight_layout()
    plt.savefig("Tree importance.png")
    plt.show()

    # Print tree rules
    print("\n📋 Decision Tree Rules:\n")
    print(export_text(clf, feature_names=list(X.columns)))

    # Optional: plot the tree
    plt.figure(figsize=(16, 8))
    plot_tree(clf, feature_names=X.columns, class_names=["Not Liked", "Liked"], filled=True)
    plt.title("Decision Tree Classifier (without SelfReportedLiking as Feature)")
    plt.savefig("Tree.png")
    plt.show()

# ----------------- helper functions -------------------

def load_all_participants(datapath: str, use_pkl = True) -> Dict[int, MuseumVRParticipantData]:
    """
    Load all participant data from the specified directory.
    
    Each subfolder is assumed to be named by the participant ID.

    Args:
        datapath (str): Path to the directory containing participant folders.

    Returns:
        Dict[int, MuseumVRParticipantData]: Dictionary mapping participant IDs to their data.
    """
    participants = {}

    for folder in os.listdir(datapath):
        folder = folder.strip()
        folder_path = os.path.join(datapath, folder)


        if not os.path.isdir(folder_path):
            continue

        # === Step 1: Check if folder name is numeric ===
        try:
            participant_id = int(folder)
        except ValueError:
            logging.warning(f"Skipping non-numeric folder name: {folder}")
            continue

        # === Step 2: Try loading participant data ===
        try:
            logging.info(f"Loading participant {participant_id}...")
            data = MuseumVRParticipantData(participant_id=str(participant_id), data_path=folder_path, use_pkl=use_pkl)
            participants[participant_id] = data
        except Exception as e:
            logging.info(f"Failed to load participant {participant_id}: {e}")
            print(f"Skipping participant {participant_id} due to error: {e}")
            continue

    return participants

def add_questionnaire_data_to_each_participant(
    participants: Dict[int, MuseumVRParticipantData],
    questionnaire_df: pd.DataFrame
) -> None:
    """
    Add questionnaire data to each participant's data.

    Args:
        participants (Dict[int, MuseumVRParticipantData]): Dictionary mapping participant IDs to their data.
        questionnaire_df (pd.DataFrame): DataFrame containing questionnaire data.
    """
    for participant in participants.values():
        pid = int(participant.participant_id)
        if pid in questionnaire_df.index:
            participant.questionnaire_data = questionnaire_df.loc[pid]
        else:
            logging.warning(f"Participant {pid} not found in questionnaire data.")

# ------------------------------------------------------

if __name__ == "__main__":
    main()
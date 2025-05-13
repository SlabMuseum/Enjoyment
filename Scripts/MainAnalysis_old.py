
import logging
import os
import pickle
from pathlib import Path
from typing import Dict, Any
from ParticipantData import *
import utilities

root_data_path = r"/Users/yanasklar/Documents/TAU/Data" # change this to your data pathexit


def main() -> None:

    participants = load_all_participants(root_data_path)
    all_fi = []

    for id, data in participants.items():
        if data.continuous_data is None:
            logging.warning(f"Skipping participant {pid} due to missing continuous data")
            continue
        try:
            data.load_data()
            fi_scores = data.compute_fi()
            all_fi.append(fi_scores)
        except Exception as e:
            logging.error(f"Error processing participant {pid}: {e}")

    fi_df = pd.DataFrame(all_fi)
    fi_df.sort_values("ID").to_csv("emotion_analysis_valence.csv", index=False)

def load_all_participants(datapath: str) -> Dict[int, MuseumVRParticipantData]:
    """
    Load all participant data from the specified directory.
    
    Each subfolder is assumed to be named by the participant ID.

    Args:
        datapath (str): Path to the directory containing participant folders.

    Returns:
        Dict[int, MuseumVRParticipantData]: Dictionary mapping participant IDs to their data.
    """
    participants = {}

    # List all subdirectories
    for folder in os.listdir(root_data_path):
        folder_path = os.path.join(root_data_path, folder)
        if not os.path.isdir(folder_path):
            continue

        folder_name = os.path.basename(folder).strip()
        if not folder_name.isdigit():
            logging.warning(f"Skipping non-numeric folder name: {folder_name}")
            continue

        participant_id = folder_name
        try:
            data = MuseumVRParticipantData(participant_id=participant_id, data_path=folder_path)
            participants[participant_id] = data
        except Exception as e:
            logging.error(f"Failed to load participant {participant_id}: {e}")

    return participants



if __name__ == "__main__":
    main()
import logging
import os
import pickle
from pathlib import Path
from typing import Dict, Any
from logger_config import configure_logging
from participant_data import *
from questionnaire_loader import load_questionnaire_data
from visualizations import *

# ---------------------configuration-------------------

# Set up logging configuration
logging_level = logging.INFO  # Set to DEBUG to see all messages, or INFO for less verbosity

# path configs - change accordingly                         # TODO set to relaive paths with known structure
# root_data_path = r"D:\Yana-Analisys\Yanas-Museum-Data\Data" 
root_data_path = r"D:\Yana-Analisys\Yanas-Museum-Data\TestData"  #3 participants
questionnaire_csv_path = r"D:\Yana-Analisys\Enjoyment\res.csv" 

# ----------- main function - entry point --------------

def main() -> None:
    
    configure_logging(logging_level)

    #-- load participant data ----
    participants = load_all_participants(root_data_path,  use_pkl=False)
    logging.info(f"Loaded {len(participants)} participants successfully.")

    #-- load questionnaire data ----
    questionnaire_df = load_questionnaire_data(questionnaire_csv_path)
    add_questionnaire_data_to_each_participant(participants, questionnaire_df)
    logging.info("Added questionnaire data to participants.")

    # ---- visualizations ----
    for participant_id, participant_data in participants.items():
        logging.info(f"Visualizing participant {participant_id}...")

        plot_trajectory_over_image_dual_view(participant_data, r"Top views\top_view_no_tiles_no_grid_isometric.png", save_file=True
                                    ,sampling_rate=60, window_size=5, close_plot=True)
        # plot_trajectory_over_image(participant_data, r"Top views\top_view_no_tiles_no_grid_isometric.png", save_file=True
        #                            ,sampling_rate=60, window_size=5, close_plot=False)
        logging.info(f"Visualization for participant {participant_id} completed.")


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
            logging.error(f"Failed to load participant {participant_id}: {str(e)}")
            raise e

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
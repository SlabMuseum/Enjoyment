
import logging
import os
import pickle
from pathlib import Path
from typing import Dict, Any
from ParticipantData import *

root_data_path = r"D:\Yana-Analisys\Yanas-Museum-Data\Data" # change this to your data path


def main() -> None:

    participants = load_all_participants(root_data_path)

        
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
    for folder_name in os.listdir(datapath):
        folder_path = os.path.join(datapath, folder_name)

        if os.path.isdir(folder_path):
            try:
                participant_id = int(folder_name)  # Folder name must be integer ID
                participant_data = MuseumVRParticipantData(
                    participant_id=participant_id,
                    data_path=folder_path
                )
                participants[participant_id] = participant_data
            except ValueError:
                logging.warning(f"Skipping non-numeric folder name: {folder_name}")
            except Exception as e:
                logging.error(f"Error loading participant {folder_name}: {str(e)}")

    return participants


if __name__ == "__main__":
    main()
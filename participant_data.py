from abc import ABC, abstractmethod
from typing import Callable, Dict, List, Optional
import pandas as pd
import numpy as np
import pickle
import logging
import os
from io import StringIO

# region ------- Constants -------

# helper variables for the dataframes names
audioGuideTiming = 'AudioGuideTiming'
continuous = 'ContinuousData'
questions = 'QuestionsData'
logs = 'TAUXR_logs'

DEFAULT_COLLIDER_CSV = """name,pos_x,pos_y,pos_z,rot_x,rot_y,rot_z,bounds_x,bounds_y,bounds_z,bounds_size_x,bounds_size_y,bounds_size_z
Klimt,1.984,1.562,1.292,0,90,0,1.984,1.562,1.292,0.001000166,2.003331,1.521984
Pollock,0.5606009,1.619,-5.546001,0,180,0,0.5599192,1.617158,-5.546001,0.5911672,0.8356895,3.814697E-05
van Dongen,0.1109,1.592,-2.39115,0,270,0,0.1109,1.590215,-2.389365,0.001000062,0.6447186,0.492722
Braque,-0.109,1.63,-2.35815,0,90,0,-0.109,1.63,-2.35815,0.001000062,0.6753142,0.4546061
de Chirico,0.099,1.566,-1.51175,0,270,0,0.1,1.565238,-1.509465,0.01000005,0.5423059,0.440496
Janco,-2.031,1.718,0.961,0,270,0,-2.031,1.720237,0.9580168,0.000295639,0.9234918,0.9535842
Picasso,-0.106,1.607499,-1.506,0,270,0,-0.106,1.607499,-1.506,0.001000062,0.5955708,0.4894981
"""
default_art_piece_colliders = pd.read_csv(StringIO(DEFAULT_COLLIDER_CSV))

DEFAULT_TILE_POSITIONS_CSV = """name,bottom-left_x,bottom-left_z,top-left_x,top-left_z,top-right_x,top-right_z,bottom-right_x,bottom-right_z
Pollock,-0.05399996,-5.553,-0.05399996,-3.903,1.246,-3.903,1.246,-5.553
Braque,-1.405,-2.942,-1.405,-1.942,-0.105,-1.942,-0.105,-2.942
Picasso,-1.406,-1.95,-1.406,-0.9499998,-0.106,-0.9499998,-0.106,-1.95
de Chirico,0.11,-1.954,0.11,-0.9540002,1.41,-0.9540002,1.41,-1.954
van Dongen,0.109,-2.947,0.109,-1.947,1.409,-1.947,1.409,-2.947
Janco,-1.983,0.189,-1.983,1.489,-0.383,1.489,-0.383,0.189
Klimt,-0.32,0.199,-0.32,2.199,1.98,2.199,1.98,0.199
"""
default_tile_positions = pd.read_csv(StringIO(DEFAULT_TILE_POSITIONS_CSV))

# endregion

# ---------- Base class for participant data ----------

class BaseParticipantData(ABC):
    """
    Abstract base class for participant data.

    This class is defining the interface for participant data processing.
    It provides a structure for loading data, filtering it by trial time, and accessing trial data.
    
    It must contain 3 dataframes: continuous_data, face_data and trials_data.
    The first two are loaded from TAUXR template exported raw data, and an implemetation is suggested.
    trials_data is experiment specific and should be implemented by the user.
    """
    
    def __init__(self, participant_id: str, data_path: str):
        self.participant_id = participant_id
        self.data_path = data_path
        
        self.dataframes = None
        # self.continuous_data = None
        # self.face_data = None

        self.trials_data = None

    @abstractmethod
    def load_data(self) -> None:
        """Main function to load and process raw data into DataFrames. called from pipeline's DataLoader to instantiate the class."""
        
        self.dataframes: Dict[str, pd.DataFrame] = self._load_dataframes()
        self.continuous_data = self.dataframes['ContinuousData']        
        self.trials_data = self._extract_trials_data()
        # TODO : decide if this is done in the constructor or in the load_data method.

    @property
    @abstractmethod
    def _extract_trials_data(self) -> Optional[pd.DataFrame]:
        """
        Extract trial data from the loaded DataFrames.
        This method should be implemented in the derived class to extract trial data from the loaded DataFrames.

        Returns: trial data as a DataFrame. expected to be a DataFrame with columns:
                - 'TrialName': distinctive name of the trial (e.g., 'trial_1', 'trial_2', etc.)
                - 'StartTime': Start time of the trial 
                - 'EndTime': End time of the trial

                other colums (that you may need for your own analysis) can be added, but the general validation pipeline will not use them.

        ."""
        pass

    @abstractmethod
    def _filter_by_trial_time(self, df: pd.DataFrame, trial_name: str) -> pd.DataFrame: #is neccassary? should we only use the function in the utils?
        """
        Filters the input DataFrame to only include rows within the trial time window
        
        Returns:
            pd.DataFrame: Filtered DataFrame within trial time.
        """
        pass
    
    @abstractmethod
    def _load_dataframes(self) -> Dict[str, pd.DataFrame]:
        """ 
        Loads all CSV files for this participant into DataFrames.
        """
        pass

# ------- Experiment specific participant data -------

class MuseumVRParticipantData(BaseParticipantData):
    def __init__(self, participant_id: str, data_path: str, use_pkl: bool = True):
        super().__init__(participant_id, data_path) # initialize the base class
        self.intermidiate_output_folder = os.path.join(data_path, f'intermediate_{participant_id}')

        # Initialize experiment specific attributes
        self.questionnaire_data = None
        self.questionnaire_data_unranked = None
        self.tour_type = None
        
        # Load data and perform analysis
        self.load_data(use_pkl)
        self.fix_focus_object_with_colliders()
        
    # region ------- Data Loading -------

    def load_data(self, use_pkl:bool) -> None:
        """
        This method is called from the constructor to load and process raw data into DataFrames.
        """
        self.dataframes = self._load_dataframes(use_pkl)
        self.dataframes['QuestionsData'] = self._clean_questions_data(self.dataframes['QuestionsData'])
        self.tour_type = self._determine_tour_type()
        self.trials_data = self._extract_trials_data()

    def _load_dataframes(self, usePkl: bool) -> Dict[str, pd.DataFrame]:
        """
        A suggested implementaion to load all CSV files for this participant into DataFrames.
        Uses pickle caching for faster loading on subsequent runs.
        
        Returns:
            Dictionary mapping file names to DataFrames
        """
        # Path to the pickle file where dataframes will be saved/loaded
        pickle_path = os.path.join(self.data_path, 'dataframes.pkl')
            
        if usePkl:
           
            if os.path.exists(pickle_path):
                logging.info(f"Loading dataframes from pickle: {pickle_path}")
                try:
                    with open(pickle_path, 'rb') as f:
                        dfs = pickle.load(f)
                        dfs.pop("FaceExpressionData", None)
                        return dfs
                except Exception as e:
                    logging.error(f"Error loading pickle file: {str(e)}")
        
        # If pickle doesn't exist or failed to load, process the raw files
        logging.info("Processing raw data files")
        files = [f for f in os.listdir(self.data_path) if f.endswith('.csv')]
        dataframes = {}
        
        for file in files:
            try:
                # Extract the base name from the file (first part before underscore)
                base_name = [part for part in file.split('_') if part][0]
                file_path = os.path.join(self.data_path, file)
                
                if file.endswith('.csv'):
                    logging.debug(f"Loading CSV file: {file}")
                    if base_name == 'TAUXR':
                        # Special handling for TAUXR logs
                        df = self._load_TAUXR_logs_to_df(file_path)
                        base_name = 'TAUXR_logs' #fix the name
                    elif base_name == "FaceExpressionData":
                        continue
                    else:
                        if "ContinuousData" in file:
                            df = pd.read_csv(file_path, dtype={"FocusedObject": str}) # avoid dtype warning
                        else:
                            df = pd.read_csv(file_path)
                    
                # Standardize time column names
                if df.columns[0] in ['LogTime', 'Time', 'TimeFromStart']:
                    df.rename(columns={df.columns[0]: 'Time'}, inplace=True)
                    df['Time'] = pd.to_numeric(df['Time'], errors='coerce')
                
                #add the dataframe to the dictionary
                dataframes[base_name] = df

            except Exception as e:
                logging.error(f"Error loading file {file}: {str(e)}")
                raise e  # Re-raise the exception for further handling
            
        # Save the dataframes to a pickle file for future use
        if dataframes:
            try:
                with open(pickle_path, 'wb') as f:
                    pickle.dump(dataframes, f)
                logging.debug(f"Saved dataframes to pickle: {pickle_path}")
            except Exception as e:
                logging.error(f"Error saving pickle file: {str(e)}")
        
        return dataframes

    def _load_TAUXR_logs_to_df(self, filepath: str) -> pd.DataFrame:
        """
        Loads a TAUXR logs file where commas inside the LogText broke the CSV structure.
        Correctly splits the first column as Time, and merges the rest into LogText.
        
        Args:
            filepath (str): Path to the corrupted CSV file.

        Returns:
            pd.DataFrame: DataFrame with columns ['Time', 'LogText'] correctly parsed.
        """
        times = []
        texts = []

        # Open the file manually
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Skip header line if exists
        for line in lines[1:]:
            parts = line.strip().split(',', 1)  # Split only on the first comma
            if len(parts) == 2:
                time_part, text_part = parts
                try:
                    time_val = float(time_part)
                    times.append(time_val)
                    texts.append(text_part)
                except ValueError:
                    # Skip lines where Time is not a valid float
                    continue

        df = pd.DataFrame({
            'Time': times,
            'LogText': texts
        })

        return df

    def _clean_questions_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Cleans the QuestionsData dataframe, dropping duplicate items.
        """

        # === Step 1: Handle "Choose the type of experiment" ===
        is_experiment_type_question = df['Question'] == "Choose the type of experiment"
        experiment_type_questions = df[is_experiment_type_question]

        if experiment_type_questions.empty:
            raise ValueError("No 'Choose the type of experiment' question found.")

        # Take the first occurrence
        first_type_row = experiment_type_questions.iloc[0]

        # Check if the ChosenAnswer starts with "Type"
        if isinstance(first_type_row['ChosenAnswer'], str) and first_type_row['ChosenAnswer'].startswith("Type"):
            valid_experiment_type_df = pd.DataFrame([first_type_row])
        else:
            raise ValueError(f"First 'Choose the type of experiment' answer does not start with 'Type'. Found: {first_type_row['ChosenAnswer']}")

        # Remove all "Choose the type of experiment" rows from the original dataframe
        df = df[~is_experiment_type_question]

        # === Step 2: Handle "איזה מאפיין תרצו שיהיה ליצירה הבאה?" ===
        feature_question_text = "איזה מאפיין תרצו שיהיה ליצירה הבאה?"
        is_feature_question = df['Question'] == feature_question_text

        feature_questions = df[is_feature_question]

        if not feature_questions.empty:
            # Drop exact duplicates based on full row
            feature_questions_clean = feature_questions.drop_duplicates()
        else:
            feature_questions_clean = pd.DataFrame(columns=df.columns)

        # === Step 3: No other questions are kept ===
        # (we already removed non-feature questions here)

        # === Step 4: Concatenate cleaned dataframes ===
        dfs_to_concat = [df for df in [valid_experiment_type_df, feature_questions_clean] if not df.empty]
        cleaned_df = pd.concat(dfs_to_concat, ignore_index=True)

        # Sort by Time
        cleaned_df = cleaned_df.sort_values('Time').reset_index(drop=True)

        return cleaned_df

    def _determine_tour_type(self):
        """
        Determines the tour type from the participant's QuestionsData
        and sets self.tour_type as an integer (1, 2, or 3).
        """
        try:
            questions_df = self.dataframes['QuestionsData']

            if questions_df is None:
                raise ValueError("Questions data not loaded.")

            # Find the first "Choose the type of experiment" answer
            type_question = questions_df[
                questions_df['Question'] == "Choose the type of experiment"
            ]

            if type_question.empty:
                raise ValueError("No 'Choose the type of experiment' question found.")

            first_answer = type_question.iloc[0]['ChosenAnswer']

            if not isinstance(first_answer, str) or not first_answer.startswith("Type"):
                raise ValueError(f"Unexpected answer format: {first_answer}")

            # Extract the number
            tour_type = int(first_answer.replace("Type", "").strip())
            logging.debug(f"Tour type determined: {tour_type}")

        except Exception as e:
            logging.error(f"Error determining tour type: {str(e)}")
            tour_type = None  # fallback if error
        return tour_type

    def _extract_trials_data(self) -> Optional[pd.DataFrame]:
        """
        Extract trials StartTime and EndTime based on participant type (1, 2, 3).
        Trial timing rules:
        - Type 1 (Active):
            - Start: First trial after "Instructions board hidden Lets start the tour Instructions" (logs),
                    next trials after answering feature question.
            - End: When audio guide finishes.

        - Type 2 (Semi-Active):
            - Klimt, Pollock, van Dongen: same as Type 1.
            - de Chirico: ends on "Instructions board hidden End of active choice Instructions" (logs).
            - Janco, Picasso: start after previous audio finishes, end when their own audio finishes.

        - Type 3 (Passive):
            - Start: First trial after "Instructions board hidden Lets start the tour Instructions",
                    following trials after previous audio finishes.
            - End: When audio guide finishes.
        """
        try:
            logs_df = self.dataframes.get('TAUXR_logs')
            audio_df = self.dataframes.get('AudioGuideTiming')
            questions_df = self.dataframes.get('QuestionsData')

            if logs_df is None or audio_df is None or questions_df is None:
                raise ValueError("Missing one or more necessary dataframes.")

            # # Sort everything by time just in case
            # logs_df = logs_df.sort_values('Time')
            # audio_df = audio_df.sort_values('Time')
            # questions_df = questions_df.sort_values('Time')

            # Define tour order
            tour_order = ["Klimt", "Pollock", "van Dongen", "Braque", "de Chirico", "Janco", "Picasso"]

            

            # Find tour start
            if self.participant_id == "109":
                tour_start_time = 129.0
            else:
                start_instruction = logs_df[logs_df['LogText'] == "Instructions board hidden Lets start the tour Instructions"]
                if start_instruction.empty:
                    raise ValueError("Start of tour instruction not found in logs.")
                tour_start_time = start_instruction.iloc[0]['Time']

            trials = []
            current_start_time = tour_start_time

            for i, piece in enumerate(tour_order):
                trial = {"TrialName": piece, "StartTime": None, "EndTime": None}

                if self.tour_type == 1:  # Active
                    if piece == "Klimt":
                        trial["StartTime"] = current_start_time
                        audio_finish_time = self._find_audio_finish(piece)
                        trial["EndTime"] = audio_finish_time
                        feature_row = self._find_next_feature_question_answer(after_time=audio_finish_time)
                        current_start_time = feature_row['Time']
                    else:
                        trial["StartTime"] = current_start_time
                        audio_finish_time = self._find_audio_finish(piece)
                        trial["EndTime"] = audio_finish_time
                        if piece != "Picasso": # if its not the last question, then:
                            feature_row = self._find_next_feature_question_answer(after_time=audio_finish_time)
                            current_start_time = feature_row['Time']

                elif self.tour_type == 2:  # Semi-Active
                    if piece in ["Klimt", "Pollock", "van Dongen"]:
                        trial["StartTime"] = current_start_time
                        audio_finish_time = self._find_audio_finish(piece)
                        trial["EndTime"] = audio_finish_time
                        feature_row = self._find_next_feature_question_answer(after_time=current_start_time)
                        current_start_time = feature_row['Time']

                    elif piece == "de Chirico":
                        trial["StartTime"] = current_start_time
                        audio_finish_time = self._find_audio_finish(piece)
                        trial["EndTime"] = audio_finish_time
                        end_of_active = logs_df[
                            logs_df['LogText'] == "Instructions board hidden End of active choice Instructions"
                        ]
                        if end_of_active.empty:
                            raise ValueError("End of active choice instruction not found in logs.")
                        current_start_time = end_of_active.iloc[0]['Time']

                    else:  # Janco, Picasso
                        trial["StartTime"] = current_start_time
                        audio_finish_time = self._find_audio_finish(piece)
                        trial["EndTime"] = audio_finish_time
                        current_start_time = audio_finish_time

                elif self.tour_type == 3:  # Passive
                    trial["StartTime"] = current_start_time
                    audio_finish_time = self._find_audio_finish(piece)
                    trial["EndTime"] = audio_finish_time
                    current_start_time = audio_finish_time

                else:
                    raise ValueError(f"Unsupported tour type: {self.tour_type}")

                trials.append(trial)

            trials_df = pd.DataFrame(trials)

            # === New: Validation phase ===
            self._validate_trials_data(trials_df)

            return trials_df

        except Exception as e:
            logging.error(f"Error extracting trials: {str(e)}")
            raise e  # Re-raise the exception for further handling
            return None

    def _find_next_feature_question_answer(self, after_time: float) -> pd.Series:
        """
        Finds the next feature question answered after a given time.
        """
        questions_df = self.dataframes.get('QuestionsData')
        feature_question_text = "איזה מאפיין תרצו שיהיה ליצירה הבאה?"

        next_feature = questions_df[
            (questions_df['Question'] == feature_question_text) &
            (questions_df['Time'] > after_time)
        ].sort_values('Time')

        if next_feature.empty:
            raise ValueError(f"Error extracting trials for participant {self.participant_id}: No next feature question found after given time.")
        
        return next_feature.iloc[0]

    def _find_audio_finish(self, piece_name: str) -> float:
        """
        Finds the time when an audio guide finishes for a given piece.
        """
        audio_df = self.dataframes.get('AudioGuideTiming')

        finished_row = audio_df[
            (audio_df['AudioGuideName'].str.contains(piece_name, na=False)) &
            (audio_df['State'] == "Finished")
        ]

        if finished_row.empty:
            raise ValueError(f"No finished audio found for {piece_name}.")

        return finished_row.iloc[0]['Time']

    def _validate_trials_data(self, trials_df: pd.DataFrame):
        """
        Validates the extracted trials data - checks for NaN values and ensures StartTime < EndTime.
        """
        if trials_df.isnull().any().any():
            logging.warning("Trials data contains NaN values!")

        invalid_times = trials_df[trials_df['StartTime'] >= trials_df['EndTime']]
        if not invalid_times.empty:
            logging.warning(f"Some trials have StartTime >= EndTime:\n{invalid_times}")
        else:
            logging.debug("Trial times validated successfully.")
    
    
    # endregion 
    # region ------- Gaze correction -------

    def fix_focus_object_with_colliders(self, saveToCSV: bool = True):

        colliders = self._get_art_piece_colliders()
        
       
        # Create bounding boxes for real paintings
        painting_bounds = {}
        for _, row in colliders.iterrows():
            name = row['name']
            min_x = row['bounds_x'] - row['bounds_size_x'] / 2
            max_x = row['bounds_x'] + row['bounds_size_x'] / 2
            min_y = row['bounds_y'] - row['bounds_size_y'] / 2
            max_y = row['bounds_y'] + row['bounds_size_y'] / 2
            min_z = row['bounds_z'] - row['bounds_size_z'] / 2
            max_z = row['bounds_z'] + row['bounds_size_z'] / 2
            painting_bounds[name] = ((min_x, max_x), (min_y, max_y), (min_z, max_z))

        # Mapping of demo pieces to paintings
        demo_map = {
            "Demo Piece 1": ["Klimt"],
            "Demo Piece 2": ["Picasso", "Braque"],
            "Demo Piece 3": ["van Dongen", "de Chirico"],
            "Demo Piece 4": ["Janco"]
        }
        
         # Get start time of first real trial
        first_trial_start = self.trials_data.iloc[0]['StartTime']

        df = self.dataframes["ContinuousData"]
        

        def check_and_fix(row):
            focused_object = row["FocusedObject"]
            x, y, z = row["EyeGazeHitPosition_X"], row["EyeGazeHitPosition_Y"], row["EyeGazeHitPosition_Z"]
            if row["Time"] < first_trial_start:
                # Before first trial — keep original
                return focused_object
            
            if focused_object in demo_map and x != -1.0 and y != -1.0 and z != -1.0:
                for candidate in demo_map[focused_object]:
                    (min_x, max_x), (min_y, max_y), (min_z, max_z) = painting_bounds.get(candidate, ((0,0),(0,0),(0,0)))
                    if min_y <= y <= max_y and min_z <= z <= max_z: # Check if within bounds in the Y and Z axes 
                        return candidate
            return focused_object

        df["CorrectedFocusedObject"] = df.apply(check_and_fix, axis=1)
        # Update the DataFrame with the fixed FocusedObject
        if (saveToCSV):
            self.save_to_intermediate_folder_as_csv(df, "ContinuousData_CorrectedFocusedObject")

        self.dataframes["ContinuousData"] = df
    

    def _get_art_piece_colliders(self):
        #TODO  in next runs of the experiment replace with per run colliders csv, if not exist return the default one
        return default_art_piece_colliders

    
    # endregion

    # region ------- filtering -------
    def _filter_by_trial_time(self, df: pd.DataFrame, trial_name: str) -> pd.DataFrame:
            """
            Filters a dataframe to the timeframe of a given trial.
            """
            trial = self.trials_data[self.trials_data['TrialName'] == trial_name].iloc[0]
            start_time = trial['StartTime']
            end_time = trial['EndTime']

            return df[(df['Time'] >= start_time) & (df['Time'] <= end_time)]
    
    def _filter_by_tile_name(self, df: pd.DataFrame, tile_name: str) -> pd.DataFrame:
        """
        Filters a dataframe to only include rows where Head_Position_X, Head_Position_Z is within the bounds of a specific tile.

        Args:
            df (pd.DataFrame): DataFrame to filter.
            tile_name (str): Name of the tile to filter by.
        """
        tiles = default_tile_positions.set_index('name')

        if tile_name not in tiles.index:
            raise ValueError(f"Tile '{tile_name}' not found in default tile positions.")

        tile = tiles.loc[tile_name]

        # Extract all X and Z coordinates
        x_coords = [tile['bottom-left_x'], tile['top-left_x'], tile['top-right_x'], tile['bottom-right_x']]
        z_coords = [tile['bottom-left_z'], tile['top-left_z'], tile['top-right_z'], tile['bottom-right_z']]

        # Get bounding box
        min_x, max_x = min(x_coords), max(x_coords)
        min_z, max_z = min(z_coords), max(z_coords)
        continuous_df = self.dataframes['ContinuousData']
        filtered_continuous = continuous_df[
            (continuous_df['Head_Position_x'] >= min_x) & (continuous_df['Head_Position_x'] <= max_x) &
            (continuous_df['Head_Position_Z'] >= min_z) & (continuous_df['Head_Position_Z'] <= max_z)
            ]
            
        
        # Check if times align directly
        if df['Time'].isin(continuous_df['Time']).all():
            # Fast path: match directly
            filtered_df = df[df['Time'].isin(filtered_continuous['Time'])]
        else:
            # Slow path: match each row to nearest ContinuousData time
            # Create a map from ContinuousData time to tile-inclusion flag
            in_tile_times = set(filtered_continuous['Time'])

            # For each time in df, find closest in continuous_df, then check if it’s in tile
            continuous_times = continuous_df['Time'].values
            def is_in_tile(t):
                idx = np.argmin(np.abs(continuous_times - t))
                nearest_time = continuous_times[idx]
                return nearest_time in in_tile_times

            mask = df['Time'].apply(is_in_tile)
            filtered_df = df[mask]

        return filtered_df
        

    
    def _filter_by_trial_and_tile(self, df: pd.DataFrame, piece_name: str) -> pd.DataFrame:
        """
        Filters a dataframe by both trial time and tile name.
        
        Args:
            df (pd.DataFrame): DataFrame to filter.
            trial_name (str): Name of the trial to filter by.
            tile_name (str): Name of the tile to filter by.
        
        Returns:
            pd.DataFrame: Filtered DataFrame.
        """
        df = self._filter_by_trial_time(df, piece_name)
        df = self._filter_by_tile_name(df, piece_name)
        return df
    
    def _filter_by_audio_guide_time(self, df: pd.DataFrame, piece_name: str) -> pd.DataFrame:
        audio_df = self.dataframes.get('AudioGuideTiming')
        if audio_df is None:
            raise ValueError("AudioGuideTiming data not loaded.")
        
        # Define tour order
        tour_order = ["Klimt", "Pollock", "van Dongen", "Braque", "de Chirico", "Janco", "Picasso"]
        if piece_name not in tour_order:
            raise ValueError(f"Piece '{piece_name}' not found in tour order: {tour_order}")
        
        # Get the audio guide timing for the specific piece
        # Find the audio guide start time for the piece find the two rows where AudioGuideName contains the piece name
        audio_start = audio_df[audio_df['AudioGuideName'].str.contains(piece_name, na=False) & (audio_df['State'] == "Started")]
        audio_end = audio_df[audio_df['AudioGuideName'].str.contains(piece_name, na=False) & (audio_df['State'] == "Finished")]

        if audio_start.empty or audio_end.empty:
            raise ValueError(f"Audio guide timing for piece '{piece_name}' not found in AudioGuideTiming data.")
        
        start_time = audio_start.iloc[0]['Time']
        end_time = audio_end.iloc[0]['Time']

        # Filter the DataFrame by the audio guide timing
        filtered_df = df[(df['Time'] >= start_time) & (df['Time'] <= end_time)]
        return filtered_df
    
    # endregion
    # region ------- Gaze analysis -------
    
    def calculate_gaze_time(self, piece_name:str, fitering_function: Callable = None, sample_rate = 0.02) -> tuple[float, float]:
        """
        Calculates the percentage of time the participant gazed at a specific piece during thr filtered time.
        
        Args:
            piece_name (str): Name of the art piece to analyze.
            fitering_function (Callable, optional): Function to filter the DataFrame before calculation (tile, trial, bot)
        
        Returns:
            float: time gazed at the piece in seconds.
            float: Percentage of time gazed at the piece.
        """
        if self.dataframes is None:
            raise ValueError("Dataframes not loaded. Please load data first.")
        
        df = self.dataframes["ContinuousData"]

        # Filter the DataFrame if a filtering function is provided
        if fitering_function:
            df = fitering_function(df, piece_name)

        # Calculate total time in the filtered DataFrame
        total_time = df['Time'].max() - df['Time'].min()

        # Count the time gazed at the piece
        gazed_time = df[df['CorrectedFocusedObject'] == piece_name]['Time'].count() * sample_rate  # Assuming each row represents 20 ms (0.02 seconds)
        # Calculate the percentage
        if total_time == 0:
            return 0.0
        gazed_percent = (gazed_time / total_time) * 100
        return gazed_time, gazed_percent

    # endregion
    # region ------- Processing Data --------
    def save_to_intermediate_folder_as_csv(self, df: pd.DataFrame, filename: str):
        """
        Saves a DataFrame to the participant's intermediate output folder.
        
        Args:
            filename (str): Name of the file to save.
            df (pd.DataFrame): DataFrame to save.
        """
        if not os.path.exists(self.intermidiate_output_folder):
            os.makedirs(self.intermidiate_output_folder)
        
        filename = f"{self.participant_id}_{filename}.csv"
        output_path = os.path.join(self.intermidiate_output_folder, filename)
        df.to_csv(output_path, index=False)
        logging.info(f"Data saved to {output_path}")

    def get_per_painting_summary(self) -> pd.DataFrame:
        
        records = []
        for painting in default_tile_positions['name']:
            try:
                gazed_time, _  = self.calculate_gaze_time(piece_name=painting)
                _, gaze_percent = self.calculate_gaze_time(piece_name=painting, fitering_function = self._filter_by_audio_guide_time)

                
                records.append({
                    'Participant': self.participant_id,
                    'Painting': painting,
                    'GazeTime': round(gazed_time, 2),
                    'GazePercent': round(gaze_percent, 2),
                })

            except Exception as e:
                logging.info(f"Failed to compute summary for {painting} (Participant {self.participant_id}): {e}")
                continue

        return pd.DataFrame(records)

    def calculate_saccade_rate_and_engagement(self, df: pd.DataFrame, distance_threshold=0.01) -> tuple[float, str]:
        """
        Calculate saccade rate and engagement from gaze hit positions.

        Args:
            df (pd.DataFrame): Must contain 'EyeGazeHitPosition_X/Y/Z'
            time_column (str): Timestamp column
            distance_threshold (float): Euclidean distance in meters to count as a saccade

        Returns:
            (saccade_rate, engagement_level)
        """
        import numpy as np

        if df.empty or df.shape[0] < 2:
            print("empty")
            return 0.0, "undefined"

        # Extract gaze hit positions
        points = df[['EyeGazeHitPosition_X', 'EyeGazeHitPosition_Y', 'EyeGazeHitPosition_Z']].values

        # Compute Euclidean distances between consecutive gaze hits
        deltas = np.linalg.norm(np.diff(points, axis=0), axis=1)
        saccades = deltas > distance_threshold
        num_saccades = np.sum(saccades)

        duration_sec = df['Time'].max() - df['Time'].min()
        if duration_sec == 0 or np.isnan(duration_sec):
            return 0.0, "undefined"

        saccade_rate = num_saccades / duration_sec

        # Engagement rule
        if saccade_rate < 3:
            level = "high"
        elif saccade_rate <= 5:
            level = "moderate"
        else:
            level = "low"

        return round(saccade_rate, 2), level

    def generate_painting_summary(self) -> pd.DataFrame:
        """
        Generates a summary DataFrame for each painting including:
        - Self-reported liking
        - FI valence, max emotion, max intensity
        - Gaze time (full), gaze percent (audio period)
        - Avg valence & emotion during audio
        - Saccade rate and engagement during audio
        - Full emotion sequence during audio
        - Reaction time (latency to first fixation)
        """
        painting_list = ["Klimt", "Pollock", "van Dongen", "Braque", "de Chirico", "Janco", "Picasso"]
        summary_rows = []

        for painting in painting_list:
            row = {"ParticipantID": self.participant_id, "Painting": painting}

            # --- 0. Calculate TimeAtTheTile from trials_data ---
            try:
                trial = self.trials_data[self.trials_data["TrialName"] == painting].iloc[0]
                row["TimeAtTheTile"] = round(trial["EndTime"] - trial["StartTime"], 2)
                audio_df = self._filter_by_audio_guide_time(self.dataframes.get("AudioGuideTiming"), painting)
                audio_duration = audio_df["Time"].max() - audio_df["Time"].min()
                row["TileTimePercent_Audio"] = round((row["TimeAtTheTile"] / audio_duration) * 100, 2) if audio_duration > 0 else None
            except Exception:
                logging.info(f"Failed to calculate TimeAtTheTile for {self.participant_id} - {painting}")
                row["TimeAtTheTile"] = None

            # --- 1. Self-reported liking ---
            try:
                q_df = self.questionnaire_data
                painting_rating = q_df.get(painting)
                row["SelfReportedLiking"] = painting_rating
            except Exception:
                row["SelfReportedLiking"] = None

        
            # --- 3. Gaze Time and Gaze Percent ---
            try:
                gaze_time, _ = self.calculate_gaze_time(piece_name=painting, fitering_function=self._filter_by_trial_and_tile)
                row["GazeTime"] = round(gaze_time, 2)
            except Exception:
                row["GazeTime"] = None

            try:
                _, gaze_percent = self.calculate_gaze_time(piece_name=painting, fitering_function=self._filter_by_audio_guide_time)
                row["GazePercent_Audio"] = round(gaze_percent, 2)
            except Exception:
                row["GazePercent_Audio"] = None

            # --- 5. Saccade Rate and Engagement ---
            try:
                continuous_df = self._filter_by_audio_guide_time(self.dataframes["ContinuousData"], painting)
                saccade_rate, engagement = self.calculate_saccade_rate_and_engagement(continuous_df)
                row["SaccadeRate"] = saccade_rate
                row["EngagementLevel"] = engagement
            except Exception:
                logging.info(f"Skipping saccade rate for {self.participant_id} - {painting}")
                row.update({"SaccadeRate": None, "EngagementLevel": None})

            # --- 6. Reaction Time to Fixation ---
            try:
                trial = self.trials_data[self.trials_data["TrialName"] == painting].iloc[0]
                trial_start = trial["StartTime"]
                trial_end = trial["EndTime"]
                df = self.dataframes["ContinuousData"]
                df_trial = df[(df["Time"] >= trial_start) & (df["Time"] <= trial_end)]
                first_fixation = df_trial[df_trial["CorrectedFocusedObject"] == painting]
                if not first_fixation.empty:
                    reaction_time = first_fixation.iloc[0]["Time"] - trial_start
                    row["ReactionTime"] = round(reaction_time, 2)
                else:
                    row["ReactionTime"] = None
            except Exception:
                row["ReactionTime"] = None

            summary_rows.append(row)
        data = pd.DataFrame(summary_rows)
        #print(data)
        return data


    def generate_participant_summary(self, still_speed_threshold=0.005) -> pd.DataFrame:
        """
        Creates a summary of general behavior, emotion, movement, and questionnaire answers
        for the entire experiment (1 row per participant).
        """
        import numpy as np

        painting_list = ["Klimt", "Pollock", "van Dongen", "Braque", "de Chirico", "Janco", "Picasso"]
        general_questions = {
            "Q1_SatisfactionTour": "Please rate your overall satisfaction with the guided tour of the Minza Blumenthal collection.",
            "Q2_SatisfactionExplanations": "Please rate your satisfaction with the explanations about the artworks.",
            "Q3_VisitDuration": "Was the duration of the visit to your liking?",
            "Q4_WantMoreExplanations": "Would you like to hear more explanations of this kind about other works in the collection?",
            "Q5_VisitAgainThisMuseum": "Would you like to visit the museum again with such a guide?",
            "Q6_VisitOtherMuseums": "Would you like to visit other museums with similar guidance?",
            "Q7_RecommendFriends": "Would you recommend your friends to visit the collection accompanied by this type of audio guide?",
        }

        # Get painting-level summary
        painting_df = self.generate_painting_summary()
        row = {"ParticipantID": self.participant_id, "TourType": self.tour_type}

        # --- Painting-level aggregates ---
        row["AvgSelfReportedLiking"] = round(painting_df["SelfReportedLiking"].mean(), 2)
        row["AvgGazeTime"] = round(painting_df["GazeTime"].mean(), 2)
        row["AvgGazePercent_Audio"] = round(painting_df["GazePercent_Audio"].mean(), 2)
        row["AvgSaccadeRate"] = round(painting_df["SaccadeRate"].mean(), 2)

        # Engagement distribution
        engagement_counts = painting_df["EngagementLevel"].value_counts()
        row["Engagement_High"] = engagement_counts.get("high", 0)
        row["Engagement_Moderate"] = engagement_counts.get("moderate", 0)
        row["Engagement_Low"] = engagement_counts.get("low", 0)

        # --- Experiment time ---
        try:
            start = self.trials_data["StartTime"].min()
            end = self.trials_data["EndTime"].max()
            row["TotalExperimentTime"] = round(end - start, 2)
        except Exception:
            row["TotalExperimentTime"] = None

        # --- Movement speed ---
        try:
            df = self.dataframes["ContinuousData"]
            start_time = self.trials_data["StartTime"].min()
            df = df[df["Time"] >= start_time]

            coords = df[["Head_Position_x", "Head_Position_Z"]].values
            dx = np.diff(coords[:, 0])
            dz = np.diff(coords[:, 1])
            distances = np.sqrt(dx**2 + dz**2)
            time_deltas = np.diff(df["Time"].values)
            speeds = np.divide(distances, time_deltas, out=np.zeros_like(distances), where=time_deltas > 0)

            row["AvgSpeed"] = round(np.nanmean(speeds), 2)
            row["TotalDistance"] = round(np.sum(distances), 2)

            still_mask = speeds < still_speed_threshold
            move_mask = speeds >= still_speed_threshold
            row["TimeStill"] = round(np.sum(time_deltas[still_mask]), 2)
            row["TimeMoving"] = round(np.sum(time_deltas[move_mask]), 2)
        except Exception:
            row.update({"AvgSpeed": None, "TimeStill": None, "TimeMoving": None})

        # --- General questionnaire answers ---
        try:
            if isinstance(self.questionnaire_data, pd.Series):
                qdata = self.questionnaire_data
            else:
                qdata = pd.Series(dtype=object)

            scores = []
            for col, qtext in general_questions.items():
                val = qdata.get(qtext, None)
                row[col] = int(val)
                if isinstance(val, (int, float, np.integer, np.floating)):
                    scores.append(val)

            row["AvgGeneralRating"] = round(np.mean(scores), 2) if scores else None
        except Exception:
            for col in general_questions:
                row[col] = None
            row["AvgGeneralRating"] = None

        data = pd.DataFrame([row])
        #print(data)
        return data


#test:
if __name__ == "__main__":
    # Example usage
    participant_data = MuseumVRParticipantData(participant_id="113", data_path=r"D:\Yana-Analisys\Yanas-Museum-Data\Data\113")

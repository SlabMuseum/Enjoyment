from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import pandas as pd
import numpy as np
import pickle
import logging
import os
from face_analysis import *
from io import StringIO

# region ------- Constants -------

# helper variables for the dataframes names
audioGuideTiming = 'AudioGuideTiming'
continuous = 'ContinuousData'
face = 'FaceExpressionData'
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
        self.face_data = self.dataframes['FaceExpressionData']
        
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
    def __init__(self, participant_id: str, data_path: str):
        super().__init__(participant_id, data_path) # initialize the base class
        
        # Initialize experiment specific attributes
        self.questionnaire_data = None
        self.emotions_df = None
        self.tour_type = None
        
        # Load data and perform analysis
        self.load_data()
        self._offline_gaze_correction()  # Correct gaze data based on colliders positions
        #self.analyze_face_expressions() # TODO before the review
        self.emotions_df = self.calculate_emotions_df()
        self.first_impressions = self.calculate_first_impressions()

    # region ------- Data Loading -------

    def load_data(self) -> None:
        """
        This method is called from the constructor to load and process raw data into DataFrames.
        """
        self.dataframes = self._load_dataframes(False)
        self.dataframes['QuestionsData'] = self._clean_questions_data(self.dataframes['QuestionsData'])
        self.tour_type = self._determine_tour_type()
        self.trials_data = self._extract_trials_data()

    def _load_dataframes(self, usePkl=True) -> Dict[str, pd.DataFrame]:
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
                        return pickle.load(f)
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
    def _offline_gaze_correction(self):
        """
        Recalculates the gaze raycast from headset position and gaze direction to correct
        the 'FocusedObject' and 'EyeGazeHitPoint' values in the ContinuousData dataframe,
        based on the actual colliders' positions of the art pieces (hidden by the invisible demo pieces colliders).

        This replicates Unity’s logic:
        - Ray is cast from between the two eyes (approximated here as Head_Position_x/y/z - which is basically centerEyeAnchor on unity).
        - Direction is based on Gaze_Pitch and Gaze_Yaw.
        - Intersects with bounding boxes representing the artwork colliders.
        
        Adds new columns:
            - 'CorrectedFocusedObject': corrected name of the object intersected or original FocusedObject.
            - 'CorrectedEyeGazeHitPoint_X/Y/Z': corrected hit point, or original if no correction needed.
        """
        if self.dataframes is None:
            raise ValueError("Dataframes not loaded. Please load data first.")
        if self.trials_data is None or self.trials_data.empty:
            raise ValueError("No tour start time available for gaze correction.")
        
        df = self.dataframes["ContinuousData"]

        # Use fallback collider data if file isn't present
        colliders = self._get_art_piece_colliders()
        
        # Get start time of first real trial
        first_trial_start = self.trials_data.iloc[0]['StartTime']


        # Extract relevant columns
        eye_pitch = df["Gaze_Pitch"]
        eye_yaw = df["Gaze_Yaw"]
        head_x = df["Head_Position_x"]
        head_y = df["Head_Height"]
        head_z = df["Head_Position_Z"]
        time = df["Time"]

        corrected_objects = []
        corrected_hit_x = []
        corrected_hit_y = []
        corrected_hit_z = []

        for i in range(len(df)):
            if time.iloc[i] < first_trial_start:
                # Before first trial — keep original
                corrected_objects.append(df["FocusedObject"].iloc[i])
                corrected_hit_x.append(df["EyeGazeHitPosition_X"].iloc[i])
                corrected_hit_y.append(df["EyeGazeHitPosition_Y"].iloc[i])
                corrected_hit_z.append(df["EyeGazeHitPosition_Z"].iloc[i])
                continue

            origin = np.array([head_x.iloc[i], head_y.iloc[i], head_z.iloc[i]])
            forward = self._gaze_direction_from_yaw_pitch(eye_yaw.iloc[i], eye_pitch.iloc[i])

            hit_obj, hit_point = self._intersect_ray_with_colliders(origin, forward, colliders)

            if hit_obj is not None:
                corrected_objects.append(hit_obj)
                corrected_hit_x.append(hit_point[0])
                corrected_hit_y.append(hit_point[1])
                corrected_hit_z.append(hit_point[2])
            else:
                # No correction possible — keep original
                corrected_objects.append(df["FocusedObject"].iloc[i])
                corrected_hit_x.append(df["EyeGazeHitPosition_X"].iloc[i])
                corrected_hit_y.append(df["EyeGazeHitPosition_Y"].iloc[i])
                corrected_hit_z.append(df["EyeGazeHitPosition_Z"].iloc[i])

        df["CorrectedFocusedObject"] = corrected_objects
        df["CorrectedEyeGazeHitPoint_X"] = corrected_hit_x
        df["CorrectedEyeGazeHitPoint_Y"] = corrected_hit_y
        df["CorrectedEyeGazeHitPoint_Z"] = corrected_hit_z

        self.dataframes["ContinuousData"] = df

    def _intersect_ray_box(self, origin, direction, bounds_center, bounds_size):
        """
        Calculates intersection of a ray with an axis-aligned bounding box using the slab method.
        Returns the hit point if intersecting, otherwise None.
        """
        bounds_min = np.array(bounds_center) - np.array(bounds_size) / 2
        bounds_max = np.array(bounds_center) + np.array(bounds_size) / 2

        tmin = (bounds_min - origin) / direction
        tmax = (bounds_max - origin) / direction

        t1 = np.minimum(tmin, tmax)
        t2 = np.maximum(tmin, tmax)

        t_near = np.max(t1)
        t_far = np.min(t2)

        if t_near > t_far or t_far < 0:
            return None  # no intersection

        return origin + direction * t_near
    
    def _intersect_ray_with_colliders(self, origin: np.ndarray, direction: np.ndarray, colliders_df: pd.DataFrame):
        """
        Iterates over all artwork colliders and checks for intersection with the given ray.
        
        Args:
            origin (np.ndarray): The ray origin point (eye position).
            direction (np.ndarray): The ray direction (gaze).
            colliders_df (pd.DataFrame): DataFrame with collider info (center + size).
        
        Returns:
            Tuple[str, np.ndarray] or (None, None): Name of hit object and hit point if found, else None.
        """
        for _, row in colliders_df.iterrows():
            center = np.array([row['bounds_x'], row['bounds_y'], row['bounds_z']])
            size = np.array([row['bounds_size_x'], row['bounds_size_y'], row['bounds_size_z']])
            hit_point = self._intersect_ray_box(origin, direction, center, size)
            if hit_point is not None:
                return row['name'], hit_point

        return None, None

    def _gaze_direction_from_yaw_pitch(self, yaw_deg: float, pitch_deg: float) -> np.ndarray:
        """
        Converts gaze yaw and pitch angles (in degrees) into a 3D direction vector.

        Unity's forward is (0, 0, 1), yaw rotates around Y (vertical), and pitch rotates around X (sideways).
        So this mimics Unity's:
            Quaternion.Euler(pitch, yaw, 0) * Vector3.forward

        Parameters:
        - yaw_deg (float): Horizontal rotation in degrees (around Y axis)
        - pitch_deg (float): Vertical rotation in degrees (around X axis)

        Returns:
        - np.ndarray: Normalized 3D direction vector
        """
        yaw_rad = np.radians(yaw_deg)
        pitch_rad = np.radians(pitch_deg)

        # Calculate direction vector components
        x = np.sin(yaw_rad) * np.cos(pitch_rad)
        y = -np.sin(pitch_rad)
        z = np.cos(yaw_rad) * np.cos(pitch_rad)

        direction = np.array([x, y, z])
        return direction / np.linalg.norm(direction)

    def _get_art_piece_colliders(self):
        #TODO  in next runs of the experiment replace with per run colliders csv, if not exist return the default one
        return default_art_piece_colliders
    # endregion
    # region ------- Face analysis -------
    
    def analyze_face_expressions(self):  # TODO this function is before our review
        """
        Calculates emotion intensities and valence per artwork based on facial expression data.
        Results are saved to self.emotions_per_painting_df.
        """
    

        logs_df = self.dataframes.get('TAUXR_logs')
        face_df = self.dataframes.get('FaceExpressionData')

        if logs_df is None or face_df is None:
            raise ValueError("Missing required dataframes: TAUXR_logs or FaceExpressionData.")
        try:
            self.emotions_per_painting_df = calculate_emotion_intensities(face_df, logs_df)
            logging.debug(f"Analized emotions for participant {self.participant_id}")
        except Exception as e:
            logging.error(f"Error analyzing face expressions for participant {self.participant_id}: {str(e)}")
            raise e

    def calculate_emotions_df(self) -> pd.DataFrame:
        """
        separates face expression data to 2 seconds windows and calcultes
        emotion intensities and valence for each window.

        returns:
            pd.DataFrame: DataFrame with columns ['Time', 'EndTime', 'joy', 'sadness', 'anger', 'fear', 'disgust', 'surprise', 'valence']

        """
        face_df = self.dataframes.get('FaceExpressionData')
        
        # Initialize an empty dataframes to store results
        results = []

        start = face_df['Time'].min()
        end = face_df['Time'].max()

        # Iterate over the DataFrame in 2-second intervals
        for start_time in np.arange(start, end, 2.0):
            # Calculate the end time for the current window
            end_time = start_time + 2.0
            
            intensities = claculate_emotion_intensities_for_2_seconds_after_time(face_df, start_time)
            
            # calculate valence
            valence = get_valence_from_emotion_intensities(intensities)
            
            # Store results
            row = intensities.iloc[0]
            results.append({
                'Time': start_time,
                'EndTime': end_time,
                'joy': row['joy'],
                'sadness': row['sadness'],
                'anger': row['anger'],
                'disgust': row['disgust'],
                'surprise': row['surprise'],
                'valence': valence
            })

        return pd.DataFrame(results)

    
    def calculate_first_impressions(self) -> pd.DataFrame:
        # Prepare an empty list to collect rows
        first_impressions_list = []

        # Iterate over the trials
        for _, trial in self.trials_data.iterrows():
            painting_name = trial['TrialName']
            
            # Get the first impression emotions for the painting
            first_impression_max_emotion = self.get_first_impression_max_emotion(painting_name)
            
            if first_impression_max_emotion is None:
                logging.warning(f"No first impression data found for {painting_name} on participant {self.participant_id}.")
                continue

            # Add the current impression to the list
            first_impressions_list.append({
                'PaintingName': painting_name,
                'MaxEmotion': first_impression_max_emotion['MaxEmotion'],
                'MaxIntensity': first_impression_max_emotion['MaxIntensity'],
                'Valence': first_impression_max_emotion['Valence']
            })

        # Create a DataFrame from the list
        return pd.DataFrame(first_impressions_list, columns=['PaintingName', 'MaxEmotion', 'MaxIntensity', 'Valence'])

    def get_first_impression_window(self, painting_name: str) -> pd.DataFrame:

        """
        Get the first impression window for a specific painting.
        first impression is defined as the first full 2 seconds the participant was looking at the painting (regardless of the trial they're at).
        """
        continuous_df = self.dataframes.get('ContinuousData')

        # Finding windows of consecutive rows where CorrectedFocusedObject == painting_name
        windows = []
        current_window = []

        for index, row in continuous_df.iterrows():
            if row['CorrectedFocusedObject'] == painting_name:
                current_window.append(row)
            else:
                if current_window:  # Save the current window if it's not empty
                    windows.append(current_window)
                    
                    start_time = current_window[0]['Time']
                    end_time = current_window[-1]['Time']
                    
                    if end_time - start_time >= 2.0:
                        # create a DataFrame for the current window and take only the first 2 seconds
                        
                        window_df = pd.DataFrame(current_window)
                        window_df = window_df[(window_df['Time'] >= start_time) & (window_df['Time'] <= start_time + 2.0)]

                        return window_df
                    
                    current_window = []  # Reset the current window

        return None

    def get_first_impression_max_emotion(self, painting_name: str) -> pd.DataFrame:
        """
        Get the first impression max emotion for a specific painting.
        """
        face_df = self.dataframes.get('FaceExpressionData')

        # Get the first impression window
        first_impression_window = self.get_first_impression_window(painting_name)

        if first_impression_window is None:
            logging.warning(f"No first impression window found for {painting_name}.")
            return None

        window_start_time = first_impression_window.iloc[0]['Time']

        intensities = claculate_emotion_intensities_for_2_seconds_after_time(face_df, window_start_time)
        max_emotion, max_intensity = get_dominany_emotion_from_intensities(intensities)
        valence = get_valence_from_emotion_intensities(intensities)

        return pd.DataFrame({
            'PaintingName': [painting_name],
            'MaxEmotion': [max_emotion],
            'MaxIntensity': [max_intensity],
            'Valence': [valence]
        })

    # endregion
    #region -------filtering -------
    def _filter_by_trial_time(self, df: pd.DataFrame, trial_name: str) -> pd.DataFrame:
            """
            Filters a dataframe to the timeframe of a given trial.
            """
            trial = self.trials_data[self.trials_data['TrialName'] == trial_name].iloc[0]
            start_time = trial['StartTime']
            end_time = trial['EndTime']

            return df[(df['Time'] >= start_time) & (df['Time'] <= end_time)]
    
    
    # endregion
#test:
if __name__ == "__main__":
    # Example usage
    participant_data = MuseumVRParticipantData(participant_id="113", data_path=r"D:\Yana-Analisys\Yanas-Museum-Data\Data\113")

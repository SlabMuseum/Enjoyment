from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import pandas as pd
import pickle
import logging
import os
from face_analysis import calculate_emotion_intensities

# region ------- Constants -------

# helper variables for the dataframes names
audioGuideTiming = 'AudioGuideTiming'
continupus = 'ContinuousData'
face = 'FaceExpressionData'
questions = 'QuestionsData'
logs = 'TAUXR_logs'

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
        self.continuous_data = None
        self.face_data = None

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
        self.analyze_face_expressions()

    # region ------- Data Loading -------

    def load_data(self) -> None:
        """
        This method is called from the constructor to load and process raw data into DataFrames.
        """
        self.dataframes = self._load_dataframes()
        self.dataframes['QuestionsData'] = self._clean_questions_data(self.dataframes['QuestionsData'])
        self.tour_type = self._determine_tour_type()
        self.trial_data = self._extract_trials_data()

    def _load_dataframes(self) -> Dict[str, pd.DataFrame]:
        """
        A suggested implementaion to load all CSV files for this participant into DataFrames.
        Uses pickle caching for faster loading on subsequent runs.
        
        Returns:
            Dictionary mapping file names to DataFrames
        """
        # Path to the pickle file where dataframes will be saved/loaded
        pickle_path = os.path.join(self.data_path, 'dataframes.pkl')
        
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
                        feature_row = self._find_next_feature_question_answer(after_time=current_start_time)
                        trial["EndTime"] = feature_row['Time']
                        current_start_time = feature_row['Time']
                    else:
                        trial["StartTime"] = current_start_time
                        audio_finish_time = self._find_audio_finish(piece)
                        trial["EndTime"] = audio_finish_time
                        current_start_time = audio_finish_time

                elif self.tour_type == 2:  # Semi-Active
                    if piece in ["Klimt", "Pollock", "van Dongen"]:
                        trial["StartTime"] = current_start_time
                        feature_row = self._find_next_feature_question_answer(after_time=current_start_time)
                        trial["EndTime"] = feature_row['Time']
                        current_start_time = feature_row['Time']

                    elif piece == "de Chirico":
                        trial["StartTime"] = current_start_time
                        end_of_active = logs_df[
                            logs_df['LogText'] == "Instructions board hidden End of active choice Instructions"
                        ]
                        if end_of_active.empty:
                            raise ValueError("End of active choice instruction not found in logs.")
                        trial["EndTime"] = end_of_active.iloc[0]['Time']
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
        Validates the extracted trials data.
        """
        if trials_df.isnull().any().any():
            logging.warning("Trials data contains NaN values!")

        invalid_times = trials_df[trials_df['StartTime'] >= trials_df['EndTime']]
        if not invalid_times.empty:
            logging.warning(f"Some trials have StartTime >= EndTime:\n{invalid_times}")
        else:
            logging.debug("Trial times validated successfully.")
    
    def _filter_by_trial_time(self, df: pd.DataFrame, trial_name: str) -> pd.DataFrame:
            """
            Filters a dataframe to the timeframe of a given trial.
            """
            trial = self.trial_data[self.trial_data['TrialName'] == trial_name].iloc[0]
            start_time = trial['StartTime']
            end_time = trial['EndTime']

            return df[(df['Time'] >= start_time) & (df['Time'] <= end_time)]

    # endregion 
    # region ------- Face analysis -------
    
    def analyze_face_expressions(self):
        """
        Calculates emotion intensities and valence per artwork based on facial expression data.
        Results are saved to self.emotions_df.
        """
        from face_analysis import calculate_emotion_intensities

        logs_df = self.dataframes.get('TAUXR_logs')
        face_df = self.dataframes.get('FaceExpressionData')

        if logs_df is None or face_df is None:
            raise ValueError("Missing required dataframes: TAUXR_logs or FaceExpressionData.")
        try:
            self.emotions_df = calculate_emotion_intensities(face_df, logs_df)
            logging.debug(f"Analized emotions for participant {self.participant_id}")
        except Exception as e:
            logging.error(f"Error analyzing face expressions for participant {self.participant_id}: {str(e)}")
            raise e

    # endregion

#test:
if __name__ == "__main__":
    # Example usage
    participant_data = MuseumVRParticipantData(participant_id="113", data_path=r"D:\Yana-Analisys\Yanas-Museum-Data\Data\113")

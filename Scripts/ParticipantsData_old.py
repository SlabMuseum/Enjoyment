from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import pandas as pd
import pickle
import logging
import os
from utilities import *

# helper variables for the dataframes names
audioGuideTiming = 'AudioGuideTiming'
continupus = 'ContinuousData'
face = 'FaceExpressionData'
questions = 'QuestionsData'
logs = 'TAUXR_logs'




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

        self.trial_data = None

    """@abstractmethod
    def load_data(self) -> None:
        # Main function to load and process raw data into DataFrames. called from pipeline's DataLoader to instantiate the class.
        
        self.dataframes: Dict[str, pd.DataFrame] = self._load_dataframes()
        self.continuous_data = self.dataframes['ContinuousData']
        self.face_data = self.dataframes['FaceExpressionData']
        
        self.trial_data = self._extract_trials_data()
        # TODO : decide if this is done in the constructor or in the load_data method.
    """

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


class MuseumVRParticipantData(BaseParticipantData):
    def __init__(self, participant_id: str, data_path: str):
        super().__init__(participant_id, data_path)
        self.load_data()
        self.dataframes['QuestionsData'] = self._clean_questions_data(self.dataframes['QuestionsData'])
        self.tour_type = self._determine_tour_type()  # 'active', 'semi-active', 'passive' as an integer (1, 2, or 3)
        self.trial_data = self._extract_trials_data()

    def load_data(self):
        self.dataframes = self._load_dataframes()

        self.face_data = self.dataframes.get("FaceExpressionData")
        if self.face_data is not None and "TimeFromStart" in self.face_data.columns:
            self.face_data = self.face_data.rename(columns={"TimeFromStart": "Time"})
        self.logs_data = self.dataframes.get("TAUXR_logs")
        if self.logs_data is not None and "LogTime" in self.logs_data.columns:
                self.logs_data = self.logs_data.rename(columns={"LogTime": "Time"})
        self.questionnaire = self.dataframes.get("QuestionsData")
        if self.questionnaire is not None and "LogTime" in self.questionnaire.columns:
            self.questionnaire = self.questionnaire.rename(columns={"LogTime": "Time"})
        self.audio_guide = self.dataframes.get("AudioGuideTiming")
        if self.audio_guide is not None and "LogTime" in self.audio_guide.columns:
            self.audio_guide = self.audio_guide.rename(columns={"LogTime": "Time"})

        # Process ContinuousData after using logs
        raw_continuous_df = self.dataframes.get("ContinuousData")

        if raw_continuous_df is None:
            logging.error(f"ContinuousData missing for participant {self.participant_id}")
            self.continuous_data = None
            return

        logs_df = self.logs_data
        expected_cols = ["Time", "LogText", "Extra"]
        num_cols = len(self.logs_data.columns)

        if num_cols <= len(expected_cols):
            self.logs_data.columns = expected_cols[:num_cols]
        else:
            logging.warning(f"Too many columns in TAUXR_logs for participant {self.participant_id}")        
        logs_df["Time"] = logs_df["Time"].astype(float)

        if self.participant_id == "109":
            experiment_start_time = 129.0
        else:
            match = logs_df.loc[
                logs_df["LogText"] == "Instructions board hidden Lets start the tour Instructions", "Time"
            ].astype(float).values
            experiment_start_time = match[0] if len(match) > 0 else None

        demo_3_switch = logs_df.loc[
            logs_df["LogText"] == "Player exited the zone of van Dongen", "Time"
        ].astype(float).values
        demo_2_switch = logs_df.loc[
            logs_df["LogText"] == "Player exited the zone of de Chirico", "Time"
        ].astype(float).values

        demo_3_switch = demo_3_switch[0] if len(demo_3_switch) > 0 else float('inf')
        demo_2_switch = demo_2_switch[0] if len(demo_2_switch) > 0 else float('inf')

        if experiment_start_time is None:
            logging.warning(f"Experiment start time not found for participant {self.participant_id}")
            self.continuous_data = None
            return

        raw_continuous_df["Time"] = raw_continuous_df["Time"].astype(float)
        origin_row = raw_continuous_df.iloc[[0]]
        filtered_rows = raw_continuous_df[raw_continuous_df["Time"] >= experiment_start_time]
        df = pd.concat([origin_row, filtered_rows], ignore_index=True)

        # Rename demo objects
        df.loc[df["FocusedObject"] == "Demo Piece 4", "FocusedObject"] = "Janco"
        df.loc[df["FocusedObject"] == "Demo Piece 1", "FocusedObject"] = "Klimt"
        df.loc[(df["FocusedObject"] == "Demo Piece 3") & (df["Time"] < demo_3_switch), "FocusedObject"] = "van Dongen"
        df.loc[(df["FocusedObject"] == "Demo Piece 3") & (df["Time"] >= demo_3_switch), "FocusedObject"] = "de Chirico"
        df.loc[(df["FocusedObject"] == "Demo Piece 2") & (df["Time"] < demo_2_switch), "FocusedObject"] = "Braque"
        df.loc[(df["FocusedObject"] == "Demo Piece 2") & (df["Time"] >= demo_2_switch), "FocusedObject"] = "Picasso"

        self.continuous_data = df

        if self.participant_id == "143":
            print(self.face_data)


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
        df_map = {}
        
        try:
            for fname in os.listdir(self.data_path):
                full_path = os.path.join(self.data_path, fname)

                if not fname.endswith(".csv"):
                    continue

                if "FaceExpressionData" in fname:
                    df_map["FaceExpressionData"] = pd.read_csv(full_path, on_bad_lines='skip', sep=",", engine="python")
                elif "ContinuousData" in fname:
                    df_map["ContinuousData"] = pd.read_csv(full_path, on_bad_lines='skip', sep=",", engine="python")
                elif "TAUXR_Logs" in fname:
                    df_map["TAUXR_logs"] = pd.read_csv(full_path)
                elif "QuestionsData" in fname:
                    df_map["QuestionsData"] = pd.read_csv(full_path)
                elif "AudioGuideTiming" in fname:
                    df_map["AudioGuideTiming"] = pd.read_csv(full_path)
        except Exception as e:
            logging.error(f"Failed loading data for {self.participant_id}: {e}")
        return df_map
        
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
        frames = [df for df in [valid_experiment_type_df, feature_questions_clean] if not df.empty and not df.isna().all(axis=None)]
        cleaned_df = pd.concat(frames, ignore_index=True)
        # cleaned_df = pd.concat([valid_experiment_type_df, feature_questions_clean], ignore_index=True)

        # Sort by Time
        cleaned_df = cleaned_df.sort_values('Time').reset_index(drop=True)

        return cleaned_df

    def _determine_tour_type(self):
        """
        Determines the tour type from the participant's QuestionsData
        and sets self.tour_type as an integer (1, 2, or 3).
        """
        try:
            questions_df = self.questionnaire

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
            logs_df = self.logs_data
            audio_df = self.audio_guide
            questions_df = self.questionnaire

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
            if self.participant_id == "109":
                tour_start_time = 129.0

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
        questions_df = self.questionnaire
        feature_question_text = "איזה מאפיין תרצו שיהיה ליצירה הבאה?"

        next_feature = questions_df[
            (questions_df['Question'] == feature_question_text) &
            (questions_df['Time'] > after_time)
        ].sort_values('Time')

        if next_feature.empty:
            raise ValueError("No next feature question found after given time.")
        
        return next_feature.iloc[0]

    def _find_audio_finish(self, piece_name: str) -> float:
        """
        Finds the time when an audio guide finishes for a given piece.
        """
        audio_df = self.audio_guide

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
            logging.info("Trial times validated successfully.")
    
    def _filter_by_trial_time(self, df: pd.DataFrame, trial_name: str) -> pd.DataFrame:
            """
            Filters a dataframe to the timeframe of a given trial.
            """
            trial = self.trial_data[self.trial_data['TrialName'] == trial_name].iloc[0]
            start_time = trial['StartTime']
            end_time = trial['EndTime']

            return df[(df['Time'] >= start_time) & (df['Time'] <= end_time)]

    def compute_fi(self) -> Dict[str, float]:

        paintings = ["Klimt", "van Dongen", "Braque", "Pollock", "de Chirico", "Janco", "Picasso"]
        result = {"ID": self.participant_id}

        for painting in paintings:
            try:
                if self.face_data is None or self.continuous_data is None:
                    logging.warning(f"Missing data for participant {self.participant_id}")
                    return {"ID": self.participant_id}
                segment = extract_valid_face_segment(
                    self.face_data, self.continuous_data, painting, sampling_rate=60, window_sec=2
                )
                if segment is not None:
                    result[painting] = compute_fi_from_segment(segment)
                else:
                    result[painting] = None
            except Exception as e:
                logging.warning(f"FI failed for {self.participant_id} - {painting}: {e}")
                result[painting] = None

        return result





#test:
if __name__ == "__main__":
    # Example usage
    participant_data = MuseumVRParticipantData(participant_id="113", data_path=r"/Users/yanasklar/Documents/TAU/Data/113")

import pandas as pd
from typing import Dict
import logging

# Emotion-to-AU mapping with weights
EMOTION_TO_AUS = {
    "joy": {'CheekRaiserL': 2.0, 'CheekRaiserR': 2.0, 'LipCornerPullerL': 2.5, 'LipCornerPullerR': 2.5},
    "sadness": {'InnerBrowRaiserL': 1.2, 'InnerBrowRaiserR': 1.2, 'BrowLowererL': 0.5, 'BrowLowererR': 0.5, 'LipCornerDepressorL': 3.0, 'LipCornerDepressorR': 3.0},
    "anger": {'BrowLowererL': 1.5, 'BrowLowererR': 1.5, 'LidTightenerL': 1.8, 'LidTightenerR': 1.8},
    "disgust": {'NoseWrinklerL': 2.0, 'NoseWrinklerR': 2.0, 'LipCornerDepressorL': 1.0, 'LipCornerDepressorR': 1.0},
    "surprise": {'JawDrop': 3.0, 'UpperLidRaiserL': 2.0, 'UpperLidRaiserR': 2.0, 'InnerBrowRaiserL': 1.2, 'InnerBrowRaiserR': 1.2}
}

def calculate_intensity_weighted(max_values: pd.Series, aus_weights: Dict[str, float], min_threshold: float = 0.1) -> float:
    intensity_sum = 0
    weight_sum = 0
    for au, weight in aus_weights.items():
        if au in max_values and max_values[au] > min_threshold:
            intensity_sum += max_values[au] * weight
            weight_sum += weight
    return round((intensity_sum / weight_sum) * 100, 2) if weight_sum > 0 else 0

# TODO: older implementation, review if needed -
def calculate_emotion_intensities(face_df: pd.DataFrame, logs_df: pd.DataFrame) -> pd.DataFrame:
    zone_logs = logs_df[logs_df['LogText'].str.contains(
        r"^(?:Player entered the zone of|Player is inside the zone of)",
        na=False, case=False, regex=True
    )].copy()

    zone_logs['Painter'] = zone_logs['LogText'].str.replace("Player entered the zone of ", "", regex=False)
    zone_logs['Painter'] = zone_logs['Painter'].str.split(",").str[0]

    first_entry = zone_logs.groupby('Painter')['Time'].min().reset_index()
    first_entry = first_entry[~first_entry['Painter'].str.contains("Demo Piece", case=False)]

    aggregated_result = {}

    for _, row in first_entry.iterrows():
        painting = row['Painter']
        start = row['Time']
        end = start + 2.0

        try:
            window = face_df[(face_df['Time'] >= start) & (face_df['Time'] <= end)].copy()
            if window.empty:
                continue

            numeric = window.iloc[:, 1:].apply(pd.to_numeric, errors='coerce')
            max_aus = numeric.max()

            intensities = {
                emotion: calculate_intensity_weighted(max_aus, aus)
                for emotion, aus in EMOTION_TO_AUS.items()
            }

            pos = intensities['joy'] + intensities['surprise']
            neg = intensities['sadness'] + intensities['anger'] + intensities['disgust']
            valence = round(((pos - neg) / 100) * 50, 2)
            valence = max(min(valence, 50), -50)

            for emotion, score in intensities.items():
                aggregated_result[f"{painting} - {emotion}"] = score
            aggregated_result[f"{painting} - valence"] = valence

        except Exception as e:
            logging.error(f"Error processing data for {painting}: {e}")
            raise e

    return pd.DataFrame([aggregated_result])

def claculate_emotion_intensities_for_2_seconds_after_time(face_df:pd.DataFrame, start_time: float) -> pd.DataFrame:
    """
    Calculate emotion intensities for 2 seconds after a specific time from the logs.
    
    Args:
        face_df (pd.DataFrame): DataFrame containing facial data.
        start_time (float): The time from which to calculate the 2-second window.
    
    Returns:
        pd.DataFrame: DataFrame with calculated emotion intensities.
    """

    end = start_time + 2.0

    try:
        window = face_df[(face_df['Time'] >= start_time) & (face_df['Time'] <= end)].copy()

        numeric_window = window.iloc[:, 1:].apply(pd.to_numeric, errors='coerce')
        max_aus_per_window = numeric_window.max()

        intensities = {}
        for emotion_name, emotion_aus_weights in EMOTION_TO_AUS.items():
            score = calculate_intensity_weighted(max_aus_per_window, emotion_aus_weights)
            intensities[emotion_name] = score

        return_df = pd.DataFrame([intensities])
        return return_df
        
    except Exception as e:
            logging.error(f"Error processing emotion intensities: {e}")
            raise e
    
def get_dominant_emotion_after_time(face_df: pd.DataFrame, logs_df: pd.DataFrame, start_time: float, intensity_threshold=0.5) -> tuple[str, float]:
        """
        Get the dominant emotion after a specific time from the logs.
        
        Args:
            face_df (pd.DataFrame): DataFrame containing facial data.
            logs_df (pd.DataFrame): DataFrame containing log data.
            start_time (float): The time from which to calculate the 2-second window.
        
        Returns:
            str: The dominant emotion and its intensity.
            if the max intensity is below the threshold, return "neutral" and 0.0
        """
        intensities = claculate_emotion_intensities_for_2_seconds_after_time(face_df, logs_df, start_time)
        max_intensity = intensities.max(axis=1).values[0]
        max_emotion = intensities.idxmax(axis=1).values[0]

        if max_intensity < intensity_threshold:
            return "neutral", 0.0

        return max_emotion, max_intensity

def get_valence_after_time(face_df: pd.DataFrame, logs_df: pd.DataFrame, start_time: float) -> float:
    """
    Get the valence after a specific time from the logs.
    
    Args:
        face_df (pd.DataFrame): DataFrame containing facial data.
        logs_df (pd.DataFrame): DataFrame containing log data.
        start_time (float): The time from which to calculate the 2-second window.
    
    Returns:
        float: The valence value.
    """
    intensities = claculate_emotion_intensities_for_2_seconds_after_time(face_df, logs_df, start_time)
    pos = intensities['joy'] + intensities['surprise']
    neg = intensities['sadness'] + intensities['anger'] + intensities['disgust']
    valence = round(((pos - neg) / 100) * 50, 2)
    valence = max(min(valence, 50), -50)
    return valence
    
def get_sequence_of_emotion_intensities(face_df: pd.DataFrame) -> pd.DataFrame:
    """
    Get the sequence of emotion intensities over a specified duration, separated to 2-second windows.
    
    Args:
        face_df (pd.DataFrame): DataFrame containing facial data.
    
    Returns:
        Dict[float, pd.DataFrame]: A dictionary where keys are the start times of each 2-second window and values are DataFrames with calculated emotion intensities.
    """


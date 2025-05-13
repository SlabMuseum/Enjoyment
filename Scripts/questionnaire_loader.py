import pandas as pd
import csv

pd.set_option('future.no_silent_downcasting', True) # opt in to future behavior and avoid warnings

def load_questionnaire_data(csv_path: str) -> pd.DataFrame:
    # Load the questionnaire data
    data = pd.read_csv(csv_path, quoting=csv.QUOTE_NONE, sep=';')
    data = data.drop(columns=['Timestamp'])
    participant_ids = data['Number']

    # Map categorical answers to numbers
    order_mapping = {
        'Not satisfied at all': 1, 'Not satisfied': 2, 'Quite dissatisfied': 3, 'Neutral': 4,
        'Quite satisfied': 5, 'Satisfied': 6, 'Very satisfied': 7,
        'Too long': 1, 'Long': 2, 'Quite long': 3, 'Exactly the right length': 4,
        'Quite short': 5, 'Short': 6, 'Too short': 7,
        'Do not want at all': 1, 'Do not want': 2, 'Quite do not want': 3, 'Not sure': 4,
        'Quite want': 5, 'Want': 6, 'Really want': 7,
        'I will not recommend at all': 1, 'I will not recommend': 2, 'I will not quite recommend': 3,
        'Somewhat recommend': 5, 'I will recommend': 6, 'Highly recommend': 7,
        'Did not like at all': 1, 'Did not like': 2, 'Quite disliked': 3,
        'Quite liked': 5, 'Liked': 6, 'Really liked': 7,
        'Option 1': 1, 'Option 2': 2
    }
    
    
    numerical_data = data.replace(order_mapping).infer_objects(copy=False) # Convert categorical data to numeric values, determines the dtype of each column
    response_columns = numerical_data.columns[2:16] # Select only the relevant columns with question responses
    numeric_responses = numerical_data[response_columns] # Select only the relevant columns with numeric responses
    numeric_responses.index = data['Number'].rename_axis("ID") # Add participant IDs as index
    

    # Rename artwork columns
    return numeric_responses.rename(columns={
        "Please rate how much you liked the artwork.": "Klimt",
        "Please rate how much you liked the artwork..1": "van Dongen",
        "Please rate how much you liked the artwork..2": "Braque",
        "Please rate how much you liked the artwork..3": "Pollock",
        "Please rate how much you liked the artwork..4": "de Chirico",
        "Please rate how much you liked the artwork..5": "Janco",
        "Please rate how much you liked the artwork..6": "Picasso"
    })


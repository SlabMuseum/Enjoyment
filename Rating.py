import pandas as pd
import csv
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from scipy.stats import kruskal

data = pd.read_csv('res.csv', quoting=csv.QUOTE_NONE, sep = ';')
data = data.drop(columns = ['Timestamp'])
participant_ids = data['Number']

order_mapping = {
    'Not satisfied at all': 1, 'Not satisfied': 2, 'Quite dissatisfied': 3, 'Neutral': 4,
    'Quite satisfied': 5, 'Satisfied': 6, 'Very satisfied': 7,
    'Too long': 1, 'Long': 2, 'Quite long': 3, 'Exactly the right length': 4,
    'Quite short': 5, 'Short': 6, 'Too short': 7,
    'Do not want at all': 1, 'Do not want': 2, 'Quite do not want': 3, 'Not sure': 4,
    'Quite want': 5, 'Want': 6, 'Really want': 7,
    'I will not recommend at all': 1, 'I will not recommend': 2, 'I will not quite recommend': 3,
    'Not sure': 4, 'Somewhat recommend': 5, 'I will recommend': 6, 'Highly recommend': 7,
    'Did not like at all': 1, 'Did not like': 2, 'Quite disliked': 3, 'Neutral': 4,
    'Quite liked': 5, 'Liked': 6, 'Really liked': 7,
    'Option 1': 1, 'Option 2': 2
}

numerical_data = data.copy()
numerical_data = numerical_data.replace(order_mapping)
response_columns = numerical_data.columns[2:16]
centralized_data = numerical_data[response_columns].sub(numerical_data[response_columns].mean(axis=1), axis=0)
z_scored_data = centralized_data.div(numerical_data[response_columns].std(axis=1), axis=0)
ranked_data = z_scored_data.rank(axis=1, method='min', ascending=False).astype(int)
# ranked_data = pd.concat([participant_ids, ranked_data], axis=1)
# ranked_data.to_csv('ranked_responses.csv', index=False)

ranked_data = pd.concat([numerical_data['Type'], ranked_data], axis=1)
avg_rank_per_type = ranked_data.groupby('Type').mean()
avg_rank_per_type = avg_rank_per_type.drop(columns=['Number'])
avg_rank_per_type = avg_rank_per_type.round(2)
avg_rank_per_type.to_csv('average_rank_per_question.csv')

# Kruskal-Wallis Test
results_df = pd.DataFrame(columns=['Question', 'Statistic', 'p-value', 'Interpretation'])

for column in ranked_data.columns[1:]:  # Iterate over questions
    group_data = [ranked_data[ranked_data['Type'] == t][column].dropna() 
                  for t in ranked_data['Type'].unique()]
    stat, p_value = kruskal(*group_data)
    stat = round(stat, 3)
    p_value = round(p_value, 3)
    print(f"Kruskal-Wallis Test for {column}: p-value = {p_value}")
    new_row = pd.DataFrame([{
    'Question': column,
    'Statistic': stat,
    'p-value': p_value,
    'Interpretation': 'Significant' if p_value < 0.05 else 'Not Significant'
    }])
    results_df = pd.concat([results_df, new_row], ignore_index=True)
results_df.to_csv('Anova_ranks.csv', index=False)

""" # Anova overall
avr_cut = avg_rank_per_type.drop(columns=['Type'])
stat_all, p_value_all = kruskal(avr_cut.iloc[0], avr_cut.iloc[1], avr_cut.iloc[2])
stat_all = round(stat_all, 3)
p_value_all = round(p_value_all, 3)
new_row = pd.DataFrame([{
    'Question': 'All Questions',
    'Statistic': stat_all,
    'p-value': p_value_all,
    'Interpretation': 'Significant' if p_value_all < 0.05 else 'Not Significant'
    }])
results_df = pd.concat([results_df, new_row], ignore_index=True)


"""

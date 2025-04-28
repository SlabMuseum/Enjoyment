import pandas as pd
import csv
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import seaborn as sns
import numpy as np
from scipy.stats import shapiro, kstest
from scipy.stats import kruskal
from scipy.stats import mannwhitneyu
from scipy.stats import fligner
from scipy.stats import chi2_contingency


# Load and preprocess data
data = pd.read_csv('res.csv', quoting=csv.QUOTE_NONE, sep=';').drop(columns=['Timestamp', 'Number'])
data = data.iloc[:, :15]

# Define mappings for each order
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

# Map ordinal values to data
numerical_data = data.replace(order_mapping)
n = numerical_data.groupby('Type').size()

# Calculate summary statistics
stats = numerical_data.groupby('Type').agg(['mean', 'median', 'std']).round(2)
# Calculate SE (std / sqrt(n)) and replace the std column
for col in numerical_data.columns:
    if col != 'Type':  # Skip non-numerical columns
        stats[(col, 'std')] = (stats[(col, 'std')] / np.sqrt(n)).round(2)  # Add rounding here

stats.columns = ['_'.join(col).replace('std', 'se').strip() for col in stats.columns.values]
stats = stats.reset_index()


# Melt the DataFrame for long format
stats = stats.melt(id_vars=['Type'], var_name='Stat_Question', value_name='Value')
stats[['Question', 'Stat']] = stats['Stat_Question'].str.split('_', n=1, expand=True)
stats = stats.drop(columns=['Stat_Question'])
stats.to_string()

# Save stats to CSV
question_order = stats['Question'].drop_duplicates().tolist()
stats['Question'] = pd.Categorical(stats['Question'], categories=question_order, ordered=True)
stats = stats.sort_values(by=['Question', 'Type']).reset_index(drop=True)
stats.to_csv('stats_ordered.csv', index=False)

# Transform the data to wide format
question_order = stats['Question'].drop_duplicates().tolist()
stats_df_pivot = stats.pivot_table(
    index=['Type', 'Question'],  
    columns='Stat',             
    values='Value',             
).reset_index()

# Remove the column index name and rename columns for clarity
stats_df_pivot.columns.name = None
stats_df_pivot = stats_df_pivot.rename(columns={'mean': 'Mean', 'median': 'Median', 'se': 'SE'})
stats_df_pivot['Question'] = pd.Categorical(stats_df_pivot['Question'], categories=question_order, ordered=True)
stats_df_pivot = stats_df_pivot.sort_values(by=['Question', 'Type']).reset_index(drop=True)
stats_df_pivot.to_csv('stats.csv', index=False)

# Filter and clean data
avg_data = stats[stats['Stat'] == 'mean'].copy()
se_data = stats[stats['Stat'] == 'se'].rename(columns={'Value': 'SE'})[['Type', 'Question', 'SE']]
avg_data = avg_data.merge(se_data, on=['Type', 'Question'], how='left')
avg_data['Ordinal'] = avg_data['Question'].map({q: i + 1 for i, q in enumerate(numerical_data.columns[1:])})
avg_data.to_string()


# Plot
plt.figure(figsize=(16, 8))
sns.barplot(
    data=avg_data,
    x='Ordinal',
    y='Value',
    hue='Type',
    palette='muted',
    dodge=True,
    ci=None,
)

# Add dynamic error bars
type_order = sorted(avg_data['Type'].unique())
for i, row in avg_data.iterrows():
    offset = 0.2 * (type_order.index(row['Type']) - (len(type_order) - 1) / 2)
    plt.errorbar(
        x=row['Ordinal'] - 1 + offset,
        y=row['Value'],
        yerr=row['SE'],
        fmt='none',
        ecolor='black',
        capsize=4,
        zorder=10
    )


median_data = stats[stats['Stat'] == 'median'].copy()
median_data['Ordinal'] = median_data['Question'].map({q: i + 1 for i, q in enumerate(numerical_data.columns[1:])})

for i, row in median_data.iterrows():
    plt.scatter(
        x=row['Ordinal'] - 1 + (0.2 * (sorted(avg_data['Type'].unique()).index(row['Type']) - 1)),  # Adjust dot position
        y=row['Value'],
        color='red',
        label='Median' if i == 0 else "",  # Add label only once for legend
        zorder=10
    )
median_legend = mlines.Line2D([], [], color='red', marker='o', linestyle='None', markersize=8, label='Median')


# Customize plot
plt.title('Average Ranks with Standard Errors by Type')
plt.ylabel('Average Rank')
plt.xlabel('Question Number')
plt.xticks(rotation=0, ha='right')
plt.legend(title='Type', loc='upper left', bbox_to_anchor=(1, 1), handles=plt.gca().get_legend_handles_labels()[0] + [median_legend])
plt.tight_layout()
plt.savefig('Average.png', dpi=300, bbox_inches='tight')
plt.show()





# Tests
results_df = pd.DataFrame(columns=['Test', 'Question', 'Type1', 'Type2', 'Type3', 'Statistic', 'p-value', 'Effect Size', 'Interpretation'])

# Check for normal distribution - no, it's not
for column in numerical_data.columns[1:]:  # Iterate over questions
    print(f"Normality Test for {column}:")
    for t in numerical_data['Type'].unique():  # Iterate over Types
        group_data = numerical_data[numerical_data['Type'] == t][column].dropna()  # Group data for this Type
        stat, p_value = shapiro(group_data)
        stat = round(stat, 3)
        p_value = round(p_value, 3)
        print(f"  Type: {t}, p-value = {p_value}")
    print("-" * 50)

# Kruskal-Wallis H Test - no significant differences
for column in numerical_data.columns[1:]:  # Iterate over questions
    group_data = [numerical_data[numerical_data['Type'] == t][column].dropna() 
                  for t in numerical_data['Type'].unique()]
    stat, p_value = kruskal(*group_data)
    stat = round(stat, 3)
    p_value = round(p_value, 3)
    print(f"Kruskal-Wallis Test for {column}: p-value = {p_value}")
    eta_squared = stat / (len(numerical_data) - 1)
    new_row = pd.DataFrame([{
    'Test': 'Kruskal-Wallis',
    'Question': column,
    'Type1': 'All',
    'Type2': 'All',
    'Type3': 'All',
    'Statistic': stat,
    'p-value': p_value,
    'Effect Size': eta_squared,
    'Interpretation': 'Significant' if p_value < 0.05 else 'Not Significant'
    }])
    results_df = pd.concat([results_df, new_row], ignore_index=True)
print(f"Kruskal-Wallis Effect Size (Eta Squared): {eta_squared}")

# Mann-Whitney U Tests - 1 and 3
for column in numerical_data.columns[1:]: 
    group1 = numerical_data[numerical_data['Type'] == '1 Fully active'][column].dropna()
    group2 = numerical_data[numerical_data['Type'] == '3 Passive'][column].dropna()
    
    stat, p_value = mannwhitneyu(group1, group2, alternative='two-sided')
    stat = round(stat, 3)
    p_value = round(p_value, 3)

    new_row = pd.DataFrame([{
    'Test': 'Mann-Whitney U Test, 1 and 3',
    'Question': column,
    'Type1': '1 Fully active',
    'Type2': '3 Passive',
    'Type3': '-',
    'Statistic': stat,
    'p-value': p_value,
    'Effect Size': 'N/A',
    'Interpretation': 'Significant' if p_value < 0.05 else 'Not Significant'
    }])
    results_df = pd.concat([results_df, new_row], ignore_index=True)
    print(f"Mann-Whitney U Test: p-value = {p_value}")

# Mann-Whitney U Tests - 1 and 2
for column in numerical_data.columns[1:]: 
    group1 = numerical_data[numerical_data['Type'] == '1 Fully active'][column].dropna()
    group2 = numerical_data[numerical_data['Type'] == '2 Semi-active'][column].dropna()
    
    stat, p_value = mannwhitneyu(group1, group2, alternative='two-sided')
    stat = round(stat, 3)
    p_value = round(p_value, 3)

    new_row = pd.DataFrame([{
    'Test': 'Mann-Whitney U Test, 1 and 2',
    'Question': column,
    'Type1': '1 Fully active',
    'Type2': '2 Semi-active',
    'Type3': '-',
    'Statistic': stat,
    'p-value': p_value,
    'Effect Size': 'N/A',
    'Interpretation': 'Significant' if p_value < 0.05 else 'Not Significant'
    }])
    results_df = pd.concat([results_df, new_row], ignore_index=True)

# Mann-Whitney U Tests - 2 and 3
for column in numerical_data.columns[1:]: 
    group1 = numerical_data[numerical_data['Type'] == '2 Semi-active'][column].dropna()
    group2 = numerical_data[numerical_data['Type'] == '3 Passive'][column].dropna()
    
    stat, p_value = mannwhitneyu(group1, group2, alternative='two-sided')
    stat = round(stat, 3)
    p_value = round(p_value, 3)

    new_row = pd.DataFrame([{
    'Test': 'Mann-Whitney U Test, 2 and 3',
    'Question': column,
    'Type1': '2 Semi-active',
    'Type2': '3 Passive',
    'Type3': '-',
    'Statistic': stat,
    'p-value': p_value,
    'Effect Size': 'N/A',
    'Interpretation': 'Significant' if p_value < 0.05 else 'Not Significant'
    }])
    results_df = pd.concat([results_df, new_row], ignore_index=True)


# Fligner-Killeen Test - no difference
for column in numerical_data.columns[1:]:
    group_data = [numerical_data[numerical_data['Type'] == t][column].dropna() 
        for t in numerical_data['Type'].unique()]
    stat, p_value = fligner(*group_data)
    stat = round(stat, 3)
    p_value = round(p_value, 3)

    new_row = pd.DataFrame([{
    'Test': 'Fligner-Killeen Test',
    'Question': column,
    'Type1': 'All',
    'Type2': 'All',
    'Type3': 'All',
    'Statistic': stat,
    'p-value': p_value,
    'Effect Size': 'N/A',
    'Interpretation': 'Significant' if p_value < 0.05 else 'Not Significant'
    }])
    results_df = pd.concat([results_df, new_row], ignore_index=True)
    print(f"Fligner-Killeen Test for {column}: p-value = {p_value}")

# Chi-Squared Test 
for column in data.columns[1:]:
    contingency_table = pd.crosstab(data['Type'], data[column])
    stat, p_value, dof, expected = chi2_contingency(contingency_table)
    stat = round(stat, 3)
    p_value = round(p_value, 3)

    new_row = pd.DataFrame([{
    'Test': 'Chi-Squared',
    'Question': column,
    'Type1': 'All',
    'Type2': 'All',
    'Type3': 'All',
    'Statistic': stat,
    'p-value': p_value,
    'Effect Size': 'N/A',
    'Interpretation': 'Significant' if p_value < 0.05 else 'Not Significant'
    }])
    results_df = pd.concat([results_df, new_row], ignore_index=True)
    print(f"Chi-Square Test for {column}: p-value = {p_value}")

results_df.to_csv('Statistical_tests.csv', index=False)

import pandas as pd
import csv
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

data = pd.read_csv('res.csv', quoting=csv.QUOTE_NONE, sep = ';')
data = data.drop(columns = ['Timestamp'])

order_0 = ['Not satisfied at all', 'Not satisfied', 'Quite dissatisfied', 'Neutral', 'Quite satisfied', 'Satisfied', 'Very satisfied']
order_1 = ['Too long', 'Long', 'Quite long', 'Exactly the right length', 'Quite short', 'Short', 'Too short']
order_2 = ['Do not want at all', 'Do not want', 'Quite do not want', 'Not sure', 'Quite want', 'Want', 'Really want']
order_3 = ['I will not recommend at all', 'I will not recommend', 'I will not quite recommend', 'Not sure', 'Somewhat recommend', 'I will recommend', 'Highly recommend']
order_4 = ['Did not like at all', 'Did not like', 'Quite disliked', 'Neutral', 'Quite liked', 'Liked', 'Really liked']
order_5 = ['Option 1', 'Option 2']

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


for i in range(2, data.shape[1]):
    columnname = data.columns[i]
    
    if numerical_data[columnname].dtype.name == 'category':
        numerical_data[columnname] = numerical_data[columnname].cat.codes + 1  # Convert to numerical codes
    # Calculate the average of numerical answers for each Type
    avg_answers = numerical_data.groupby('Type')[columnname].mean().round(2).reset_index()
    # Prepare legend with averages
    legend_labels = [
        f"{row['Type']} (Avg: {row[columnname]})"
        for _, row in avg_answers.iterrows()
    ]

    # Create categorical data
    if i ==2 or i == 3:
        data[columnname] = pd.Categorical(data[columnname], categories=order_0, ordered=True)
    if i ==4:
        data[columnname] = pd.Categorical(data[columnname], categories=order_1, ordered=True)
    if i >=5 and i<8:
        data[columnname] = pd.Categorical(data[columnname], categories=order_2, ordered=True)
    if i ==8:
        data[columnname] = pd.Categorical(data[columnname], categories=order_3, ordered=True)
    if i >=9 and i<16:
        data[columnname] = pd.Categorical(data[columnname], categories=order_4, ordered=True)
    if i >=16:
        data[columnname] = pd.Categorical(data[columnname], categories=order_5, ordered=True)
    
    # Group by Type and column, then normalize within each Type
    grouped = data.groupby(['Type', columnname]).size().reset_index(name='Count')
    grouped['Proportion'] = grouped.groupby('Type')['Count'].apply(lambda x: x / x.sum()).reset_index(drop=True)
    

    # Plot the normalized data
    if i<16:
        plt.figure(figsize=(10, 6))
        sns.barplot(data=grouped, x=columnname, y='Proportion', hue='Type', palette='muted')
        plt.title(f'{columnname}')
        plt.ylabel('Proportion')
        plt.xlabel('')
        plt.legend(title='Type')
        plt.xticks(rotation=45, ha='right')  # Rotate labels 45 degrees and align them to the right
        # Update legend with averages
        handles, _ = plt.gca().get_legend_handles_labels()
        plt.legend(handles, legend_labels, title='Type', loc='upper right')

        plt.tight_layout()    
        plt.suptitle('') 
        plt.savefig(f'graph {i}.png', dpi=300, bbox_inches='tight')
        plt.show()
    else:
        plt.figure(figsize=(6, 6))
        sns.barplot(data=grouped, x=columnname, y='Proportion', hue='Type', palette='muted')
        plt.title(f'{columnname}')
        plt.ylabel('Proportion')
        plt.xlabel('')
        plt.legend(title='Type')
        plt.xticks(rotation=45, ha='right')  # Rotate labels 45 degrees and align them to the right
        plt.tight_layout()    
        plt.suptitle('') 
        plt.savefig(f'graph {i}.png', dpi=300, bbox_inches='tight')
        plt.show()

# all the paintings from the museum
minidata = data.iloc[:, 9:16]
minidata = data.melt(id_vars=['Type'], value_vars=data.columns[9:16], var_name='Painting', value_name='Rating')
minidata['Rating'] = minidata['Rating'].map(order_mapping).astype(float)  # Ensure numerical type
avg_painting_ratings = minidata.groupby('Type')['Rating'].mean().round(2).reset_index()

#minidata['Rating'] = pd.Categorical(minidata['Rating'], categories=order_4, ordered=True)
grouped_minidata = (minidata.groupby(['Type', 'Rating']).size().reset_index(name='Count'))
grouped_minidata['Proportion'] = grouped_minidata.groupby('Type')['Count'].apply(lambda x: x / x.sum()).reset_index(drop=True)

legend_labels = [
    f"{row['Type']} (Avg: {row['Rating']})"
    for _, row in avg_painting_ratings.iterrows()
]

plt.figure(figsize=(10, 6))
sns.barplot(data=grouped_minidata, x='Rating', y='Proportion', hue='Type', palette='muted')
plt.title('How much you liked all the paintings from the museum by Type')
plt.ylabel('Proportion')
plt.xlabel('Rating')
plt.legend(title='Type')
plt.xticks(ticks=range(len(order_4)), labels=order_4, rotation=45, ha='right')
handles, _ = plt.gca().get_legend_handles_labels()
plt.legend(handles, legend_labels, title='Type', loc='upper right')
plt.tight_layout()
plt.savefig('All.png', dpi=300, bbox_inches='tight')
plt.show()

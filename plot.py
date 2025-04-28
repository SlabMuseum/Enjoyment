
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import glob
import os
from scipy.stats import kruskal
import seaborn as sns

# Path to the CSV file
file_list = glob.glob('/Users/yanasklar/Documents/TAU/Data/Continuous/*.csv')
logs_folder = '/Users/yanasklar/Documents/TAU/Data/Logs/'


all_data = []
all_focus = []

for file in file_list:
    df = pd.read_csv(file)
    participant_id = file.split("/")[-1].split(".csv")[0]  # Extract participant ID from filename
    participant_id = participant_id[-3:]
    df.insert(0, "ID", participant_id)  # Add participant identifier
    
    # Get start time, not demo
    log_file_pattern = os.path.join(logs_folder, f"*{participant_id}.csv")  
    logs_path = glob.glob(log_file_pattern)
    logs_path = logs_path[0]
    logs = pd.read_csv(logs_path)
    start_time = logs[logs.iloc[:, 0] == 'Instructions board hidden Lets start the tour Instructions']
    if start_time.empty:
        print(f"Start instruction not found for participant {participant_id}, skipping...")
        start_time = logs[logs.iloc[:, 0] == 'Instructions board hidden']
        start_time = start_time.index[-2]
        start_time = float(start_time)
        print(start_time)
        continue  # Skip this participant if no start time found
    start_time = start_time.index[0]
    start_time = float(start_time)
    df = df[df['Time'] > start_time]
    df = df.reset_index(drop=True) # Reset the index after filtering

    # Get the type
    type_exp = logs[logs.iloc[:, 0].str.startswith('Selected experiment type:')]
    type_exp = type_exp.iloc[0, 0][-1]
    df.insert(0, 'Type', type_exp)
    all_data.append(df)

    # Get the data on focused objects and duration 
    focused_object = df['FocusedObject']
    focus_durations = df['FocusedObject'].value_counts()  # Counts the occurrences of each object
    sampling_rate = 1 / 60  # Assuming 60 Hz (60 rows per second) sampling rate
    focus_durations_seconds = (focus_durations * sampling_rate).round(2)
    focus_durations_seconds = focus_durations_seconds.reset_index()
    focus_durations_seconds.columns = ['FocusedObject', 'DurationInSeconds']

    overall_duration = (df.iloc[-1, 2] - df.iloc[0, 2]).round(2)    
    overall = pd.DataFrame({'FocusedObject': ['Overall time'], 'DurationInSeconds': [overall_duration]})
    focus_durations_seconds = pd.concat([focus_durations_seconds, overall], ignore_index=True)
    focus_durations_seconds = focus_durations_seconds.T
    focus_durations_seconds.columns = focus_durations_seconds.iloc[0] 
    focus_durations_seconds = focus_durations_seconds[1:].reset_index(drop=True)
    focus_durations_seconds.insert(0, 'ID', participant_id)
    focus_durations_seconds.insert(1, 'Type', type_exp)
    focus_durations_seconds.index.name = "Index"
    all_focus.append(focus_durations_seconds)

all_df = pd.concat(all_data, ignore_index=True)
all_focus_data = pd.concat(all_focus, ignore_index=True)
barrier_columns = [col for col in all_focus_data.columns if col.startswith("Barrier")]
all_focus_data = all_focus_data.drop(columns=barrier_columns)
all_focus_data = all_focus_data.drop(columns= ['HeadCollider'])
all_focus_data.to_csv('/Users/yanasklar/Documents/TAU/Data/Focus/Focus Data.csv')


# Kruskal-Wallis Test
results_df = pd.DataFrame(columns=['Question', 'Statistic', 'p-value', 'Interpretation'])
for column in all_focus_data.columns.difference(['Type']): 
    group_data = [all_focus_data[all_focus_data['Type'] == t][column].dropna() 
                  for t in all_focus_data['Type'].unique()]
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
results_df.to_csv('/Users/yanasklar/Documents/TAU/Data/Focus/Anova_focus_objects.csv', index=False)


""" Plots the gazing for each participant 
# Extract the EyeGazeHitPosition columns
x = df['EyeGazeHitPosition_X']
y = df['EyeGazeHitPosition_Y']
z = df['EyeGazeHitPosition_Z']
focused_object = df['FocusedObject']

# Generate a unique color for each focused object
unique_objects = focused_object.unique()
colors = plt.cm.get_cmap('tab20', len(unique_objects))
color_dict = {obj: colors(i) for i, obj in enumerate(unique_objects)}
color_list = [color_dict[obj] for obj in focused_object]

# Create a 3D plot
fig = plt.figure(figsize=(14, 6))
ax = fig.add_subplot(111, projection='3d')
# Plot the gaze hit positions with colors based on FocusedObject
scatter = ax.scatter(x, z, y, c=color_list, marker='o')
ax.set_xlabel('EyeGazeHitPosition_X')
ax.set_ylabel('EyeGazeHitPosition_Z')
ax.set_zlabel('EyeGazeHitPosition_Y')
ax.set_title('3D Plot of Gaze Hit Position')
handles = [plt.Line2D([0], [0], marker='o', color=color_dict[obj], markersize=10, label=obj) for obj in unique_objects]
ax.legend(handles=handles, title='FocusedObject', loc='center left', bbox_to_anchor=(1.05, 0.5), borderaxespad=0., ncol = 2)
plt.subplots_adjust(left=0.1, right=0.75)  # Expands the right margin for legend

# Set the same scale for all axes
max_range = max(x.max() - x.min(), y.max() - y.min(), z.max() - z.min())
mid_x = (x.max() + x.min()) * 0.5
mid_y = (y.max() + y.min()) * 0.5
mid_z = (z.max() + z.min()) * 0.5

ax.set_xlim(mid_x - max_range * 0.5, mid_x + max_range * 0.5)
ax.set_ylim(mid_z - max_range * 0.5, mid_z + max_range * 0.5)
ax.set_zlim(0, mid_y + max_range * 0.5)

# Show the plot
plt.show()
"""

# Compute engagement metrics by participant and Type
participant_metrics = all_df.groupby(["ID", "Type"]).agg(
    FocusedObjectCount=('FocusedObject', 'nunique'),  # Unique objects looked at
    TotalFocusDuration=('FocusedObject', 'count'),  # Total gaze samples
    SwitchingFrequency=('FocusedObject', lambda x: (x != x.shift()).sum()),  # Focus changes
    MinTime=('Time', 'min'),
    MaxTime=('Time', 'max')
).reset_index()

participant_metrics["TotalDuration"] = participant_metrics["MaxTime"] - participant_metrics["MinTime"]
participant_metrics["NormalizedSwitching"] = participant_metrics["SwitchingFrequency"] / participant_metrics["TotalDuration"] # Normalize Switching Frequency by Total Duration

type_metrics = participant_metrics.groupby("Type").agg(
    AvgFocusDuration=('TotalDuration', 'mean'),
    AvgSwitchingFrequency=('NormalizedSwitching', 'mean'),
    AvgObjectsFocused=('FocusedObjectCount', 'mean'),
    ParticipantCount=('ID', 'nunique')
).reset_index()

# Visualizing Differences by Type
plt.figure(figsize=(12, 5))
sns.barplot(data=type_metrics, x="Type", y="AvgFocusDuration", palette="viridis")
plt.xlabel("Type")
plt.ylabel("Average Focus Duration (Seconds)")
plt.title("Average Engagement Duration by Type")
plt.xticks(rotation=45)
plt.show()

plt.figure(figsize=(12, 5))
sns.barplot(data=type_metrics, x="Type", y="AvgSwitchingFrequency", palette="coolwarm")
plt.xlabel("Type")
plt.ylabel("Average Switching Frequency")
plt.title("Average Gaze Switching by Type")
plt.xticks(rotation=45)
plt.show()


# Calculate engagement levels for each participant
all_categorized_data = []

for t in participant_metrics["Type"].unique():
    subset = participant_metrics[participant_metrics["Type"] == t].copy()  # Copy to avoid warnings
    if len(subset) > 2:  
        low_threshold = np.percentile(subset["TotalDuration"], 33)
        high_threshold = np.percentile(subset["TotalDuration"], 66)
        # Categorize engagement levels
        def categorize_engagement(duration):
            if duration <= low_threshold:
                return "Low Engagement"
            elif duration <= high_threshold:
                return "Medium Engagement"
            else:
                return "High Engagement"
        subset["EngagementCategory"] = subset["TotalDuration"].apply(categorize_engagement)
        all_categorized_data.append(subset)
final_engagement_data = pd.concat(all_categorized_data, ignore_index=True)
final_engagement_data.to_csv('/Users/yanasklar/Documents/TAU/Data/Engagement_Levels_All_Types.csv', index=False)


import os
import glob
import pandas as pd

def assign_tiles(df):
    # Define bounding boxes in pixel coordinates: (xmin, xmax, ymin, ymax)
    # Each tuple = (x_min, x_max, y_min, y_max)
    tiles = {
        "Pollock":    (398, 774, 324, 691),
        "van Dongen": (388, 694, 892, 1200),
        "de Chirico": (388, 694, 1295, 1600),
        "Klimt":      (305, 686, 1873, 2243),
        "Braque":     (790, 1100, 892, 1200),
        "Picasso":    (790, 1100, 1295, 1600),
        "Janco":      (890, 1210, 1902, 2206),
    }

    # Initialize a column for tile labels
    df["tile_label"] = "None"

    # Assign tiles based on (x_pix, y_pix) falling within bounding boxes
    for label, (xmin, xmax, ymin, ymax) in tiles.items():
        condition = (df["x_pix"] >= xmin) & (df["x_pix"] <= xmax) & \
                    (df["y_pix"] >= ymin) & (df["y_pix"] <= ymax)
        df.loc[condition, "tile_label"] = label

    return df

def add_pixels(df, pixel_size):
    origin_x = df["Head_Position_x"].iloc[0]
    origin_y = df["Head_Position_Z"].iloc[0]
    anchor_x = 755
    anchor_y = 1800
    df["x_pix"] = anchor_x - ((df["Head_Position_x"] - origin_x) / pixel_size)
    df["y_pix"] = ((df["Head_Position_Z"] - origin_y) / pixel_size) + anchor_y
    return df

def deal_with_demo(file):
    logs_data_folder = "/Users/yanasklar/Documents/TAU/Data/Logs/"
    df = pd.read_csv(file)
    participant_id = os.path.basename(file).split(".csv")[0][-3:]  # Extract participant ID
    
    # Load the corresponding Logs file
    logs_file_path = glob.glob(os.path.join(logs_data_folder, f"*{participant_id}.csv"))
    if not logs_file_path:
        print(f"No logs file found for participant {participant_id}. Skipping...")
    logs_df = pd.read_csv(logs_file_path[0], names=["LogTime", "LogText", "Extra"], dtype=str, engine="python", skiprows=1)

    # Extract timestamps from the logs
    if participant_id == "109":
        experiment_start_time = 129.0
    else:    
        experiment_start_time = logs_df.loc[logs_df['LogText'] == "Instructions board hidden Lets start the tour Instructions", 'LogTime'].astype(float).values
        experiment_start_time = experiment_start_time[0] if len(experiment_start_time) > 0 else None
    demo_3_switch = logs_df.loc[logs_df['LogText'] == "Player exited the zone of van Dongen", 'LogTime'].astype(float).values
    demo_2_switch = logs_df.loc[logs_df['LogText'] == "Player exited the zone of de Chirico", 'LogTime'].astype(float).values

    # Ensure we have valid values
    demo_3_switch = demo_3_switch[0] if len(demo_3_switch) > 0 else float('inf')
    demo_2_switch = demo_2_switch[0] if len(demo_2_switch) > 0 else float('inf')

    if experiment_start_time is None:
        print(f"Experiment start time not found for participant {participant_id}. Skipping...")
    
    # Filter the Continuous data to keep only data collected after experiment_start_time
    df["Time"] = df["Time"].astype(float)
    origin_row = df.iloc[[0]]
    filtered_rows = df[df["Time"] >= experiment_start_time]
    df = pd.concat([origin_row, filtered_rows], ignore_index=True)

    # Replace demo object names based on Time conditions
    df.loc[df["FocusedObject"] == "Demo Piece 4", "FocusedObject"] = "Janco"
    df.loc[df["FocusedObject"] == "Demo Piece 1", "FocusedObject"] = "Klimt"

    df.loc[(df["FocusedObject"] == "Demo Piece 3") & (df["Time"] < demo_3_switch), "FocusedObject"] = "van Dongen"
    df.loc[(df["FocusedObject"] == "Demo Piece 3") & (df["Time"] >= demo_3_switch), "FocusedObject"] = "de Chirico"

    df.loc[(df["FocusedObject"] == "Demo Piece 2") & (df["Time"] < demo_2_switch), "FocusedObject"] = "Braque"
    df.loc[(df["FocusedObject"] == "Demo Piece 2") & (df["Time"] >= demo_2_switch), "FocusedObject"] = "Picasso"
    return df, participant_id
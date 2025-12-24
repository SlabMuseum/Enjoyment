import logging
import numpy as np
from participant_data import MuseumVRParticipantData as participantData
from participant_data import default_tile_positions 
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import Normalize
from scipy.ndimage import convolve1d
from PIL import Image
import cv2
import matplotlib.patches as patches
from matplotlib.cm import get_cmap
import seaborn as sns

import pandas as pd
from io import StringIO

import os
#region ---- Constants ----

# 3 points to convert Unity coordinates to pixel coordinates with affine transformation
# img_origin: unity zero point in image coordinates (player positioner - spawn point)
# bottom_left_barrier: reference point in image coordinates --- (seahorse statue corner barrier)
# top_right_barrier: reference point in image coordinates --- (Klimt corner barrier)

image_dict = {
    r"Top views/museum_top_iso_grid.png": {
        "img_origin": (224, 113),
        "bottom_left_barrier": (44, 720),
        "top_right_barrier": (331, 32),
    }
    , r"Top views/museum_top_iso.png": {
        "img_origin": (226, 107),
        "bottom_left_barrier": (46, 712),
        "top_right_barrier": (334, 26),
    }
    , r"Top views/museum_top_perspective_grid.png": {
        "img_origin": (286, 133),
        "bottom_left_barrier": (113, 715),
        "top_right_barrier": (391, 55),
    }
    , r"Top views/museum_top_perspective.png": {
        "img_origin": (306, 138),
        "bottom_left_barrier": (133, 720),
        "top_right_barrier": (411, 60),
    }
    , r"sanity": {
        "img_origin": (0,0),
        "bottom_left_barrier": (-2.3101, -2.4648), 
        "top_right_barrier": (0.9805, 5.351),
    }
    , r"Top views/top_view.png": {
        "img_origin": (753,1976),
        "bottom_left_barrier": (1215,409),
        "top_right_barrier": (476,2185),
    }
    , r"Top views/top_view_no_tiles_grid_isometric.png": {
        "img_origin": (266,109),
        "bottom_left_barrier": (68,775),
        "top_right_barrier": (386,20),
    }
        , r"Top views/top_view_no_tiles_no_grid_isometric.png": {
        "img_origin": (254,117),
        "bottom_left_barrier": (56,783),
        "top_right_barrier": (374,27),
    }
        , r"Top views/top_view_no_grid_no_tiles_prespective.png": {
        "img_origin": (283,141),
        "bottom_left_barrier": (111,718),
        "top_right_barrier": (387,63),
    }
        , r"Top views/top_view_grid_no_tiles_prespective_.png": {
        "img_origin": (285,139),
        "bottom_left_barrier": (113,716),
        "top_right_barrier": (389,61),
    }
}

UNITY_ORIGIN = (0, 1.6758) # fixed that! the z ia actually not zero. the zero is the placement of the instructions...
UNITY_BOTTOM_LEFT_BARRIER = (-2.0462, -5.2143) 
UNITY_TOP_RIGHT_BARRIER = (1.2454, 2.6032)

# conver to numpy arrays (vectors) for easier manipulation:
unity_origin = np.array(UNITY_ORIGIN)
unity_bottom_left_barrier = np.array(UNITY_BOTTOM_LEFT_BARRIER)
unity_top_right_barrier = np.array(UNITY_TOP_RIGHT_BARRIER)


EXPORTS_FOLDER = "Plots"  # Folder to save plots


#endregion

# region ---- Plotting trajectory functions ----
def plot_trajectory_over_image(participant_data : participantData, image_path, save_file=True, sampling_rate=60, window_size=5, close_plot=True):
    """
    Plot trajectory colored by smoothed speed over museum top-view image with valence heatmap and gaze/valence legend.
    """
    if image_path not in image_dict:
        raise ValueError(f"Image path '{image_path}' not found in image_dict.")

    image_metadata = image_dict[image_path]
    background = Image.open(image_path)

    df = participant_data.dataframes["ContinuousData"]
    exp_start_time = participant_data.trials_data.iloc[0]["StartTime"]
    df = df[df['Time'] >= exp_start_time]

    coords = df[['Head_Position_x', 'Head_Position_Z']].values
    pixel_points = np.array([convert_unity_units_to_image_px(x, z, image_metadata) for x, z in coords])
    x, y = pixel_points[:, 0], pixel_points[:, 1]

    dx = np.diff(x)
    dy = np.diff(y)
    distances = np.sqrt(dx**2 + dy**2)
    speed = distances * sampling_rate
    smoothed_speed = convolve1d(speed, np.ones(window_size) / window_size, mode='reflect')

    points = np.array([x, y]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)

    norm = Normalize(vmin=np.percentile(smoothed_speed, 2), vmax=np.percentile(smoothed_speed, 98))
    cmap = plt.get_cmap('plasma')
    colors = cmap(norm(smoothed_speed))

    fig, ax = plt.subplots(figsize=(14, 8))  # Wider canvas to leave space for legend
    fig.subplots_adjust(left=0.4)  # Reserve space on the left
    ax.imshow(background)
    ax.add_collection(LineCollection(segments, colors=colors, linewidth=2))
    ax.scatter(x[0], y[0], color="green", label="Start", zorder=5)
    ax.scatter(x[-1], y[-1], color="blue", label="End", zorder=5)

    default_tile_positions_px = convert_tile_position_to_image_px(image_metadata)
    for _, row in default_tile_positions_px.iterrows():
        xs = [row['bottom-left_x'], row['top-left_x'], row['top-right_x'], row['bottom-right_x'], row['bottom-left_x']]
        ys = [row['bottom-left_z'], row['top-left_z'], row['top-right_z'], row['bottom-right_z'], row['bottom-left_z']]
        ax.plot(xs, ys, color='black', linewidth=1.5, zorder=1)

        side = get_tile_label_position(row['name'])
        if side == "left":
            label_x = row["top-left_x"] + 5
            label_y = row["top-left_z"] + 5
            ha = "left"
        else:
            label_x = row["top-right_x"] - 5
            label_y = row["top-right_z"] + 5
            ha = "right"

        ax.text(label_x, label_y, row['name'], ha=ha, va='top', rotation=90, fontsize=8, color='black', zorder=2)

    # Add legend with Gaze Percent | First Impression OUTSIDE to the LEFT
    legend_labels = gaze_percent_legend_labels(participant_data)
    dy = 0.035
    x_pos = 0.02     # Far left, in freed-up space
    y_start = 0.9    # Near top

    fig.text(x_pos, y_start, "Gaze Percent:",
            fontsize=10, weight='bold', va='top', ha='left')
    for i, label in enumerate(legend_labels):
        fig.text(x_pos, y_start - (i + 1) * dy, label,
                fontsize=9, va='top', ha='left')

    # Add speed colorbar
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, orientation="vertical", shrink=0.8)
    cbar.set_label("Speed (px/sec)")

    ax.set_title("Trajectory Colored by Smoothed Speed")
    ax.axis("off")
    ax.legend(loc="upper right")

    if save_file:
        filename = f"{participant_data.participant_id}_speed_trajectory_valence.png"
        path = os.path.join(EXPORTS_FOLDER, filename)
        plt.savefig(path, bbox_inches='tight')
        logging.info(f"Saved to {path}")

    if close_plot:
        plt.show()
        plt.close(fig)
    else:
        plt.show()

def plot_trajectory_over_image_dual_view(participant_data: participantData, image_path, save_file=True, sampling_rate=60, window_size=5, close_plot=True):
    """
    Plot participant's trajectory in both Unity units and image pixel coordinates.
    - Left: Unity space with tile overlays
    - Right: Image with pixel-transformed trajectory colored by smoothed speed
    """
    if image_path not in image_dict:
        raise ValueError(f"Image path '{image_path}' not found in image_dict. Available images: {list(image_dict.keys())}")

    image_metadata = image_dict[image_path]
    background = Image.open(image_path)

    df = participant_data.dataframes["ContinuousData"]
    
    # filter out the demo
    exp_start_time = participant_data.trials_data.iloc[0]["StartTime"]
    df = df[df['Time'] >= exp_start_time]
    
    coords = df[['Head_Position_x', 'Head_Position_Z']].values

    # --- Unity space trajectory ---
    unity_x, unity_z = coords[:, 0], coords[:, 1]

    # --- Image space trajectory ---
    pixel_points = np.array([convert_unity_units_to_image_px(x, z, image_metadata) for x, z in coords])
    px, py = pixel_points[:, 0], pixel_points[:, 1]

    # --- Speed computation ---
    dx, dy = np.diff(px), np.diff(py)
    distances = np.sqrt(dx**2 + dy**2)
    speed = distances * sampling_rate
    smoothed_speed = convolve1d(speed, np.ones(window_size) / window_size, mode='reflect')

    points = np.array([px, py]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)

    norm = Normalize(vmin=np.percentile(smoothed_speed, 2), vmax=np.percentile(smoothed_speed, 98))
    cmap = plt.get_cmap('plasma')
    colors = cmap(norm(smoothed_speed))

    # --- Plotting ---
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(17, 8), gridspec_kw={'wspace': 0.3})

    # -- Unity coordinate plot --
    ax1.plot(unity_x, unity_z, color='black', linewidth=1, alpha=0.4, label='Trajectory')
    ax1.scatter(unity_x[0], unity_z[0], color="green", label="Start", zorder=5)
    ax1.scatter(unity_x[-1], unity_z[-1], color="blue", label="End", zorder=5)

    # Add tiles as rectangles
    for _, row in default_tile_positions.iterrows():
        xs = [row['bottom-left_x'], row['top-left_x'], row['top-right_x'], row['bottom-right_x'], row['bottom-left_x']]
        zs = [row['bottom-left_z'], row['top-left_z'], row['top-right_z'], row['bottom-right_z'], row['bottom-left_z']]
        ax1.plot(xs, zs, 'gray', linewidth=1.5)
        cx = np.mean(xs[:-1])
        cz = np.mean(zs[:-1])
        ax1.text(cx, cz, row['name'], ha='center', va='center', fontsize=9, color='dimgray')

    ax1.set_title("Trajectory in Unity Units")
    ax1.set_xlabel("Unity X")
    ax1.set_ylabel("Unity Z")
    ax1.axis("equal")
    ax1.grid(True)
    ax1.legend()

    # -- Image coordinate plot --
    ax2.imshow(background)
    ax2.add_collection(LineCollection(segments, colors=colors, linewidth=2))
    ax2.scatter(px[0], py[0], color="green", label="Start", zorder=5)
    ax2.scatter(px[-1], py[-1], color="blue", label="End", zorder=5)

    # Add tiles as rectangles in pixel coordinates
    default_tile_positions_px = convert_tile_position_to_image_px(image_metadata)
    for _, row in default_tile_positions_px.iterrows():
        xs = [row['bottom-left_x'], row['top-left_x'], row['top-right_x'], row['bottom-right_x'], row['bottom-left_x']]
        ys = [row['bottom-left_z'], row['top-left_z'], row['top-right_z'], row['bottom-right_z'], row['bottom-left_z']]

        # Draw black tile outline
        ax2.plot(xs, ys, color='black', linewidth=1.5, zorder=1)

        # Determine label placement side
        side = get_tile_label_position(row['name'])

        if side == "left":
            label_x = row["top-left_x"] + 5
            label_y = row["top-left_z"] + 5
            ha = "left"
        else:
            label_x = row["top-right_x"] - 5
            label_y = row["top-right_z"] + 5
            ha = "right"

        ax2.text(label_x, label_y, row['name'],
             ha=ha, va='top', rotation=90,
             fontsize=8, color='black', zorder=2)
        
        name = row['name']
        
    #add a legend with the gaze percentage for each painting 
    legend_labels = gaze_percent_legend_labels(participant_data)
    # Place legend labels between plots using figure coordinates
    # Move legend slightly left to avoid overlapping right graph
    dy = 0.025
    x_pos = 0.475 
    y_start = 0.85

    fig = plt.gcf()
    fig.text(x_pos, y_start + dy, "Gaze Percent:",
            fontsize=9, weight='bold', va='top', ha='left')

    for i, label in enumerate(legend_labels):
        fig.text(x_pos, y_start - i * dy, label,
                fontsize=9, va='top', ha='left')

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax2, orientation="vertical", shrink=0.8)
    cbar.set_label("Speed (px/sec)")

    ax2.set_title("Trajectory on Image (Pixels)")
    ax2.axis("off")
    ax2.legend(loc="upper right")

    fig.suptitle(f"Participant: {participant_data.participant_id}", fontsize=14)

    if save_file:
        filename = f"{participant_data.participant_id}_trajectory_dual_view.png"
        path = os.path.join(EXPORTS_FOLDER, filename)
        plt.savefig(path, bbox_inches='tight')
        logging.info(f"Saved to {path}")
    
    if close_plot:
        plt.show()
        plt.close('all')
    else:
        plt.show()

def plot_mean_trajectories_by_metric(participants: dict, summary_df: pd.DataFrame, image_path: str, n_points=100000, save_file=True, close_plot=True):
    """
    Plots average trajectory grouped by TotalExperimentTime,
    binned into 3 quantiles (Low, Medium, High).

    Args:
        participants (dict): participant_id → MuseumVRParticipantData
        summary_df (pd.DataFrame): Per_Participant_Summary with 'ParticipantID' and 'TotalExperimentTime'
        image_path (str): path to museum top-view image
        n_points (int): number of resampled points per trajectory
    """
    import os
    from PIL import Image

    if image_path not in image_dict:
        raise ValueError(f"Image path '{image_path}' not found in image_dict.")

    image_metadata = image_dict[image_path]
    background = Image.open(image_path)

    # Bin participants into 3 groups by TotalExperimentTime
    summary_df = summary_df[["ParticipantID", "TotalExperimentTime"]].dropna()
    summary_df["ParticipantID"] = summary_df["ParticipantID"].astype(int)

    try:
        binned = pd.qcut(summary_df["TotalExperimentTime"], q=3, duplicates="drop")
        bin_count = binned.nunique()
        label_map = {
            1: ["Low"],
            2: ["Low", "High"],
            3: ["Low", "Medium", "High"]
        }
        labels = label_map[bin_count]
        summary_df["Group"] = pd.qcut(summary_df["TotalExperimentTime"], q=3, labels=labels, duplicates="drop")
        if bin_count < 3:
            logging.warning(f"Only {bin_count} bins were created for TotalExperimentTime. Some groups may be missing.")
    except ValueError as e:
        logging.error(f"Could not create bins: {e}")
        return

    group_map = dict(zip(summary_df["ParticipantID"], summary_df["Group"]))
    group_colors = {"Low": "blue", "Medium": "green", "High": "orange"}
    trajectories = {label: [] for label in labels}

    for participant in participants.values():
        try:
            pid = int(participant.participant_id)
            if pid not in group_map:
                logging.info(f"Participant {pid} not in metric group map")
                continue

            df = participant.dataframes.get("ContinuousData")
            if df is None or df.empty:
                logging.info(f"No or empty ContinuousData for {pid}")
                continue

            start_time = participant.trials_data.iloc[0]["StartTime"]
            df = df[df["Time"] >= start_time]
            coords = df[["Head_Position_x", "Head_Position_Z"]].dropna().values

            if len(coords) < 10:
                logging.info(f"Too few coordinates for {pid}")
                continue

            # Resample
            orig_idx = np.linspace(0, 1, len(coords))
            target_idx = np.linspace(0, 1, n_points)
            interp_x = np.interp(target_idx, orig_idx, coords[:, 0])
            interp_z = np.interp(target_idx, orig_idx, coords[:, 1])
            pixels = [convert_unity_units_to_image_px(x, z, image_metadata) for x, z in zip(interp_x, interp_z)]

            group = group_map[pid]
            trajectories[group].append(pixels)

        except Exception as e:
            logging.warning(f"Skipping participant {participant.participant_id}: {e}")
            continue

    # Plot
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.imshow(background)
    ax.set_title("Mean Trajectories Grouped by TotalExperimentTime")
    ax.axis("off")

    for group, traj_list in trajectories.items():
        if not traj_list:
            continue
        traj_array = np.array(traj_list)
        mean_path = np.nanmean(traj_array, axis=0)
        std_path = np.nanstd(traj_array, axis=0)
        x, y = mean_path[:, 0], mean_path[:, 1]
        x_std, y_std = std_path[:, 0], std_path[:, 1]

        ax.plot(x, y, label=f"{group} TotalExperimentTime", color=group_colors.get(group, "gray"), linewidth=2)
        ax.fill_betweenx(y, x - x_std, x + x_std, color=group_colors.get(group, "gray"), alpha=0.2)

    ax.legend(loc='lower right')

    if save_file:
        os.makedirs(EXPORTS_FOLDER, exist_ok=True)
        filename = "mean_trajectories_by_TotalExperimentTime.png"
        plt.savefig(os.path.join(EXPORTS_FOLDER, filename), bbox_inches='tight')
        logging.info(f"Saved {filename}")

    if close_plot:
        plt.show()
        plt.close()
    else:
        plt.show()



# endregion

# region ---- Different plots ----

def plot_gaze_per_painting(participants: dict):
    """
    Plot a boxplot of gaze percent per painting across participants.
    Expects a dict: {participant_id: MuseumVRParticipantData}
    """
    all_summaries = pd.concat([
        participant.get_per_painting_summary()
        for participant in participants.values()
    ])

    sns.boxplot(data=all_summaries, x="Painting", y="GazeTime")
    plt.title("Gaze Time by Painting Across Participants")
    plt.xticks(rotation=45)
    plt.tight_layout()
    filename = "Gaze Time by Painting.png"
    path = os.path.join(EXPORTS_FOLDER, filename)
    plt.savefig(path, bbox_inches='tight')
    plt.show()

def plot_gaze_percent_per_painting(participants: dict):
    """
    Plot a boxplot of gaze percent per painting across participants.
    Expects a dict: {participant_id: MuseumVRParticipantData}
    """
    all_summaries = pd.concat([
        participant.get_per_painting_summary()
        for participant in participants.values()
    ])

    sns.boxplot(data=all_summaries, x="Painting", y="GazePercent")
    plt.title("Gaze Percent During Audioguide")
    plt.xticks(rotation=45)
    plt.tight_layout()
    filename = "Gaze Percent During Audioguide.png"
    path = os.path.join(EXPORTS_FOLDER, filename)
    plt.savefig(path, bbox_inches='tight')
    plt.show()

def plot_individual_voting_bars(questionnaire: pd.DataFrame, save_file=True, close_plot=True):
    """
    Plots separate bar charts for each voting question (column 16+),
    showing % of participants who voted for Option 1 and Option 2.
    """
    voting_columns = questionnaire.columns[14:]

    for col in voting_columns:
        votes = questionnaire[col].dropna().astype(str)
        total = len(votes)
        if total == 0:
            continue

        percent_1 = (votes == "1").sum() / total * 100
        percent_2 = (votes == "2").sum() / total * 100

        df = pd.DataFrame({
            "Option": ["Option 1", "Option 2"],
            "Percent": [percent_1, percent_2]
        })

        plt.figure(figsize=(5, 6))
        sns.barplot(data=df, x="Option", y="Percent", palette=["#4C72B0", "#55A868"])
        plt.title(f"Voting Distribution for {col}")
        plt.ylim(0, 100)
        plt.ylabel("Percentage (%)")
        plt.tight_layout()

        if save_file:
            os.makedirs(EXPORTS_FOLDER, exist_ok=True)
            filename = f"{col}_VotingBar.png".replace(" ", "_")
            path = os.path.join(EXPORTS_FOLDER, filename)
            plt.savefig(path, bbox_inches='tight')
            logging.info(f"Saved voting plot for {col} to {path}")

        if close_plot:
            plt.show()
            plt.close()
        else:
            plt.show()


#endregion


# region ---- helpers ----

def gaze_percent_legend_labels(participant_data: participantData) -> list[str]:
    legend_labels = []

    for _, row in default_tile_positions.iterrows():
        painting_name = row['name']

        # Gaze percentage
        df = participant_data.dataframes["ContinuousData"]
        filtering_func = participant_data._filter_by_trial_and_tile
        gazed_time, gaze_percent = participant_data.calculate_gaze_time(
            piece_name=painting_name,
            fitering_function=filtering_func
        )

        label = f"{painting_name}: {gaze_percent:.1f}%"
        legend_labels.append(label)

    return legend_labels




def compute_trajectory_data(df, image_metadata, sampling_rate=60, window_size=5):
    coords = df[['Head_Position_x', 'Head_Position_Z']].values
    unity_x, unity_z = coords[:, 0], coords[:, 1]

    pixel_points = np.array([convert_unity_units_to_image_px(x, z, image_metadata) for x, z in coords])
    px, py = pixel_points[:, 0], pixel_points[:, 1]

    dx, dy = np.diff(px), np.diff(py)
    distances = np.sqrt(dx**2 + dy**2)
    speed = distances * sampling_rate
    smoothed_speed = convolve1d(speed, np.ones(window_size) / window_size, mode='reflect')

    points = np.array([px, py]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)

    return unity_x, unity_z, px, py, segments, smoothed_speed

def plot_start_end_markers(ax, x, y, start_color="green", end_color="blue"):
    ax.scatter(x[0], y[0], color=start_color, label="Start", zorder=5)
    ax.scatter(x[-1], y[-1], color=end_color, label="End", zorder=5)

def plot_tiles(ax, tile_df_px, label_offset=5):
    for _, row in tile_df_px.iterrows():
        xs = [row['bottom-left_x'], row['top-left_x'], row['top-right_x'],
              row['bottom-right_x'], row['bottom-left_x']]
        ys = [row['bottom-left_z'], row['top-left_z'], row['top-right_z'],
              row['bottom-right_z'], row['bottom-left_z']]
        ax.plot(xs, ys, color='black', linewidth=1.5, zorder=1)

        side = get_tile_label_position(row['name'])
        if side == "left":
            label_x = row["top-left_x"] + label_offset
            label_y = row["top-left_z"] + label_offset
            ha = "left"
        else:
            label_x = row["top-right_x"] - label_offset
            label_y = row["top-right_z"] + label_offset
            ha = "right"

        ax.text(label_x, label_y, row['name'], ha=ha, va='top',
                rotation=90, fontsize=8, color='black', zorder=2)

def convert_tile_position_to_image_px(image_reference_points: dict):
    """
    Convert Unity tile positions to pixel coordinates using the affine transform.
    
    Args:
        image_reference_points (dict): Contains 'img_origin', 'bottom_left_barrier', 'top_right_barrier'
    
    Returns:
        pd.DataFrame: Tile positions in pixel coordinates, same structure as default_tile_positions
    """
    # Access the Unity tile positions
    unity_df = default_tile_positions.copy()

    # Columns to convert
    coord_columns = [
        'bottom-left_x', 'bottom-left_z',
        'top-left_x', 'top-left_z',
        'top-right_x', 'top-right_z',
        'bottom-right_x', 'bottom-right_z'
    ]

    # Create a new dict to build the pixel DataFrame
    pixel_rows = []

    for _, row in unity_df.iterrows():
        pixel_row = {'name': row['name']}
        for prefix in ['bottom-left', 'top-left', 'top-right', 'bottom-right']:
            x = row[f"{prefix}_x"]
            z = row[f"{prefix}_z"]
            px, py = convert_unity_units_to_image_px(x, z, image_reference_points)
            pixel_row[f"{prefix}_x"] = px
            pixel_row[f"{prefix}_z"] = py
        pixel_rows.append(pixel_row)

    return pd.DataFrame(pixel_rows)

def convert_unity_units_to_image_px(x: float, z: float, image_reference_points: dict) -> tuple[float, float]:
    """
    Convert Unity coordinates (x, z) to pixel coordinates (x_px, y_px) in the image with affine transformation.

    Args:
        x (float): Unity x-coordinate
        z (float): Unity z-coordinate
        image_reference_points (dict): Contains:
            - 'img_origin': (x_px, y_px)
            - 'bottom_left_barrier': (x_px, y_px)
            - 'top_right_barrier': (x_px, y_px)

    Returns:
        tuple: Pixel coordinates (x_px, y_px)
    """
    
    # ---- full 3 reference points for affine transformation ----
    # Image pixel reference points
    img_origin = np.array(image_reference_points["img_origin"])
    img_bottom_left_barrier = np.array(image_reference_points["bottom_left_barrier"])
    img_top_right_barrier = np.array(image_reference_points["top_right_barrier"])

    # Unity world-space reference points
    src_points = np.array([unity_origin, unity_bottom_left_barrier, unity_top_right_barrier], dtype=np.float32)
    dst_points = np.array([img_origin, img_bottom_left_barrier, img_top_right_barrier], dtype=np.float32)

    # Compute affine transform: Unity → Image
    affine_transformation_matrix = cv2.getAffineTransform(src_points, dst_points)
    
    # Apply to input point (x, z)
    point = np.array([[x, z]], dtype=np.float32)
    transformed = cv2.transform(np.array([point]), affine_transformation_matrix)[0][0]

    return float(transformed[0]), float(transformed[1])

def get_tile_label_position(name: str) -> str:
    """Return 'left' or 'right' label position for a given tile name."""
    left_labels = {"janco", "de chirico", "pollock", "van dongen"}
    return "left" if name.lower() in left_labels else "right"

# endregion

# region ---- debug functions ----

def debug_plot_unity_to_image_point_dual(x: float, z: float, image_path: str):
    """
    Plot both Unity and image coordinate systems:
    - Unity view: reference points and input point in Unity units
    - Image view: reference points and projected points overlaid on image

    Args:
        x (float): Unity x coordinate
        z (float): Unity z coordinate
        image_path (str): Path to the top-view image (must exist in image_dict)
    """
    if image_path not in image_dict:
        raise ValueError(f"Image path '{image_path}' not found in image_dict.")

    image_reference_points = image_dict[image_path]
    img = Image.open(image_path)

    # Unity reference points
    unity_refs = {
        "unity_origin": UNITY_ORIGIN,
        "bottom_left": UNITY_BOTTOM_LEFT_BARRIER,
        "top_right": UNITY_TOP_RIGHT_BARRIER,
        "input": (x, z)
    }

    # Project Unity points into image space
    projected_refs = {
        label: convert_unity_units_to_image_px(pt[0], pt[1], image_reference_points)
        for label, pt in unity_refs.items()
    }

    # Plot both views
    fig, axes = plt.subplots(1, 2, figsize=(16, 8))

    # --- Unity Space ---
    ax1 = axes[0]
    for label, (ux, uz) in unity_refs.items():
        color = 'green' if label == 'input' else 'blue'
        marker = '*' if label == 'input' else 'o'
        ax1.scatter(ux, uz, color=color, s=100, marker=marker)
        ax1.text(ux + 0.05, uz + 0.05, f"{label}\n({ux:.2f}, {uz:.2f})", color=color)
    ax1.set_title("Unity Coordinate System")
    ax1.set_xlabel("Unity X")
    ax1.set_ylabel("Unity Z")
    ax1.axis("equal")
    ax1.grid(True)

    # --- Image Space ---
    ax2 = axes[1]
    ax2.imshow(img)

    for label, (px, py) in projected_refs.items():
        color = 'green' if label == 'input' else 'red'
        marker = '*' if label == 'input' else 'o'
        ax2.scatter(px, py, color=color, s=100, marker=marker)
        ax2.text(px + 5, py, f"{label}\n({px:.1f}, {py:.1f})", color=color)
    ax2.set_title("Image Coordinate System (Pixels)")
    ax2.axis("off")

    plt.tight_layout()
    plt.show()

# endregion

#---test---

#debug_plot_unity_to_image_point_dual(0.5, 0.5, r"Top views\museum_top_iso_grid.png")
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

import os
#region ---- Constants ----

# 3 points to convert Unity coordinates to pixel coordinates with affine transformation
# img_origin: unity zero point in image coordinates (player positioner - spawn point)
# bottom_left_barrier: reference point in image coordinates --- (seahorse statue corner barrier)
# top_right_barrier: reference point in image coordinates --- (Klimt corner barrier)

image_dict = {
    r"Top views\museum_top_iso_grid.png": {
        "img_origin": (224, 113),
        "bottom_left_barrier": (44, 720),
        "top_right_barrier": (331, 32),
    }
    , r"Top views\museum_top_iso.png": {
        "img_origin": (226, 107),
        "bottom_left_barrier": (46, 712),
        "top_right_barrier": (334, 26),
    }
    , r"Top views\museum_top_perspective_grid.png": {
        "img_origin": (286, 133),
        "bottom_left_barrier": (113, 715),
        "top_right_barrier": (391, 55),
    }
    , r"Top views\museum_top_perspective.png": {
        "img_origin": (306, 138),
        "bottom_left_barrier": (133, 720),
        "top_right_barrier": (411, 60),
    }
    , r"sanity": {
        "img_origin": (0,0),
        "bottom_left_barrier": (-2.3101, -2.4648), 
        "top_right_barrier": (0.9805, 5.351),
    }
    , r"Top views\top_view.png": {
        "img_origin": (753,1976),
        "bottom_left_barrier": (1215,409),
        "top_right_barrier": (476,2185),
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

def plot_trajectory_over_image(participant_data : participantData, image_path, save_file=True, sampling_rate=60, window_size=5,close_plot=True):
    """
    Plot trajectory colored by smoothed speed over museum top-view image.

    Args:
        df (pd.DataFrame): Must contain 'Head_Position_x' and 'Head_Position_Z'
        image_path (str): Path to top-view image
        image_metadata (dict): Contains 'img_origin' and 'bottom_left_barrier'
        save_file (bool): Whether to save the plot as a file
        sampling_rate (int): Sampling rate in Hz
        window_size (int): Smoothing window for speed
    """

    if (image_path not in image_dict):
        raise ValueError(f"Image path '{image_path}' not found in image_dict. Available images: {list(image_dict.keys())}")
    
    image_metadata = image_dict[image_path]
    background = Image.open(image_path)

    df = participant_data.dataframes["ContinuousData"]
    # filter out the demo
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

    fig, ax = plt.subplots(figsize=(12, 8))
    ax.imshow(background)
    ax.add_collection(LineCollection(segments, colors=colors, linewidth=2))
    ax.scatter(x[0], y[0], color="green", label="Start", zorder=5)
    ax.scatter(x[-1], y[-1], color="blue", label="End", zorder=5)

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, orientation="vertical", shrink=0.8)
    cbar.set_label("Speed (px/sec)")

    ax.set_title("Trajectory Colored by Smoothed Speed, participant: " + str(participant_data.participant_id))
    ax.axis("off")
    ax.legend(loc="upper right")

    if save_file:
        filename = f"{participant_data.participant_id}_speed_trajectory.png"
        path = os.path.join(EXPORTS_FOLDER, filename)
        plt.savefig(path, bbox_inches='tight')
        logging.info(f"Saved to {path}")
    else:
        plt.show()
    if close_plot:
        plt.close()


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
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8))

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
    else:
        plt.show()

    if close_plot:
        plt.close()

# region ---- helpers ----

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



#---test---

#debug_plot_unity_to_image_point_dual(0.5, 1.0, r"Top views\museum_top_iso_grid.png")
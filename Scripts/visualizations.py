import numpy as np
from participant_data import MuseumVRParticipantData as participantData

import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import Normalize
from scipy.ndimage import convolve1d
from PIL import Image

import os
#region ---- Constants ----

image_dict = {
    r"Top views\museum_top_iso_grid.png": {
        "img_origin": (224, 113),
        "bottom_left_barrier": (44, 720),
    }
    , r"Top views\museum_top_iso.png": {
        "img_origin": (226, 107),
        "bottom_left_barrier": (46, 712),
    }
    , r"Top views\museum_top_perspective_grid.png": {
        "img_origin": (288, 133),
        "bottom_left_barrier": (116, 712),
    }
    , r"Top views\museum_top_perspective.png": {
        "img_origin": (308, 138),
        "bottom_left_barrier": (136, 720),
    }
    , r"sanity.png": {
        "img_origin": (0,0),
        "bottom_left_barrier": (-2.3101, -2.4648),
    }
}

UNITY_ORIGIN = (0, 0)  # Unity coordinates of origin
UNITY_BOTTOM_LEFT_BARRIER = (-2.3101, -2.4648)  # Unity coordinates of reference point

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

    ax.set_title("Trajectory Colored by Smoothed Speed")
    ax.axis("off")
    ax.legend(loc="upper right")

    if save_file:
        filename = f"{participant_data.participant_id}_speed_trajectory.png"
        path = os.path.join(EXPORTS_FOLDER, filename)
        plt.savefig(path, bbox_inches='tight')
        print(f"Saved to {path}")
    else:
        plt.show()
    if close_plot:
        plt.close()


# region ---- helpers ----
def calculate_isometric_projection_ratio(img_origin, bottom_left_barrier, unity_origin=UNITY_ORIGIN, unity_corner=UNITY_BOTTOM_LEFT_BARRIER): 
    """
    Calculates the pixel-per-Unity-unit scale along the isometric projection directions.

    Parameters:
    - unity_origin: (x, z) Unity coordinates of origin
    - unity_corner: (x, z) Unity coordinates of reference point
    - img_origin: (x, y) pixel coordinates of origin in screenshot
    - bottom_left_barrier: (x, y) pixel coordinates of reference point in screenshot

    Returns:
    - scale_per_unit: pixels per Unity unit (Euclidean length ratio)
    """



    # Vector in Unity world (XZ plane)
    unity_vec = np.array([unity_corner[0] - unity_origin[0],
                          unity_corner[1] - unity_origin[1]])  # (x, z)

    # Vector in pixel space (image XY)
    pixel_vec = np.array([bottom_left_barrier[0] - img_origin[0],
                          bottom_left_barrier[1] - img_origin[1]])  # (x, y)

    # Lengths of both vectors
    pixel_len = np.linalg.norm(pixel_vec)
    unity_len = np.linalg.norm(unity_vec)

    # Ratio: pixels per Unity unit
    scale_ratio = pixel_len / unity_len

    return scale_ratio

def convert_unity_units_to_image_px(x: float, z: float, image_metadata: dict) -> tuple[float, float]:
    img_origin = np.array(image_metadata["img_origin"], dtype=np.float64)
    img_ref = np.array(image_metadata["bottom_left_barrier"], dtype=np.float64)

    unity_origin = np.array(UNITY_ORIGIN, dtype=np.float64)
    unity_ref = np.array(UNITY_BOTTOM_LEFT_BARRIER, dtype=np.float64)

    # Direction vectors
    unity_dir = unity_ref - unity_origin
    image_dir = img_ref - img_origin

    # Normalize
    unity_dir /= np.linalg.norm(unity_dir)
    image_dir /= np.linalg.norm(image_dir)

    # Scale ratio (pixels per Unity unit)
    scale_ratio = np.linalg.norm(img_ref - img_origin) / np.linalg.norm(unity_ref - unity_origin)

    # Displacement from Unity origin to (x, z)
    displacement = np.array([x, z]) - unity_origin

    # Project Unity displacement onto Unity direction vector (scalar)
    projected_length = np.dot(displacement, unity_dir)

    # Map to image direction vector
    pixel_offset = projected_length * scale_ratio * image_dir
    pixel_point = img_origin + pixel_offset

    return float(pixel_point[0]), float(pixel_point[1])


# endregion

 # 45 ,711 bottom left barrier at Top views\museum_top_iso.png
 # -2.313, -2.469  bottom left barrier at Unity

(x,y) = convert_unity_units_to_image_px(1.7761, 2.1231, image_dict[r"Top views\museum_top_iso.png"])
print(f"Converted Unity (-2.313, -2.469) to pixel coordinates: ({x}, {y})")
import numpy as np




def calculate_isometric_projection_ratio(img_origin, img_corner):
    """
    Calculates the pixel-per-Unity-unit scale along the isometric projection directions.

    Parameters:
    - unity_origin: (x, z) Unity coordinates of origin
    - unity_corner: (x, z) Unity coordinates of reference point
    - img_origin: (x, y) pixel coordinates of origin in screenshot
    - img_corner: (x, y) pixel coordinates of reference point in screenshot

    Returns:
    - scale_per_unit: pixels per Unity unit (Euclidean length ratio)
    """

    unity_origin = (0, 0)
    unity_corner = (-2.047, -5.213) 

    # Vector in Unity world (XZ plane)
    unity_vec = np.array([unity_corner[0] - unity_origin[0],
                          unity_corner[1] - unity_origin[1]])  # (x, z)

    # Vector in pixel space (image XY)
    pixel_vec = np.array([img_corner[0] - img_origin[0],
                          img_corner[1] - img_origin[1]])  # (x, y)

    # Lengths of both vectors
    pixel_len = np.linalg.norm(pixel_vec)
    unity_len = np.linalg.norm(unity_vec)

    # Ratio: pixels per Unity unit
    scale_ratio = pixel_len / unity_len

    return scale_ratio

# Inputs

img_origin = (216, 107)
img_corner = (396, 712)

print(calculate_isometric_projection_ratio(img_origin, img_corner))

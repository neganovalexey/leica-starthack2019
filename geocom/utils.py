import numpy as np

def sph_to_dec(yaw, pitch, distance):
    return (np.cos(yaw) * np.sin(pitch) * distance,
            np.sin(-yaw) * np.sin(pitch) * distance,
            np.cos(pitch) * distance)

from math import pi
import numpy as np


# FOG parameters
FOG_ROTATION = np.array([[1., 0., 0.], 
                         [0., 1., 0.],
                         [0., 0., 1.]])
FOG_POSITION = np.array([-0.335, -0.035, 0.78])

# LiDAR parameters
LIDAR_ANGLES = np.linspace(-5, 185, num=286) / 360 * 2 * pi
LIDAR_ANGLE_COS = np.cos(LIDAR_ANGLES)
LIDAR_ANGLE_SIN = np.sin(LIDAR_ANGLES)
LIDAR_MAXRANGE = 60
LIDAR_ROTATION = np.array([[0.00130201, 0.796097, 0.605167], 
                           [0.999999, -0.000419027, -0.00160026], 
                           [-0.00102038, 0.605169, -0.796097]])
LIDAR_POSITION = np.array([0.8349, -0.0126869, 1.76416])
N_LIDAR_SAMPLES = 4

# Encoder parameters
ENCODER_RESOLUTION = 4096
ENCODER_LEFT_DIAMETER = 0.623479
ENCODER_RIGHT_DIAMETER = 0.622806
ENCODER_WHEEL_BASE = 1.52439

# Stereo camara parameters
STEREO_BASELINE = 0.475143600050775
STEREO_ROTATION = np.array([[-0.00680499, -0.0153215, 0.99985   ],
                            [-0.999977, 0.000334627, -0.00680066],
                            [-0.000230383, -0.999883, -0.0153234]])
STEREO_POSITION = np.array([1.64239, 0.247401, 1.58411])
STEREO_LEFT_CAMERA = np.array([[ 8.1690378992770002e+02, 5.0510166700000003e-01,
       6.0850726281690004e+02],
       [0., 8.1156803828490001e+02,
       2.6347599764440002e+02], [0., 0., 1. ]])
STEREO_IMG_WIDTH = 1280
STEREO_IMG_HEIGHT = 560
STEREO_Z_RANGE = [-0.3, 0.3]
# General parameters
INIT_LOGODDS = 0
LOGODDS_LOWER = -10
LOGODDS_UPPER = 10
LOGODDS_UPDATE = np.log(4)
NUM_PARTICLES = 100
STEPS_TRAJECTORY = 100
STEPS_FIGURES = 5000
VELOCITY_NOISE = 1e-10
A_VELOCITY_NOISE = 1e-11
MAP_SIZE = [-100, 1400, -1400, 100]
MAP_RESOLUTION = 0.3
RESAMPLE_THRESHOLD = 0.01
IMG_OUTPUT_PATH = "img"
CORRELATION_SERACHGRID_SIZE = 0.3
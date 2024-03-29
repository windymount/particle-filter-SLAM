from cmath import pi
from turtle import pos
import pandas as pd
import cv2
import numpy as np
import matplotlib.pyplot as plt; plt.ion()
from mpl_toolkits.mplot3d import Axes3D
from params import LIDAR_MAXRANGE, ENCODER_LEFT_DIAMETER, ENCODER_RESOLUTION, ENCODER_RIGHT_DIAMETER, STEREO_BASELINE, STEREO_IMG_HEIGHT, STEREO_IMG_WIDTH, STEREO_LEFT_CAMERA, STEREO_MIN_DISPARITY
import time
import os

def tic():
    return time.time()
def toc(tstart, name="Operation"):
    print('%s took: %s sec.\n' % (name,(time.time() - tstart)))


def compute_stereo():
    """
    
    Compute the disparity map for stereo images.
    
    """
    if not os.path.exists("data/disparity.npy"):
        path_l = 'data/stereo_left'
        path_r = 'data/stereo_right'
        stereo = cv2.StereoBM_create(numDisparities=64, blockSize=9) 
        time_stamp_array = np.zeros(len(os.listdir(path_l)), dtype=np.int64)
        disparity_array = None
        for i, filename in enumerate(os.listdir(path_l)):
            time_stamp = os.path.splitext(filename)[0]
            image_l = cv2.imread(os.path.join(path_l, filename), 0)
            image_r = cv2.imread(os.path.join(path_r, filename), 0)
            if image_l is None or image_r is None:
                continue
            image_l = cv2.cvtColor(image_l, cv2.COLOR_BAYER_BG2BGR)
            image_r = cv2.cvtColor(image_r, cv2.COLOR_BAYER_BG2BGR)
            image_l_gray = cv2.cvtColor(image_l, cv2.COLOR_BGR2GRAY)
            image_r_gray = cv2.cvtColor(image_r, cv2.COLOR_BGR2GRAY)

            if disparity_array is None:
                disparity_array = np.zeros((len(os.listdir(path_l)), *image_l.shape[:-1]), dtype=np.float16)
            # You may need to fine-tune the variables `numDisparities` and `blockSize` based on the desired accuracy
            disparity = stereo.compute(image_l_gray, image_r_gray).astype(np.float32) / 16
            disparity[disparity < 0] = 0
            disparity_array[i, :, :] = disparity
            time_stamp_array[i] = time_stamp
        nonzero_idx = (time_stamp_array != 0)
        time_stamp_array, disparity_array = time_stamp_array[nonzero_idx], disparity_array[nonzero_idx]
        np.save("data/disparity.npy", disparity_array)
        np.save("data/time_stamp.npy", time_stamp_array)


def calculate_camera():
    # Calculate transformation from camera parameters. (For further recover 3d coordinate from depth)
    inv_mat = np.linalg.inv(STEREO_LEFT_CAMERA)
    map_x, map_y = np.meshgrid(np.arange(STEREO_IMG_WIDTH), np.arange(STEREO_IMG_HEIGHT))
    map_co = np.stack((map_x, map_y, np.ones_like(map_x)))
    world_co = np.einsum("ij,jkl", inv_mat, map_co)
    return world_co


def recover_space_coordinate(camera_trans, disparity):
    """
    
    Recover 3D coordinate for each pixel. (In camera frame)
    
    """
    fsu = STEREO_LEFT_CAMERA[0, 0]
    valid_idx = disparity >= STEREO_MIN_DISPARITY
    depth_map = np.zeros_like(disparity, dtype=np.float32)
    depth_map[valid_idx] = fsu * STEREO_BASELINE / disparity[valid_idx]
    world_co = camera_trans * depth_map
    # plt.imshow((depth_map))
    # plt.show(block=True)
    # Optical to Regular
    # world_co = world_co[[2, 0, 1], :, :]
    # world_co[1:, :, :] *= -1
    return world_co



def read_data_from_csv(filename):
    '''
    INPUT 
    filename        file address

    OUTPUT 
    timestamp       timestamp of each observation
    data            a numpy array containing a sensor measurement in each row
    '''
    data_csv = pd.read_csv(filename, header=None)
    data = data_csv.values[:, 1:]
    timestamp = data_csv.values[:, 0]
    return timestamp, data


def mapCorrelation(im, x_im, y_im, vp, xs, ys, ptype):
    '''
    INPUT 
    im              the map 
    x_im,y_im       physical x,y positions of the grid map cells
    vp[0:2,:]       occupied x,y positions from range sensor (in physical unit)  
    xs,ys           physical x,y,positions you want to evaluate "correlation" 
    ptype           specify the point is occupied or free
    

    OUTPUT 
    c               sum of the cell values of all the positions hit by range sensor
    '''
    nx = im.shape[0]
    ny = im.shape[1]
    xmin = x_im[0]
    xmax = x_im[-1]
    xresolution = (xmax-xmin)/(nx-1)
    ymin = y_im[0]
    ymax = y_im[-1]
    yresolution = (ymax-ymin)/(ny-1)
    nxs = xs.size
    nys = ys.size
    cpr = np.zeros((nxs, nys))
    for jy in range(0,nys):
        y1 = vp[1,:] + ys[jy] # 1 x 1076
        iy = np.int16(np.round((y1-ymin)/yresolution))
        for jx in range(0,nxs):
            x1 = vp[0,:] + xs[jx] # 1 x 1076
            ix = np.int16(np.round((x1-xmin)/xresolution))
            points = im[ix,iy]
            cpr[jx, jy] = np.sum(points * ptype) - np.sum(np.log(1 + np.exp(points)))
    return cpr




def bresenham2D(sx, sy, ex, ey):
    '''
    Bresenham's ray tracing algorithm in 2D.
    Inputs:
        (sx, sy)	start point of ray
        (ex, ey)	end point of ray
    '''
    sx = int(round(sx))
    sy = int(round(sy))
    ex = int(round(ex))
    ey = int(round(ey))
    dx = abs(ex-sx)
    dy = abs(ey-sy)
    steep = abs(dy)>abs(dx)
    if steep:
        dx,dy = dy,dx # swap 

    if dy == 0:
        q = np.zeros((dx+1,1))
    else:
        q = np.append(0,np.greater_equal(np.diff(np.mod(np.arange( np.floor(dx/2), -dy*dx+np.floor(dx/2)-1,-dy),dx)),0))
    if steep:
        if sy <= ey:
            y = np.arange(sy,ey+1)
        else:
            y = np.arange(sy,ey-1,-1)
        if sx <= ex:
            x = sx + np.cumsum(q)
        else:
            x = sx - np.cumsum(q)
    else:
        if sx <= ex:
            x = np.arange(sx,ex+1)
        else:
            x = np.arange(sx,ex-1,-1)
        if sy <= ey:
            y = sy + np.cumsum(q)
        else:
            y = sy - np.cumsum(q)
    return np.vstack((x,y))
    

def test_bresenham2D():
    import time
    sx = 0
    sy = 1
    print("Testing bresenham2D...")
    r1 = bresenham2D(sx, sy, 10, 5)
    r1_ex = np.array([[0, 1, 2, 3, 4, 5, 6, 7, 8, 9,10],[1,1,2,2,3,3,3,4,4,5,5]])
    r2 = bresenham2D(sx, sy, 9, 6)
    r2_ex = np.array([[0,1,2,3,4,5,6,7,8,9],[1,2,2,3,3,4,4,5,5,6]])	
    if np.logical_and(np.sum(r1 == r1_ex) == np.size(r1_ex),np.sum(r2 == r2_ex) == np.size(r2_ex)):
        print("...Test passed.")
    else:
        print("...Test failed.")

    # Timing for 1000 random rays
    num_rep = 1000
    start_time = time.time()
    for i in range(0,num_rep):
        x,y = bresenham2D(sx, sy, 500, 200)
    print("1000 raytraces: --- %s seconds ---" % (time.time() - start_time))

    
    
def show_lidar():
    _, lidar_data = read_data_from_csv('data/sensor_data/lidar.csv')
    angles = np.linspace(-5, 185, 286) / 180 * np.pi
    ranges = lidar_data[0, :]
    plt.figure()
    ax = plt.subplot(111, projection='polar')
    ax.plot(angles, ranges)
    ax.set_rmax(80)
    ax.set_rticks([0.5, 1, 1.5, 2])  # fewer radial ticks
    ax.set_rlabel_position(-22.5)  # get radial labels away from plotted line
    ax.grid(True)
    ax.set_title("Lidar scan data", va='bottom')
    plt.show(block=True)
  

def correct_lidar(lidar_data):
    # Correct lidar_data
    lidar_data[lidar_data == 0] = LIDAR_MAXRANGE
    lidar_data[lidar_data > LIDAR_MAXRANGE] = LIDAR_MAXRANGE
    return lidar_data
    

def get_angular_velocity(fog_path):
    # Get angular_velocity from FOG data
    time_stamp, FOG_data = read_data_from_csv(fog_path)
    time_difference = time_stamp[1:] - time_stamp[:-1]
    angular_velocity = FOG_data[1:] / time_difference[:, None]
    return time_stamp[:-1], angular_velocity


def physics2map(map, xm, ym, xphy, yphy):
    """
    
    Transform from physical coordinate to map index.
    :param map: occupancy map
    :param xm: x position of map (physical)
    :param ym: y position of map (physical)
    :param xphy: x physical coordinate of points
    :param yphy: y physical coordinate of points
    :return xidx: x index in map
    :return yidx: y index in map

    """
    nx = map.shape[0]
    ny = map.shape[1]
    xmin = xm[0]
    xmax = xm[-1]
    xresolution = (xmax-xmin)/(nx-1)
    ymin = ym[0]
    ymax = ym[-1]
    yresolution = (ymax-ymin)/(ny-1)
    xidx = np.round((xphy - xmin) / xresolution)
    yidx = np.round((yphy - ymin) / yresolution)
    assert np.all(xidx > 0) and np.all(xidx < nx) and np.all(yidx > 0) and np.all(yidx < ny), "Point out of map!"
    return xidx.astype(np.int16), yidx.astype(np.int16)


def show_particles_on_map(map, xm, ym, position):
    xidx, yidx = physics2map(map, xm, ym, position[0, :], position[1, :])
    map[xidx, yidx] = 1
    return map


def get_velocity(encoder_path):
    time_stamp, encoder_data = read_data_from_csv(encoder_path)
    time_difference = time_stamp[1:] - time_stamp[:-1]
    velocity = (encoder_data[1:] - encoder_data[:-1]) / time_difference[:, None]
    velocity = velocity / ENCODER_RESOLUTION
    velocity = velocity * pi * np.array([ENCODER_LEFT_DIAMETER, ENCODER_RIGHT_DIAMETER])
    return time_stamp[:-1], np.mean(velocity, axis=1)


def transform_2d_to_3d(position, orient):
    rotation = np.array([[np.cos(orient), -np.sin(orient), 0], 
                         [np.sin(orient), np.cos(orient),  0], 
                         [0, 0, 1]])
    return np.concatenate([position, np.zeros(1)]), rotation


def transform_orient_to_mat(orient):
    m_cos, m_sin = np.cos(orient), np.sin(orient)
    return np.reshape(np.transpose(np.array([[m_cos, -m_sin], [m_sin, m_cos]]),axes=[2, 0, 1]), newshape=(-1, 2))


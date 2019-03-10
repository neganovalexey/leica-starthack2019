import cv2
import numpy as np
import trimesh
import pyrender
from math import cos, sin, pi


v_fov = 50
h_fov = 70


class VideoCamera(object):
    def __init__(self, width, height):
        # Using OpenCV to capture from device 0. If you have trouble capturing
        # from a webcam, comment the line below out and use a video file
        # instead.
        self.video = cv2.VideoCapture(1) # 0 is laptop webcam, 1 is external
        self.video.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.video.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        self.feature_params = {
            'maxCorners': 100, # 100
            'qualityLevel': 0.3,
            'minDistance': 7,
            'blockSize': 7
        }

        # Parameters for lucas kanade optical flow
        self.lk_params = {
            'winSize': (15, 15),
            'maxLevel': 2,
            'criteria': (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03)
        }

        # camera window size, px
        self.height = 720
        self.width = 1280
        # Angle
        self.phi = 0.0
        self.base_phi = 0.0
        self.theta = 0.0
        self.base_theta = 0.0
        self.mean_distance_to_points = 300 # cm

        self._init_state()

    def _init_state(self):
        # Create some random colors
        self.color = np.random.randint(0, 255, (100, 3))

        # Take first frame and find corners in it
        _, self.old_frame = self.video.read()
        self.old_gray = cv2.cvtColor(self.old_frame, cv2.COLOR_BGR2GRAY)
        self.p0 = cv2.goodFeaturesToTrack(self.old_gray, mask=None, **self.feature_params)
        self.good_features_size = len(self.p0)
        self.init_coords = self.p0
        self.base_phi = self.phi
        self.base_theta = self.theta

        # Create a mask image for drawing purposes
        self.mask = np.zeros_like(self.old_frame)
    
    def __del__(self):
        self.video.release()

    def get_frame(self, draw_traces=False):
        success, frame = self.video.read()

        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # calculate optical flow
        p1, st, err = cv2.calcOpticalFlowPyrLK(self.old_gray, frame_gray, self.p0, None, **self.lk_params)

        # Select good points
        if p1 is None:
            self._init_state()
            return frame, self.phi, self.theta

        good_new = p1[st==1]
        good_old = self.p0[st==1]
        good_init = self.init_coords[st==1]
        delta_px = np.array([[new[0] - init[0], new[1] - init[1]] for new, init in zip(good_new, good_init)])
        if len(delta_px) == 0:
            self._init_state()
            return frame, self.phi, self.theta

        mean_delta = np.mean(delta_px, axis=0)
        if (abs(mean_delta[0]) > self.width / 2 or 
            abs(mean_delta[1]) > self.height / 2 or
            len(good_new) < self.good_features_size / 3):
            print('regenerating features')
            self._init_state()
            return frame, self.phi, self.theta

        self.theta = self.base_theta + mean_delta[0] / self.width * h_fov # 62
        self.phi = self.base_phi + mean_delta[1] / self.height * v_fov # 37

        #print('phi = {},\ttheta = {}'.format(self.phi, self.theta))

        # draw the tracks
        if draw_traces:
            for i,(new,old,init_coords) in enumerate(zip(good_new, good_old, good_init)):
                a,b = new.ravel()
                c,d = old.ravel()
                x,y = init_coords.ravel()
                self.mask = cv2.line(self.mask, (a, b), (c, d), self.color[i].tolist(), 2)
                self.mask = cv2.line(self.mask, (a, b), (x, y), self.color[i].tolist(), 2)
                frame = cv2.circle(frame, (a, b), 5, self.color[i].tolist(), -1)
        img = cv2.add(frame, self.mask)

        k = cv2.waitKey(30) & 0xff
        if k == 27:
            self._init_state()
            return img, self.phi, self.theta

        # Now update the previous frame and previous points
        self.old_gray = frame_gray.copy()
        self.p0 = good_new.reshape(-1, 1, 2)
        self.init_coords = good_init.reshape(-1, 1, 2)

        return img, self.phi, self.theta


class AugmentedSpace(object):
    def __init__(self, width, height, objects):
        self.scene = pyrender.Scene(bg_color=np.zeros(4))
        for tmesh in objects:
            tmesh.apply_transform(np.array([
                [ 1.0, 0.0, 0.0, 0.0],
                [ 0.0, 0.0, 1.0, 0.0],
                [ 0.0, 1.0, 0.0, 0.0],
                [ 0.0, 0.0, 0.0, 1.0]
            ]))
            self.scene.add(pyrender.Mesh.from_trimesh(tmesh))
        light = pyrender.PointLight(color=np.ones(3), intensity=30.0)
        self.scene.add(light)
        self.renderer = pyrender.OffscreenRenderer(width, height)

    def get_frame(self, cam_x, cam_y, cam_z, phi, theta):
        camera = pyrender.PerspectiveCamera(yfov = v_fov * pi / 180)
        camera_rot_y = np.array([
               [1.0, 0.0, 0.0, 0.0],
               [0.0, cos(phi), -sin(phi), 0.0],
               [0.0, sin(phi), cos(phi), 0.0],
               [0.0, 0.0, 0.0, 1.0],
            ])
        camera_rot_x = np.array([
               [cos(theta), 0.0, sin(theta), 0.0],
               [0.0, 1.0, 0.0, 0.0],
               [-sin(theta), 0.0, cos(theta), 0.0],
               [0.0, 0.0, 0.0, 1.0],
            ])
        camera_rot_z = np.eye(4)
        # camera_rot_z = np.array([
        #        [1, 0.0, 0.0, 0.0],
        #        [0.0, cos(gamma), sin(gamma), 0.0],
        #        [0.0, -sin(gamma), cos(gamma), 0.0],
        #        [0.0, 0.0, 0.0, 1.0],
        #     ])
        camera_pose = np.matmul(np.matmul(camera_rot_y, camera_rot_x), camera_rot_z)
        camera_pose[0][3] = cam_x
        camera_pose[1][3] = cam_y
        camera_pose[2][3] = cam_z
        # camera_pose =  np.array([
        #        [1.0, 0.0, 0.0, -20],
        #        [0.0, 1.0, 0.0, 3],
        #        [0.0, 0.0, 1.0, 150],
        #        [0.0, 0.0, 0.0, 1.0],
        #     ])
        camnode = self.scene.add(camera, pose=camera_pose)
        
        # Set up the light
        color, depth = self.renderer.render(self.scene)
        self.scene.remove_node(camnode)
        return color, depth

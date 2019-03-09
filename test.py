import cv2
import numpy as np
import trimesh
import pyrender
import matplotlib.pyplot as plt

from flask import Flask, render_template, Response


class VideoCamera(object):
    def __init__(self, width, height):
        # Using OpenCV to capture from device 0. If you have trouble capturing
        # from a webcam, comment the line below out and use a video file
        # instead.
        self.video = cv2.VideoCapture(1) # 0 is laptop webcam, 1 is external
        self.video.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.video.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        self.feature_params = {
            'maxCorners': 100,
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
        self._init_state()

    def _init_state(self):
        # Create some random colors
        self.color = np.random.randint(0, 255, (100, 3))

        # Take first frame and find corners in it
        _, self.old_frame = self.video.read()
        self.old_gray = cv2.cvtColor(self.old_frame, cv2.COLOR_BGR2GRAY)
        self.p0 = cv2.goodFeaturesToTrack(self.old_gray, mask=None, **self.feature_params)

        # Create a mask image for drawing purposes
        self.mask = np.zeros_like(self.old_frame)
    
    def __del__(self):
        self.video.release()
    
    def get_frame(self):
        success, frame = self.video.read()

        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # calculate optical flow
        p1, st, err = cv2.calcOpticalFlowPyrLK(self.old_gray, frame_gray, self.p0, None, **self.lk_params)

        # Select good points
        if p1 is None:
            self._init_state()
            return frame

        good_new = p1[st==1]
        good_old = self.p0[st==1]

        # draw the tracks
        for i,(new,old) in enumerate(zip(good_new, good_old)):
            a,b = new.ravel()
            c,d = old.ravel()
            self.mask = cv2.line(self.mask, (a, b), (c, d), self.color[i].tolist(), 2)
            frame = cv2.circle(frame, (a, b), 5, self.color[i].tolist(), -1)
        img = cv2.add(frame, self.mask)

        k = cv2.waitKey(30) & 0xff
        if k == 27:
            self._init_state()
            return img

        # Now update the previous frame and previous points
        self.old_gray = frame_gray.copy()
        self.p0 = good_new.reshape(-1, 1, 2)

        return img


class AugmentedSpace(object):
    def __init__(self, width, height):
        fuze_trimesh = trimesh.load('teapot.obj')
        mesh = pyrender.Mesh.from_trimesh(fuze_trimesh) #, material=
        self.scene = pyrender.Scene(bg_color=np.zeros(4))
        self.scene.add(mesh)

        camera = pyrender.PerspectiveCamera(yfov=np.pi / 3.0)
        s = np.sqrt(2)/2
        camera_pose = np.array([
               [1.0, 0.0, 0.0, 0.0],
               [0.0, 1.0, 0.0, 3.0],
               [0.0, 0.0, 1.0, 7.0],
               [0.0, 0.0, 0.0, 1.0],
            ])
        self.scene.add(camera, pose=camera_pose)
        
        # Set up the light
        light = pyrender.PointLight(color=np.ones(3), intensity=30.0)
        self.scene.add(light, pose=camera_pose)
        
        self.renderer = pyrender.OffscreenRenderer(width, height)

    def get_frame(self):
        color, depth = self.renderer.render(self.scene)
        return color, depth


def cv_to_jpg(image):
    # We are using Motion JPEG, but OpenCV defaults to capture raw images,
    # so we must encode it into JPEG in order to correctly display the
    # video stream.
    ret, jpeg = cv2.imencode('.jpg', image)
    return jpeg.tobytes()


app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


def gen(camera, ar):
    while True:
        frame = camera.get_frame()
        if frame is None:
            continue
        ar_color, ar_depth = ar.get_frame()
        mask = np.repeat(np.expand_dims(ar_depth > 0.01, -1), 3, axis=-1) # 3 channels
        frame = np.where(mask, ar_color, frame)
        jpg = cv_to_jpg(frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpg + b'\r\n\r\n')


@app.route('/video_feed')
def video_feed():
    w = 1280
    h = 720
    return Response(gen(VideoCamera(w, h), AugmentedSpace(w, h)),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=2122, debug=True)

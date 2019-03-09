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
        # If you decide to use video.mp4, you must have this file in the folder
        # as the main.py.
        # self.video = cv2.VideoCapture('video.mp4')
    
    def __del__(self):
        self.video.release()
    
    def get_frame(self):
        success, image = self.video.read()
        return image

class AugumentedSpace(object):
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
    return Response(gen(VideoCamera(w, h), AugumentedSpace(w, h)),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=2122, debug=True)

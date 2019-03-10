import argparse
import cv2
import numpy as np

from flask import Flask, render_template, Response

from ar import VideoCamera, AugmentedSpace
from room_model_builder import RoomModelBuilder

parser = argparse.ArgumentParser(description='MS60 CLI')
parser.add_argument('--host',   default='192.168.12.59',  metavar='MS60 host')
parser.add_argument('--port',   default=1212,             metavar='MS60 port')
args = parser.parse_args()



room_builder = RoomModelBuilder()
#room_builder.measure_new_vertices(args.host, args.port, True, 42, 40)
room_model = room_builder.build()

import trimesh
import pyrender

#scene = pyrender.Scene()

st_mesh = trimesh.load('../models/StartHack_StairsOnly.obj')
st_mesh.apply_transform(np.array([
       [0.1, 0.0, 0.0, 5.8],
       [0.0, 0.1, 0.0, 1.0],
       [0.0, 0.0, 0.1, -1.25],
       [0.0, 0.0, 0.0, 1.0],
    ]))
objects = [trimesh.boolean.difference([st_mesh, room_model], engine='blender')]
#scene.add(pyrender.Mesh.from_trimesh(objects[0]))
#mesh = pyrender.Mesh.from_trimesh(st_mesh)
#scene.add(mesh)
#cmesh = pyrender.Mesh.from_trimesh(room_model)
#scene.add(cmesh)
#pyrender.Viewer(scene, use_raymond_lighting=True)

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
        frame, phi, theta = camera.get_frame()
        phi = phi * np.pi / 180
        theta = theta * np.pi / 180
        if frame is None:
            continue
        ar_color, ar_depth = ar.get_frame(0.0, -1.0, 0.0, phi, theta)
        mask = np.repeat(np.expand_dims(ar_depth > 0.01, -1), 3, axis=-1) # 3 channels
        frame = np.where(mask, ar_color, frame)
        jpg = cv_to_jpg(frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpg + b'\r\n\r\n')


@app.route('/video_feed')
def video_feed():
    w = 1280
    h = 720
    return Response(gen(VideoCamera(w, h), AugmentedSpace(w, h, objects)),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=2122, debug=True)

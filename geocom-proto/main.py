import argparse
import numpy as np
from room_model_builder import RoomModelBuilder

parser = argparse.ArgumentParser(description='MS60 CLI')
parser.add_argument('--host',   default='192.168.12.59',  metavar='MS60 host')
parser.add_argument('--port',   default=1212,             metavar='MS60 port')
args = parser.parse_args()



room_builder = RoomModelBuilder()
#room_builder.measure_new_vertices(args.host, args.port)
room_model = room_builder.build()

import trimesh
import pyrender
mesh = pyrender.Mesh.from_trimesh(room_model)
scene = pyrender.Scene()
scene.add(mesh)
pyrender.Viewer(scene, use_raymond_lighting=True)

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

scene = pyrender.Scene()

st_mesh = trimesh.load('../models/StartHack_StairsOnly.obj')
st_mesh.apply_transform(np.array([
       [0.1, 0.0, 0.0, 4.0],
       [0.0, 0.1, 0.0, 0.0],
       [0.0, 0.0, 0.1, 0.0],
       [0.0, 0.0, 0.0, 1.0],
    ]))
#st_mesh = pyrender.Mesh.from_trimesh(fuze_trimesh)
#scene.add(st_mesh)
cst_mesh = trimesh.boolean.difference([st_mesh, room_model], engine='blender')
mesh = pyrender.Mesh.from_trimesh(cst_mesh)
scene.add(mesh)
pyrender.Viewer(scene, use_raymond_lighting=True)

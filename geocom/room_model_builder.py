import socket
import random
import numpy as np
import trimesh
from trimesh.base import Trimesh
from geocom import *
from triangulation import Triangulation
import utils

class RoomModelBuilder:
    def __init__(self):
        self.vertices = None
    
    def measure_new_vertices(self, host, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))

        #TMC_DoMeasure(sock, 3, 2) # STOP
        #BAP_SetMeasPrg(sock, 5) # set continious
        #TMC_SetEdmMode(sock, 8) # CONT_REFLESS
        #TMC_DoMeasure(sock, 1, 2)

        COM_NullProc(sock)
        BAP_SetMeasPrg(sock, BAP_USER_MEASPRG.BAP_CONT_REF_STANDARD)
        BAP_SetTargetType(sock, 1)

        v_per_edge = 15
        max_distance = 15 # 1000
        triangulation = Triangulation(v_per_edge, yaw_min=-np.pi*0.6, yaw_max=0.3, pitch_min=0, pitch_max=np.pi * 0.9)
        self.vertices = np.zeros((v_per_edge, v_per_edge, 3))
        for (i, j, yaw, pitch) in triangulation:
            if i == 0 or i == v_per_edge - 1 or j == 0 or j == v_per_edge - 1:
                # edges
                self.vertices[i][j] = utils.sph_to_dec(yaw, pitch, max_distance)
                continue
                
            retries = 3
            while retries > 0:
                AUT_MakePositioning(sock, yaw + random.uniform(-0.03, 0.03), pitch + random.uniform(-0.03, 0.03))
                point = BAP_MeasDistanceAngle(sock)
                if point['RC'] == 0:
                    point = point['P']
                    self.vertices[i][j] = utils.sph_to_dec(point['dHz'], point['dV'], point['dDist'])
                    break
                elif retries > 1:
                    retries -= 1
                    print('bad response ' + str(point) + ', ' + str(retries) + ' retries left')
                else:
                    retries -= 1
                    print('zero retries left, replacing the point')
                    self.vertices[i][j] = utils.sph_to_dec(yaw, pitch, max_distance)

        np.save('vertices', self.vertices)
        sock.close()

    def _load_last_vertices(self):
        self.vertices = np.load('vertices.npy')
    
    
    def _fli_ij(self, i, j):
        return i * self.vertices.shape[1] + j
    
    def _add_face(self, i1, j1, i2, j2, i3, j3):
        self.faces[self.next_face] = (self._fli_ij(i1, j1), self._fli_ij(i3, j3), self._fli_ij(i2, j2))
        self.face_normals[self.next_face] = np.cross(self.vertices[i3][j3] - self.vertices[i1][j1],
                                                     self.vertices[i2][j2] - self.vertices[i1][j1])
        self.next_face += 1

    def build(self):
        self._load_last_vertices()
        
        self.faces = np.zeros(((self.vertices.shape[0] - 1) * (self.vertices.shape[1] - 1) * 2, 3), dtype=int)
        self.face_normals = np.zeros((self.faces.shape[0], 3))
        self.next_face = 0
        for i in range(self.vertices.shape[0] - 1):
            for j in range(self.vertices.shape[1] - 1):
                self._add_face(i, j, i+1, j, i, j+1)
                self._add_face(i, j+1, i+1, j, i+1, j+1)
        
        return Trimesh(vertices=self.vertices.reshape(-1, 3),
                       faces=self.faces,
                       #face_normals=self.face_normals,
                       process = False)

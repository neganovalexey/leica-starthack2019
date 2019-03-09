import argparse
import socket
import random
import numpy as np
from triangulation import Triangulation
from geocom import *
import utils

parser = argparse.ArgumentParser(description='MS60 CLI')
parser.add_argument('--host',   default='192.168.12.59',  metavar='MS60 host')
parser.add_argument('--port',   default=1212,             metavar='MS60 port')
args = parser.parse_args()

def measure_vertices():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((args.host, args.port))

    #TMC_DoMeasure(sock, 3, 2) # STOP
    #BAP_SetMeasPrg(sock, 5) # set continious
    #TMC_SetEdmMode(sock, 8) # CONT_REFLESS
    #TMC_DoMeasure(sock, 1, 2)

    COM_NullProc(sock)
    BAP_SetMeasPrg(sock, BAP_USER_MEASPRG.BAP_CONT_REF_STANDARD)
    BAP_SetTargetType(sock, 1)

    triangulation = Triangulation(5, yaw_min=-np.pi*0.5, yaw_max=0, pitch_min=0, pitch_max=np.pi * 0.8)
    vertices = np.zeros((5, 5, 3))
    for (i, j, yaw, pitch) in triangulation:
        rc = -1
        while rc != 0:
            AUT_MakePositioning(sock, yaw + random.uniform(-0.03, 0.03), pitch + random.uniform(-0.03, 0.03))
            point = BAP_MeasDistanceAngle(sock)
            rc = point['RC']
        point = point['P']
        vertices[i][j] = utils.sph_to_dec(point['dHz'], point['dV'], point['dDist'])

    np.save('vertices.npa', vertices)
    sock.close()
    return vertices

def load_last_vertices():
    return np.load('vertices.npa.npy')

#vertices = measure_vertices()
vertices = load_last_vertices()
print(vertices[:,:,0])

import numpy as np

class Triangulation:
    '''
        Triangulates the sphere sector of yaw 0-90 degrees and pitch -90 - +90 degrees
    '''
    def __init__(self, v_per_edge = 10, yaw_min = 0, yaw_max = np.pi * 0.5, pitch_min = 0, pitch_max = np.pi):
        self.points = np.zeros((v_per_edge, v_per_edge, 2))
        for i in range(v_per_edge):
            for j in range(v_per_edge):
                if (i == 0 and j == 0) or (i == v_per_edge - 1 and j == v_per_edge - 1):
                    continue
                if i + j < v_per_edge:
                    self.points[i][j][0] = i / (i + j) # yaw 
                else:
                    self.points[i][j][0] = (v_per_edge - 1 - j) / (2*v_per_edge - 2 - i - j) # yaw 
                self.points[i][j][1] = (i + j) * 0.5 / (v_per_edge - 1) # pitch
        
        for i in range(v_per_edge):
            for j in range(v_per_edge):
                self.points[i][j][0] = yaw_min + self.points[i][j][0] * (yaw_max - yaw_min)
                self.points[i][j][1] = pitch_min + self.points[i][j][1] * (pitch_max - pitch_min)
    
    def __iter__(self):
        self.cur_i = 0
        self.cur_j = 0
        self.cur_dir = -1
        return self
    
    def __next__(self):
        if self.cur_dir == -1 and self.cur_j == self.points.shape[1] - 1:
            self.cur_i += 1
            self.cur_dir = 1
        elif self.cur_dir == -1 and self.cur_i == 0:
            self.cur_j += 1
            self.cur_dir = 1
        elif self.cur_dir == 1 and self.cur_i == self.points.shape[0] - 1:
            self.cur_j += 1
            self.cur_dir = -1
        elif self.cur_dir == 1 and self.cur_j == 0:
            self.cur_i += 1
            self.cur_dir = -1
        else:
            self.cur_i += self.cur_dir
            self.cur_j -= self.cur_dir
        if self.cur_i == self.points.shape[0] - 1 and self.cur_j == self.points.shape[1] - 1:
            raise StopIteration
        return (self.cur_i, self.cur_j, self.points[self.cur_i][self.cur_j][0], self.points[self.cur_i][self.cur_j][1])


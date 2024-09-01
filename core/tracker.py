from scipy.spatial import distance as dist
from collections import OrderedDict
import numpy as np
import logging
import math

LOG = logging.getLogger(__name__)

#MARTY ADD
SAMPLE_FRAMES = 50

class ObjectSpeed:
    def __init__(self, ID, start_frame, start_centroid):
        self.ID = ID

        self.start_centroid = start_centroid
        self.current_centroid = start_centroid

        self.start_frame = start_frame
        self.finish_frame = start_frame
        self.start_timing_frame = start_frame
        self.start_timing_centroid = start_centroid
        self.frame_history = OrderedDict()
        self.frame_history[start_frame] = start_centroid

        self.speed = 0

        self.active = True
        self.visible = True

    def update(self, current_centroid, frame):
        self.current_centroid = current_centroid
        self.frame_history[frame] = current_centroid
        self.visible = True
        sample_frames_away = frame - SAMPLE_FRAMES
        if sample_frames_away > self.start_timing_frame:
            for key_frame in list(self.frame_history.keys()):
                if key_frame > sample_frames_away:
                    break
                elif key_frame == sample_frames_away:
                    self.start_timing_frame =  sample_frames_away
                    self.start_timing_centroid = self.frame_history[key_frame]
                elif key_frame < sample_frames_away:
                    del self.frame_history[key_frame]
            self.speed = math.dist(current_centroid, self.start_timing_centroid)

    def deactivate(self, finish_frame):
        self.finish_frame = finish_frame
        self.active = False

class CentroidTracker:
    def __init__(self):
        self.ID = 0
        self.objects = OrderedDict()
        self.disappeared = OrderedDict()
        self.objects_speed = OrderedDict()
        
    def register(self, centroid, frame):
        self.objects[self.ID] = centroid
        self.disappeared[self.ID] = 0
        self.objects_speed[self.ID] = ObjectSpeed(self.ID, frame, centroid)
        self.ID += 1

        
    def deregister(self, ID, finish_frame):
        del self.objects[ID]
        del self.disappeared[ID]
        self.objects_speed[ID].deactivate(finish_frame)

        
    def update(self, inputCentroids, frame_threshold, frame):
        if len(inputCentroids) == 0:
            for ID in list(self.disappeared.keys()):
                self.disappeared[ID] += 1
                self.objects_speed[ID].visible = False
                
                if self.disappeared[ID] > 2*frame_threshold:
                    self.deregister(ID, frame - 2*frame_threshold)
            
            return self.objects
        
        if len(self.objects) == 0:
            for centroid in inputCentroids:
                self.register(centroid, frame)
                
        else:
            IDs = list(self.objects.keys())
            centroids = list(self.objects.values())
            
            D = dist.cdist(np.array(centroids), inputCentroids)
            rows = D.min(axis=1).argsort()
            cols = D.argmin(axis=1)[rows]
            
            usedRows = set()
            usedCols = set()
            
            for(row, col) in zip(rows, cols):
                if row in usedRows or col in usedCols:
                    continue
                
                ID = IDs[row]
                self.objects[ID] = inputCentroids[col]
                self.disappeared[ID] = 0
                self.objects_speed[ID].update(inputCentroids[col], frame)

                
                usedRows.add(row)
                usedCols.add(col)
                
            unusedRows = set(range(0, D.shape[0])).difference(usedRows)
            unusedCols = set(range(0, D.shape[1])).difference(usedCols)
            
            if D.shape[0] >= D.shape[1]:
                for row in unusedRows:
                    ID = IDs[row]
                    self.disappeared[ID] += 1
                    
                    if self.disappeared[ID] > 2*frame_threshold:
                        self.deregister(ID, frame - 2*frame_threshold)
                        
            else:
                for col in unusedCols:
                    self.register(inputCentroids[col], frame)
        
        return self.objects
from .painters import KeypointPainter, CrowdPainter, DetectionPainter

#MARTY ADD
import logging

#MARTY ADD
from collections import OrderedDict
from .. import core

PAINTERS = {
    'Annotation': KeypointPainter,
    'AnnotationCrowd': CrowdPainter,
    'AnnotationDet': DetectionPainter,
}

#MARTY ADD
LOG = logging.getLogger(__name__)


class AnnotationPainter:
    def __init__(self, *,
                 xy_scale=1.0,
                 painters=None):
        self.painters = {annotation_type: painter(xy_scale=xy_scale)
                         for annotation_type, painter in PAINTERS.items()}

        if painters:
            for annotation_type, painter in painters.items():
                self.painters[annotation_type] = painter
                
        
        #MARTY ADD
        self.ct = core.CentroidTracker()
                

    def annotations(self, ax, annotations, *,
                    color=None, colors=None, texts=None, subtexts=None, frame=None, **kwargs):
        #MARTY ADD
        centroids = []
        index_centroids_dict = OrderedDict()
        for i, ann in enumerate(annotations):
            if colors is not None:
                this_color = colors[i]
            elif color is not None:
                this_color = color
            elif getattr(ann, 'id_', None):
                this_color = ann.id_
            else:
                this_color = i
                
            text = None
            if texts is not None:
                text = texts[i]


            
            subtext = None
            if subtexts is not None:
                subtext = subtexts[i]

            painter = self.painters[ann.__class__.__name__]
            painter.annotation(ax, ann, color=this_color, text=text, subtext=subtext, **kwargs)
            

            if painter.centroid != -1:
                centroids.append(painter.centroid)
                index_centroids_dict[i] = painter.centroid
                #LOG.info('append centroid')
                
        #MARTY ADD
        index_id_dict = OrderedDict()
        LOG.info(f"Frame={frame}")
        centroid_objects = OrderedDict(self.ct.update(centroids,10, frame))
        for ID, centroid_object in centroid_objects.items():
            for index, index_centroid in index_centroids_dict.items():
                if(centroid_object == index_centroid):
                    index_id_dict[index] = ID
                    index_centroids_dict.popitem(index)
                    break

        
        #MARTY ADD
        for i, ann in enumerate(annotations):
            ID = index_id_dict.get(i)
            if ID in self.ct.objects_speed.keys():
                speed = f"{self.ct.objects_speed[ID].speed:.1f}"
                text = f"{ID}-{speed}"
            else:
                text = ''

            painter = self.painters[ann.__class__.__name__]
            painter.annotation_text(ax, ann, color=this_color, text=text, subtext=subtext, **kwargs)
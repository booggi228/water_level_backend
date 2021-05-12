import shapely
import json
import shapely.wkt
from sentinelhub import BBox, CRS


def get_bbox(polygon, inflate_bbox=0.1):
    """
    Determines the BBOX from polygon. BBOX is inflated in order to include polygon's surroundings. 
    """
    minx, miny, maxx, maxy = polygon.bounds
    delx=maxx-minx
    dely=maxy-miny

    minx=minx-delx*inflate_bbox
    maxx=maxx+delx*inflate_bbox
    miny=miny-dely*inflate_bbox
    maxy=maxy+dely*inflate_bbox
    
    return BBox(bbox=[minx, miny, maxx, maxy], crs=CRS.WGS84)

def toGeoJson (shape):
    return json.dumps(shapely.geometry.mapping(shape))
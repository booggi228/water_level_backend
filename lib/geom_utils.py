import shapely
import numpy as np
import json
import shapely.wkt
from sentinelhub import BBox, CRS
import rasterio
from rasterio import features
#from skimage.filters import sobel
#from skimage.morphology import disk
from skimage.morphology import dilation

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

def mask_to_polygons_layer(mask, eopatch, tolerance):
    
    all_polygons = []
    bbox = eopatch.bbox
    size_x = eopatch.meta_info['size_x']
    size_y = eopatch.meta_info['size_y']
    
    vx = bbox.min_x
    vy = bbox.max_y
    cx = (bbox.max_x-bbox.min_x)/size_x
    cy = (bbox.max_y-bbox.min_y)/size_y
    
    for shape, value in features.shapes(mask.astype(np.int16), mask=(mask == 1), transform=rasterio.Affine(cx, 0.0, vx,
       0.0, -cy, vy)): 
        return shapely.geometry.shape(shape).simplify(tolerance, False)
        all_polygons.append(shapely.geometry.shape(shape))
    
    all_polygons = shapely.geometry.MultiPolygon(all_polygons)
    if not all_polygons.is_valid:
        all_polygons = all_polygons.buffer(0)
        if all_polygons.type == 'Polygon':
            all_polygons = shapely.geometry.MultiPolygon([all_polygons])
    return all_polygons

def toGeoJson (shape):
    return json.dumps(shapely.geometry.mapping(shape))

def get_observed_shape(eopatch, idx):
    ratio = np.abs(eopatch.bbox.max_x - eopatch.bbox.min_x) / np.abs(eopatch.bbox.max_y - eopatch.bbox.min_y)
    
    tolerance = 0.00025
    
    observed = eopatch.mask['WATER_MASK'][idx,...,0]
    observed = dilation(observed)
    observed = np.ma.masked_where(observed == False, observed)
    observedShape = mask_to_polygons_layer(observed, eopatch, tolerance)
    return shapely.geometry.mapping(observedShape)
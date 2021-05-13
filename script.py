import geojson
import json
from shapely.geometry import shape
from eolearn.core import LinearWorkflow, FeatureType

from eolearn.io import SentinelHubInputTask
#from eolearn.core import LoadFromDisk, SaveToDisk
from eolearn.mask import AddValidDataMaskTask
# filtering of scenes
from eolearn.features import SimpleFilterTask, NormalizedDifferenceIndexTask
# burning the vectorised polygon to raster
from eolearn.geometry import VectorToRaster
# The golden standard: numpy and matplotlib
import numpy as np
# For manipulating geo-spatial vector dataset (polygons of nominal water extent)
import geopandas as gpd
# sentinelhub-py package
from sentinelhub import CRS, DataCollection

import re
import sys
sys.path.append('./src')
# from visualisation import mask_to_polygons_layer, plot_rgb_w_water, plot_water_levels
from geom_utils import get_bbox, toGeoJson
from water_extraction import calculate_valid_data_mask, calculate_coverage, AddValidDataCoverage, ValidDataCoveragePredicate, WaterDetector
from login import login_config
from json_convert_help import time_conv, list_of_dicts, NumpyArrayEncoder
from json import JSONEncoder

# Loading data
with open('./data/data.json') as f:
    input_json = json.load(f)

features = input_json["geometry"]
dam_nominal = shape(features)
dam_bbox = get_bbox(dam_nominal)

# Use login credentials from Sentinel Hub
config = login_config()

# Create an EOPatch and add all EO features (satellite imagery data)
download_task = SentinelHubInputTask(data_collection=DataCollection.SENTINEL2_L1C, 
                                     bands_feature=(FeatureType.DATA, 'BANDS'),
                                     resolution=20, 
                                     maxcc=0.5, 
                                     bands=['B02', 'B03', 'B04', 'B08'], 
                                     additional_data=[(FeatureType.MASK, 'dataMask', 'IS_DATA'), (FeatureType.MASK, 'CLM')],
                                     config=config
                                    )

calculate_ndwi = NormalizedDifferenceIndexTask((FeatureType.DATA, 'BANDS'), (FeatureType.DATA, 'NDWI'), (1, 3))

dam_gdf = gpd.GeoDataFrame(crs=CRS.WGS84.pyproj_crs(), geometry=[dam_nominal])
add_nominal_water = VectorToRaster(dam_gdf, (FeatureType.MASK_TIMELESS, 'NOMINAL_WATER'), values=1, 
                                   raster_shape=(FeatureType.MASK, 'IS_DATA'), raster_dtype=np.uint8)

add_valid_mask = AddValidDataMaskTask(predicate=calculate_valid_data_mask)
add_coverage = AddValidDataCoverage()

cloud_coverage_threshold = 0.05
remove_cloudy_scenes = SimpleFilterTask((FeatureType.MASK, 'VALID_DATA'), ValidDataCoveragePredicate(cloud_coverage_threshold))

water_detection = WaterDetector()

# Define the EOWorkflow
workflow = LinearWorkflow(download_task, calculate_ndwi, add_nominal_water, add_valid_mask,
                          add_coverage, remove_cloudy_scenes, water_detection)

# Run the workflow
time_interval = [input_json["startDate"],input_json["endDate"]] 

result = workflow.execute({
    download_task: {
        'bbox': dam_bbox,
        'time_interval': time_interval
    },
})

eopatch = list(result.values())[-1]

mydic = {
    'COVERAGE': eopatch.scalar['COVERAGE'],
    'WATER_LEVEL': eopatch.scalar['WATER_LEVEL'],
    'TIMESTAMP': eopatch.timestamp,
    'BBOX': eopatch.bbox.geometry.bounds,
    'CRS': eopatch.bbox.crs
}

def CRS_transform(data):

    crs_conv = re.sub('\D', '', str(data))
    crs_conv_list = list(crs_conv)
    #b = ''.join(str(x) for x in a)
    add_crs = crs_conv_list*(len(COVERAGE_convert)-1)
    manipulate_crs_list = [add_crs[i:i+(len(COVERAGE_convert)-1)] for i in range(0, len(add_crs), (len(COVERAGE_convert)-1))]
    #ccc = ''.join(str(x) for x in cc)
    save = [''.join(x) for x in manipulate_crs_list]
    #savee = map(int, save)
    return save

COVERAGE_convert = [y for x in mydic['COVERAGE'] for y in x]
WATER_LEVEL_convert = [y for x in mydic['WATER_LEVEL'] for y in x]
TIMESTAMP_convert = time_conv(mydic['TIMESTAMP'])
bbox_copy = mydic['BBOX']*(len(COVERAGE_convert)-1)
BBOX_convert = [bbox_copy[i:i+(len(COVERAGE_convert)-1)] for i in range(0, len(bbox_copy), (len(COVERAGE_convert)-1))]
CRS_convert = CRS_transform(mydic['CRS'])

numpyData = {"COVERAGE": COVERAGE_convert, "WATER_LEVEL": WATER_LEVEL_convert, "TIMESTAMP": TIMESTAMP_convert, "BBOX": BBOX_convert, "CRS": CRS_convert}
new_numpyData = list_of_dicts(numpyData)


json.dump(new_numpyData, open("result.json","w"), cls=NumpyArrayEncoder)



# def time_conv(time):
#     new_time = np.array([d.strftime('%Y.%m.%d') for d in time])
#     return new_time

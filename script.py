import geojson
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

import sys
sys.path.append('./src')
# from visualisation import mask_to_polygons_layer, plot_rgb_w_water, plot_water_levels
from geom_utils import get_bbox, toGeoJson
from water_extraction import calculate_valid_data_mask, calculate_coverage, AddValidDataCoverage, ValidDataCoveragePredicate, WaterDetector
from login import login_config

# Loading data
with open('data/Фронтовое.geojson') as f:
    gj = geojson.load(f)

features = gj['features'][0]['geometry']
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
time_interval = ['1992-05-01','2040-06-01'] 

result = workflow.execute({
    download_task: {
        'bbox': dam_bbox,
        'time_interval': time_interval
    },
})

eopatch = list(result.values())[-1]

from eolearn.core import OverwritePermission

#eopatch.save('./example_patch', overwrite_permission=OverwritePermission.OVERWRITE_FEATURES)
import json
# with open('data.json', 'w') as outfile:
#     json.dump(eopatch, outfile)
type(eopatch)
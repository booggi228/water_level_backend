import sys, json, io

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
from lib.geom_utils import get_bbox, toGeoJson, get_observed_shape
from lib.water_extraction import calculate_valid_data_mask, calculate_coverage, AddValidDataCoverage, ValidDataCoveragePredicate, WaterDetector
from lib.login import login_config



with open('./data/map.geojson') as f:
    input_json = json.load(f)


features = input_json["features"][0]["geometry"]
#features = input_json["geometry"]
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
#time_interval = [input_json["startDate"],input_json["endDate"]] 
time_interval = [input_json["features"][0]["startDate"],input_json["features"][0]["endDate"]]

result = workflow.execute({
    download_task: {
        'bbox': dam_bbox,
        'time_interval': time_interval
    },
})

eopatch = list(result.values())[-1]

output = []

for i in range(len(eopatch.scalar['WATER_LEVEL'])):
    numpyData = {"measurement_date": eopatch.timestamp[i].strftime('%d/%m/%Y'), "bbox": eopatch.bbox.geometry.bounds, "crs": eopatch.bbox.crs.epsg, "water_level": eopatch.scalar['WATER_LEVEL'][i,0], "cloud_coverage": eopatch.scalar['COVERAGE'][i,0], "measurement_type": "observed"}
    #obJect = {"type": "Feature", "properties": numpyData, "geometry": get_observed_shape(eopatch, i)}
    obJect = {"type": "FeatureCollection", "features":[{"type":"Feature", "properties": numpyData, "geometry": get_observed_shape(eopatch, i)}]}
    output.append(obJect)

output_json = json.dumps(output, ensure_ascii=False).encode('utf-8')
sys.stdout.buffer.write(output_json)
# print()
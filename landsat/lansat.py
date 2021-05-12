import re
import sys
import geojson
from landsatxplore.api import API
from landsatxplore.earthexplorer import EarthExplorer
from pandas.io import pickle
from rasterio.io import DatasetReader
from shapely.geometry.polygon import  Polygon
import rasterio
from rasterio import plot
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd

USER = "manuelfer1996@gmail.com"
PASS = "Nazlyman12345"

def login():
    global api,ee
    api = API(USER,PASS)
    ee = EarthExplorer(USER, PASS)

def exportSecenes(lat,lon):
    scenes = api.search(
        dataset='landsat_ot_c2_l2',
        latitude=lat,
        longitude=lon,
        max_cloud_cover=10,
        start_date='2015-01-01',
        end_date='2015-01-08'
        )
    if (len(scenes) ==0):
        print("No hay ningun dato")
        return
    print(scenes[0].keys())
    print(len(scenes))
    for scene in scenes:
        print(scene['acquisition_date'])
        polygon:Polygon = scene['spatial_coverage']
        # Write scene footprints to disk
        fname = f"landsat/landsat_data/{scene['landsat_product_id']}.geojson"
        with open(fname, "w") as f:
            geojson.dump(polygon,f)
        
        ee.download(scene["landsat_scene_id"], output_dir='./landsat/landsat_data')
        ee.logout()

def logout():
    api.logout()
    sys.exit()

# login()
# exportSecenes(4.6482422,-74.3880256)

PATH_DATOS = "landsat/landsat_data/datos"
datos = os.listdir(PATH_DATOS)

images = [val for val in datos if val.endswith(".TIF")]
df = {}
for val in images:
    m = re.search('B[\w]+', val)
    df[m.group(0)] = val 

band4:DatasetReader = rasterio.open(f"{PATH_DATOS}/{df['B4']}")
band5:DatasetReader = rasterio.open(f"{PATH_DATOS}/{df['B5']}")
plot.show(band4)
plot.show(band5)

import geopandas
import numpy as np
import pandas as pd
from shapely.geometry import Point

import missingno as msn

import seaborn as sns
import matplotlib.pyplot as plt

country = geopandas.read_file("data/gz_2010_us_040_00_5m.json")
country.head()
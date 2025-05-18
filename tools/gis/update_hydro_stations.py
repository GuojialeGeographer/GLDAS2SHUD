import geopandas as gpd
from shapely.geometry import Point
import os
import pandas as pd

# 新增水文站信息
new_stations = [
    {"ID": "TOS01004379", "Lat": 43.686, "Long": 10.585},
    {"ID": "TOS01004411", "Lat": 43.574, "Long": 11.869},
    {"ID": "TOS01004521", "Lat": 43.465, "Long": 11.823},
    {"ID": "TOS01004568", "Lat": 43.484, "Long": 11.618},
    {"ID": "TOS01004625", "Lat": 43.887, "Long": 11.525},
    {"ID": "TOS01004642", "Lat": 43.801, "Long": 11.466},
    {"ID": "TOS01004659", "Lat": 43.769, "Long": 11.424},
    {"ID": "TOS01004782", "Lat": 43.88,  "Long": 11.105},
    {"ID": "TOS01004875", "Lat": 43.815, "Long": 11.061},
    {"ID": "TOS01004941", "Lat": 43.724, "Long": 10.947},
    {"ID": "TOS01004971", "Lat": 43.604, "Long": 10.97},
    {"ID": "TOS01005005", "Lat": 43.633, "Long": 10.851},
    {"ID": "TOS01005131", "Lat": 43.593, "Long": 10.686},
    {"ID": "TOS01005181", "Lat": 43.666, "Long": 10.633},
    {"ID": "TOS01005191", "Lat": 43.685, "Long": 10.586},
]

shp_path = os.path.join("data", "shp数据", "hydro_stations.shp")

# 读取原有shp
gdf = gpd.read_file(shp_path)

# 构建新增站点GeoDataFrame
gdf_new = gpd.GeoDataFrame(
    new_stations,
    geometry=[Point(s["Long"], s["Lat"]) for s in new_stations],
    crs="EPSG:4326"
)

# 合并并去重（如ID重复则保留第一个）
gdf_all = pd.concat([gdf, gdf_new], ignore_index=True)
gdf_all = gdf_all.drop_duplicates(subset=["ID"])

gdf_all.to_file(shp_path)
print(f"已追加15个新站点，shp已更新: {shp_path}") 
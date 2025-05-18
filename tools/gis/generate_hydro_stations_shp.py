import geopandas as gpd
from shapely.geometry import Point
import os

# 水文站信息
stations = [
    {"ID": "TOS01004731", "Lat": 43.755, "Long": 11.195},
    {"ID": "TOS01004791", "Lat": 43.804, "Long": 11.131},
    {"ID": "TOS01004811", "Lat": 43.774, "Long": 11.094},
]

# 构建GeoDataFrame

gdf = gpd.GeoDataFrame(
    stations,
    geometry=[Point(s["Long"], s["Lat"]) for s in stations],
    crs="EPSG:4326"
)

# 输出目录
out_dir = os.path.join("data", "shp数据")
os.makedirs(out_dir, exist_ok=True)

# 保存为shp
out_path = os.path.join(out_dir, "hydro_stations.shp")
gdf.to_file(out_path)

print(f"水文站点shp已生成: {out_path}") 
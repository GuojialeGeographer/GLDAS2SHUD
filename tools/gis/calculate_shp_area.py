import geopandas as gpd
import os
import sys

# 默认文件路径
DEFAULT_SHP_PATH = os.path.join('data', 'shp数据', 'meteo.shp')

def main():
    # 支持命令行参数传入shp路径
    if len(sys.argv) > 1:
        shp_path = sys.argv[1]
    else:
        shp_path = DEFAULT_SHP_PATH

    # 读取shapefile
    gdf = gpd.read_file(shp_path)
    print(f"原始投影: {gdf.crs}")

    # 如果是地理坐标（经纬度），自动投影到等积投影（EPSG:6933）
    if gdf.crs is None or gdf.crs.is_geographic:
        print("检测到地理坐标，自动投影到等积投影（EPSG:6933）以便面积计算...")
        gdf = gdf.to_crs('EPSG:6933')
        print(f"新投影: {gdf.crs}")

    # 计算每个要素的面积（平方米）
    gdf['area_m2'] = gdf.geometry.area
    total_area_m2 = gdf['area_m2'].sum()
    total_area_km2 = total_area_m2 / 1e6

    print(f"要素数量: {len(gdf)}")
    print(f"总面积: {total_area_m2:.2f} 平方米 ({total_area_km2:.4f} 平方公里)")

if __name__ == "__main__":
    main() 
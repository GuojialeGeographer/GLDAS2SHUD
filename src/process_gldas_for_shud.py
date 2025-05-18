#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GLDAS数据处理工具 - 生成SHUD模型所需的气象驱动数据
功能:
1. 从shapefile中读取研究区域的点
2. 从GLDAS的nc4文件中提取这些点的气象数据（从2023年5月开始）
3. 按照SHUD模型要求的格式转换单位
4. 输出SHUD模型可直接使用的气象驱动数据
"""

import os
import glob
import argparse
import numpy as np
import xarray as xr
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import geopandas as gpd
from scipy.spatial import distance
import re
import shutil

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="处理GLDAS数据生成SHUD模型所需的气象驱动数据")
    parser.add_argument("--data-dir", default="data/gldas_data", help="GLDAS数据目录")
    parser.add_argument("--output-dir", default="output", help="输出目录")
    parser.add_argument("--shp-file", type=str, help="包含研究区域点的shapefile文件")
    parser.add_argument("--points", nargs='+', type=str, help="指定的坐标点列表，格式为'lon,lat'，例如 '120.5,30.5'")
    parser.add_argument("--force", action="store_true", help="强制重新处理已存在的文件")
    parser.add_argument("--start-date", type=str, default="20230501", help="数据开始日期 (YYYYMMDD)")
    parser.add_argument("--end-date", type=str, default="", help="数据结束日期 (YYYYMMDD)，默认处理到最后一个文件")
    return parser.parse_args()

def create_directories(base_dir):
    """创建必要的目录结构"""
    dirs = {
        "cache": os.path.join(base_dir, "cache"),  # 中间缓存文件（npz格式）
        "csv": os.path.join(base_dir, "csv"),      # 最终CSV文件
        "fig": os.path.join(base_dir, "fig"),      # 图表
    }
    
    for dir_path in dirs.values():
        os.makedirs(dir_path, exist_ok=True)
        
    return dirs

def get_nc4_files(data_dir, pattern="*.nc4"):
    """获取所有NC4文件并按时间排序"""
    files = []
    
    # 首先尝试在根目录查找NC4文件
    root_files = glob.glob(os.path.join(data_dir, pattern))
    files.extend(root_files)
    
    # 然后尝试在downloads子目录查找
    downloads_dir = os.path.join(data_dir, "downloads")
    if os.path.exists(downloads_dir):
        downloads_files = glob.glob(os.path.join(downloads_dir, pattern))
        files.extend(downloads_files)
    
    # 按文件名排序
    files = sorted(files)
    print(f"找到NC4文件总数: {len(files)}")
    
    return files

def extract_date_from_filename(filename):
    """从GLDAS文件名中提取日期时间信息"""
    # 文件名示例: GLDAS_NOAH025_3H.A20230501.0000.021.nc4
    base = os.path.basename(filename)
    
    # 尝试新格式: GLDAS_YYYYMMDD_HHMM.nc4
    match = re.match(r'GLDAS_(\d{8})_(\d{4})\.nc4', base)
    if match:
        date_str = match.group(1)  # 例如 "20230501"
        time_str = match.group(2)  # 例如 "0000"
        
        # 解析日期和时间
        year = int(date_str[0:4])
        month = int(date_str[4:6])
        day = int(date_str[6:8])
        hour = int(time_str[0:2])
        minute = int(time_str[2:4])
        
        return datetime(year, month, day, hour, minute)
    
    # 尝试旧格式: GLDAS_NOAH025_3H_EP.A20230501.0000.021.nc4
    match = re.search(r'\.A(\d{8})\.(\d{4})\.', base)
    if match:
        date_str = match.group(1)  # 例如 "20230501"
        time_str = match.group(2)  # 例如 "0000"
        
        # 解析日期和时间
        year = int(date_str[0:4])
        month = int(date_str[4:6])
        day = int(date_str[6:8])
        hour = int(time_str[0:2])
        minute = int(time_str[2:4])
        
        return datetime(year, month, day, hour, minute)
    
    return None

def filter_files_by_date(files, start_date_str, end_date_str=None):
    """根据日期过滤文件"""
    filtered_files = []
    
    # 将日期字符串转换为datetime对象
    start_date = None
    if start_date_str:
        start_date = datetime.strptime(start_date_str, "%Y%m%d")
    
    end_date = None
    if end_date_str:
        end_date = datetime.strptime(end_date_str, "%Y%m%d")
    
    # 逐个检查文件
    for file in files:
        date = extract_date_from_filename(file)
        if date:
            # 检查是否在日期范围内
            if start_date and date < start_date:
                continue
            if end_date and date > end_date:
                continue
            filtered_files.append(file)
    
    print(f"过滤后的文件数量: {len(filtered_files)}")
    if filtered_files:
        first_date = extract_date_from_filename(filtered_files[0])
        last_date = extract_date_from_filename(filtered_files[-1])
        print(f"开始日期: {first_date}")
        print(f"结束日期: {last_date}")
    
    return filtered_files

def group_files_by_year(files):
    """将文件按年份分组"""
    year_groups = {}
    
    for file in files:
        date = extract_date_from_filename(file)
        if date:
            year = date.year
            if year not in year_groups:
                year_groups[year] = []
            year_groups[year].append(file)
    
    return year_groups

def read_points_from_shapefile(shp_file):
    """从shapefile中读取坐标点"""
    try:
        print(f"从shapefile读取点: {shp_file}")
        gdf = gpd.read_file(shp_file)
        points = []
        
        # 输出shapefile的基本信息
        print(f"Shapefile包含{len(gdf)}个要素")
        print(f"坐标系统: {gdf.crs}")
        print(f"列名: {gdf.columns.tolist()}")
        
        # 获取点的坐标
        for idx, row in gdf.iterrows():
            # 获取几何对象
            geom = row.geometry
            
            # 如果是点类型
            if geom.type == 'Point':
                x, y = geom.x, geom.y
                point_id = f"{idx+1}"  # 使用索引作为ID
                
                # 如果shapefile中有ID字段，使用该字段
                if 'ID' in gdf.columns:
                    point_id = str(row['ID'])
                elif 'id' in gdf.columns:
                    point_id = str(row['id'])
                elif 'Id' in gdf.columns:
                    point_id = str(row['Id'])
                
                # 创建点对象
                points.append({
                    "id": point_id,
                    "lon": x,
                    "lat": y
                })
                print(f"  点{point_id}: ({x}, {y})")
        
        return points
    except Exception as e:
        print(f"读取shapefile时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

def parse_point_list(point_strings):
    """解析命令行参数中的点列表"""
    points = []
    for i, point_str in enumerate(point_strings):
        try:
            lon, lat = map(float, point_str.split(','))
            points.append({
                "id": f"{i+1}",
                "lon": lon,
                "lat": lat
            })
        except ValueError:
            print(f"警告: 无法解析坐标点 '{point_str}'")
    
    return points

def find_nearest_gldas_points(user_points, nc_file):
    """找到最接近用户指定点的GLDAS格点"""
    print(f"查找最近的GLDAS格点...")
    
    # 打开NC文件获取所有格点信息
    ds = xr.open_dataset(nc_file)
    lats = ds.lat.values
    lons = ds.lon.values
    ds.close()
    
    nearest_points = []
    for point in user_points:
        point_id = point["id"]
        x = point["lon"]
        y = point["lat"]
        
        # 找到最接近的经纬度点
        lat_idx = np.abs(lats - y).argmin()
        lon_idx = np.abs(lons - x).argmin()
        
        nearest_lat = lats[lat_idx]
        nearest_lon = lons[lon_idx]
        
        # 生成点ID
        gldas_id = f"{point_id}"  # 保持与原始ID一致
        
        nearest_points.append({
            "id": gldas_id,  # 使用与用户点相同的ID
            "original_id": point_id,
            "original_lon": x,
            "original_lat": y,
            "lon": nearest_lon,
            "lat": nearest_lat,
            "lon_idx": lon_idx,
            "lat_idx": lat_idx
        })
        
        print(f"  点{point_id} ({x:.4f}, {y:.4f}) -> GLDAS点 ({nearest_lon:.4f}, {nearest_lat:.4f})")
    
    return nearest_points

def extract_points_to_cache(nc_files, year, cache_dir, points, force=False):
    """从NC文件中提取特定点的数据并保存为缓存文件"""
    # 检查是否已存在对应年份的缓存文件
    cache_file = os.path.join(cache_dir, f"GLDAS-{year}-points.cache.npz")
    if os.path.exists(cache_file) and not force:
        print(f"缓存文件已存在: {cache_file}，跳过处理")
        return cache_file
    
    # 需要提取的变量
    extract_vars = [
        "Rainf_tavg",   # 降水 (kg m-2 s-1)
        "Tair_f_inst",   # 温度 (K)
        "Qair_f_inst",   # 比湿 (kg kg-1)
        "Wind_f_inst",   # 风速 (m s-1)
        "SWdown_f_tavg", # 短波辐射 (W m-2)
        "Psurf_f_inst"   # 表面气压 (Pa)
    ]
    
    # 按照时间顺序排序
    nc_files.sort()
    
    # 获取点信息
    point_ids = [p["id"] for p in points]
    lat_indices = [p["lat_idx"] for p in points]
    lon_indices = [p["lon_idx"] for p in points]
    
    # 获取第一个文件，用于检查变量
    first_ds = xr.open_dataset(nc_files[0])
    
    # 获取变量列表
    available_vars = list(first_ds.variables)
    variables = []
    for var in extract_vars:
        if var in available_vars:
            variables.append(var)
        else:
            print(f"警告: 变量 {var} 不在数据集中")
    
    first_ds.close()
    
    print(f"提取{len(point_ids)}个点的数据")
    print(f"提取变量: {variables}")
    
    # 初始化数据数组和时间列表
    times = []
    all_data = []
    
    # 逐个处理NC文件
    for idx, nc_file in enumerate(nc_files):
        print(f"  处理文件 {idx+1}/{len(nc_files)}: {os.path.basename(nc_file)}")
        
        try:
            # 打开NC文件
            ds = xr.open_dataset(nc_file)
            
            # 获取时间戳
            time_value = pd.to_datetime(ds.time.values[0])
            times.append(time_value)
            
            # 创建当前时间步的数据数组
            time_step_data = np.zeros((len(point_ids), len(variables)))
            
            # 遍历所有点和所有变量，提取数据
            for point_idx in range(len(points)):
                lat_idx = lat_indices[point_idx]
                lon_idx = lon_indices[point_idx]
                
                for var_idx, var in enumerate(variables):
                    # 提取数据
                    value = float(ds[var].isel(lat=lat_idx, lon=lon_idx).values.item())
                    time_step_data[point_idx, var_idx] = value
            
            # 将当前时间步的数据添加到所有数据中
            all_data.append(time_step_data)
            
        except Exception as e:
            print(f"    处理文件时出错: {str(e)}")
            continue
    
    # 检查是否提取到了数据
    if len(all_data) == 0:
        print(f"警告: 未能从NC文件中提取到任何数据")
        return None
    
    # 将所有时间步的数据合并为一个数组
    data_array = np.zeros((len(point_ids), len(times), len(variables)))
    for t_idx, t_data in enumerate(all_data):
        data_array[:, t_idx, :] = t_data
    
    # 保存为缓存文件
    try:
        np.savez_compressed(
            cache_file,
            data_array=data_array,
            point_ids=point_ids,
            variables=variables,
            times=times
        )
        print(f"缓存文件已保存: {cache_file}")
    except Exception as e:
        print(f"保存缓存文件失败: {str(e)}")
        return None
    
    return cache_file

def convert_to_rh(qair, tair, psurf):
    """将比湿转换为相对湿度"""
    # 绝对零度
    t0 = 273.15  # K
    
    # 计算相对湿度
    rh = 0.263 * psurf * qair / np.exp(17.67 * (tair - t0) / (tair - 29.65)) 
    
    # 将百分比转换为0-1的比例
    rh = rh / 100.0
    
    # 限制在0.1-1.0的范围内
    rh = np.minimum(rh, 1.0)
    rh = np.maximum(rh, 0.1)
    
    return rh

def process_cache_to_csv(cache_file, csv_dir, force=False):
    """将缓存文件转换为每个点的CSV文件"""
    print(f"从{cache_file}加载缓存数据...")
    
    try:
        # 加载缓存数据
        cache_data = np.load(cache_file, allow_pickle=True)
        data_array = cache_data['data_array']
        point_ids = cache_data['point_ids']
        variables = cache_data['variables']
        times = cache_data['times']
    except Exception as e:
        print(f"加载缓存文件失败: {str(e)}")
        return False
    
    # 处理每个点的数据
    for p_idx, point_id in enumerate(point_ids):
        # 创建CSV文件名
        csv_file = os.path.join(csv_dir, f"{point_id}.csv")
        if os.path.exists(csv_file) and not force:
            print(f"  CSV文件已存在: {csv_file} (跳过)")
            continue
            
        print(f"  处理点 {p_idx+1}/{len(point_ids)}: {point_id}")
        
        # 创建数据字典
        data_dict = {}
        for var_idx, var in enumerate(variables):
            data_dict[var] = data_array[p_idx, :, var_idx]
        
        # 将数据添加到DataFrame
        df = pd.DataFrame(data_dict, index=times)
        
        # 1. 时间间隔（以天为单位）
        time_intervals = [(t - times[0]).total_seconds() / (24 * 3600) for t in times]
        
        # 2. 降水: kg m-2 s-1 -> mm/day
        if 'Rainf_tavg' in df.columns:
            df['Precip'] = df['Rainf_tavg'] * 86400  # 转换为mm/day
        else:
            df['Precip'] = 0.0
        
        # 3. 温度: K -> ℃
        if 'Tair_f_inst' in df.columns:
            df['Temp'] = df['Tair_f_inst'] - 273.15
        else:
            df['Temp'] = 15.0  # 默认值
        
        # 4. 相对湿度: 比湿 -> 相对湿度(0-1)
        if all(var in df.columns for var in ['Qair_f_inst', 'Tair_f_inst', 'Psurf_f_inst']):
            df['RH'] = convert_to_rh(df['Qair_f_inst'], df['Tair_f_inst'], df['Psurf_f_inst'])
        else:
            df['RH'] = 0.7  # 默认值
        
        # 5. 风速: m/s
        if 'Wind_f_inst' in df.columns:
            df['Wind'] = df['Wind_f_inst']
        else:
            df['Wind'] = 2.0  # 默认值
        
        # 6. 辐射: W/m2
        if 'SWdown_f_tavg' in df.columns:
            df['RADN'] = df['SWdown_f_tavg']
        else:
            df['RADN'] = 0.0  # 默认值
        
        # 7. 气压: Pa -> kPa
        if 'Psurf_f_inst' in df.columns:
            df['VP'] = df['Psurf_f_inst'] / 1000.0  # 转换为kPa
        else:
            df['VP'] = 101.325  # 默认值 (标准大气压)
        
        # 保留4位小数
        columns = ['Precip', 'Temp', 'RH', 'VP', 'Wind', 'RADN']
        df[columns] = df[columns].round(4)
        
        # 写入SHUD模型所需的CSV格式
        with open(csv_file, 'w') as f:
            # 第一行: 时间步数 列数 开始日期 结束日期 时间间隔(秒)
            start_date = times[0].strftime("%Y%m%d")
            end_date = times[-1].strftime("%Y%m%d")
            time_step = int((times[1] - times[0]).total_seconds())  # 秒
            num_rows = len(df)
            num_cols = len(columns) + 1  # 变量列 + 时间列
            
            f.write(f"{num_rows}\t{num_cols}\t{start_date}\t{end_date}\t{time_step}\n")
            
            # 第二行: 列名
            f.write("Time_interval\t" + "\t".join(columns) + "\n")
            
            # 数据行
            for i, (time, row) in enumerate(zip(time_intervals, df[columns].values)):
                values = [f"{time:.4f}"] + [f"{val:.4f}" for val in row]
                f.write("\t".join(values) + "\n")
        
        print(f"  CSV文件已创建: {csv_file}")
    
    return True

def create_meteotsd_file(csv_dir, points, output_dir):
    """创建SHUD模型需要的meteo.tsd.forc文件"""
    print("创建meteo.tsd.forc文件...")
    
    # 获取第一个CSV文件的开始日期
    first_csv = os.path.join(csv_dir, f"{points[0]['id']}.csv")
    
    with open(first_csv, 'r') as f:
        first_line = f.readline().strip().split('\t')
        if len(first_line) >= 3:
            start_date = first_line[2]  # 开始日期
        else:
            print("警告: CSV文件格式不正确，使用默认日期")
            start_date = "20230501"
    
    # 创建meteo.tsd.forc文件
    meteo_file = os.path.join(output_dir, "meteo.tsd.forc")
    
    with open(meteo_file, 'w') as f:
        # 写入点数和开始日期
        f.write(f"{len(points)} {start_date}\n")
        
        # 写入相对路径
        f.write("./csv/\n")
        
        # 写入各点的文件名
        for point in points:
            f.write(f"{point['id']}.csv\n")
    
    print(f"已创建meteo.tsd.forc文件: {meteo_file}")
    return True

def create_point_locations_file(points, output_dir):
    """创建包含点位置信息的CSV文件"""
    print("创建点位置文件...")
    
    location_file = os.path.join(output_dir, "meteo_locations.csv")
    
    with open(location_file, 'w') as f:
        # 写入表头
        f.write("ID,Original_Lon,Original_Lat,GLDAS_Lon,GLDAS_Lat\n")
        
        # 写入每个点的信息
        for point in points:
            f.write(f"{point['id']},{point['original_lon']},{point['original_lat']},{point['lon']},{point['lat']}\n")
    
    print(f"已创建点位置文件: {location_file}")
    return True

def save_points_map(points, output_dir):
    """保存原始点和GLDAS点的对应关系图"""
    print("创建点对应关系图...")
    
    plt.figure(figsize=(10, 8))
    
    # 绘制原始点
    user_x = [p["original_lon"] for p in points]
    user_y = [p["original_lat"] for p in points]
    plt.scatter(user_x, user_y, c='blue', marker='o', s=80, label='原始点')
    
    # 绘制GLDAS点
    gldas_x = [p["lon"] for p in points]
    gldas_y = [p["lat"] for p in points]
    plt.scatter(gldas_x, gldas_y, c='red', marker='x', s=100, label='GLDAS点')
    
    # 连接对应的点
    for i in range(len(points)):
        plt.plot([user_x[i], gldas_x[i]], [user_y[i], gldas_y[i]], 'k--', alpha=0.5)
    
    # 添加点ID标签
    for i, p in enumerate(points):
        plt.annotate(p["id"], (user_x[i], user_y[i]), 
                    textcoords="offset points", xytext=(0,10), ha='center')
    
    plt.xlabel('经度')
    plt.ylabel('纬度')
    plt.title('研究点与GLDAS点对应关系')
    plt.legend()
    plt.grid(True)
    
    # 保存图像
    map_file = os.path.join(output_dir, "fig", "meteo_points_map.png")
    plt.savefig(map_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"已创建点对应关系图: {map_file}")
    return True

def prepare_shud_project(output_dir):
    """准备SHUD模型项目目录结构"""
    # 确保CSV目录在输出目录中
    source_csv_dir = os.path.join(output_dir, "csv")
    if not os.path.exists(source_csv_dir):
        print(f"错误: CSV目录不存在: {source_csv_dir}")
        return False
    
    # 复制文件到SHUD项目目录
    try:
        # 确保项目目录存在
        shud_dir = os.path.join(output_dir, "shud_project")
        os.makedirs(shud_dir, exist_ok=True)
        
        # 复制meteo.tsd.forc文件
        shutil.copy(os.path.join(output_dir, "meteo.tsd.forc"), shud_dir)
        
        # 创建并复制CSV目录
        shud_csv_dir = os.path.join(shud_dir, "csv")
        os.makedirs(shud_csv_dir, exist_ok=True)
        
        # 复制所有CSV文件
        for file in os.listdir(source_csv_dir):
            if file.endswith(".csv"):
                shutil.copy(os.path.join(source_csv_dir, file), shud_csv_dir)
        
        print(f"SHUD模型项目已创建: {shud_dir}")
        print(f"  - meteo.tsd.forc: 气象驱动配置文件")
        print(f"  - csv/: 气象驱动数据")
        
        return True
    except Exception as e:
        print(f"准备SHUD项目时出错: {str(e)}")
        return False

def main():
    """主函数"""
    # 解析命令行参数
    args = parse_arguments()
    
    # 创建目录结构
    dirs = create_directories(args.output_dir)
    
    # 获取用户指定的点
    user_points = []
    if args.shp_file:
        # 从shapefile读取点
        user_points = read_points_from_shapefile(args.shp_file)
    elif args.points:
        # 从命令行参数读取点
        user_points = parse_point_list(args.points)
    
    if not user_points:
        print("错误: 没有提供有效的坐标点。请使用--shp-file或--points指定坐标点。")
        return 1
    
    print(f"找到{len(user_points)}个坐标点")
    
    # 获取所有NC4文件
    print("搜索GLDAS数据文件...")
    nc4_files = get_nc4_files(args.data_dir)
    if not nc4_files:
        print("错误: 没有找到NC4文件，退出")
        return 1
    
    # 按日期过滤文件
    nc4_files = filter_files_by_date(nc4_files, args.start_date, args.end_date)
    if not nc4_files:
        print("错误: 过滤后没有文件符合日期范围要求")
        return 1
    
    # 找到最接近研究点的GLDAS格点
    gldas_points = find_nearest_gldas_points(user_points, nc4_files[0])
    
    # 按年份分组
    year_groups = group_files_by_year(nc4_files)
    print(f"数据分为{len(year_groups)}个年份组")
    
    # 为每个年份提取点数据并生成缓存文件
    cache_files = []
    for year, files in year_groups.items():
        print(f"处理{year}年的数据...")
        cache_file = extract_points_to_cache(files, year, dirs["cache"], gldas_points, args.force)
        if cache_file:
            cache_files.append(cache_file)
    
    if not cache_files:
        print("错误: 没有成功创建缓存文件")
        return 1
    
    # 从缓存文件生成CSV
    csv_success = False
    for cache_file in cache_files:
        result = process_cache_to_csv(cache_file, dirs["csv"], args.force)
        csv_success = csv_success or result
    
    if not csv_success:
        print("错误: 没有成功创建CSV文件")
        return 1
    
    # 创建meteo.tsd.forc文件
    create_meteotsd_file(dirs["csv"], gldas_points, args.output_dir)
    
    # 创建点位置信息文件
    create_point_locations_file(gldas_points, args.output_dir)
    
    # 保存点对应关系图
    save_points_map(gldas_points, args.output_dir)
    
    # 准备SHUD项目
    prepare_shud_project(args.output_dir)
    
    print("==============================================")
    print("GLDAS数据处理完成!")
    print(f"SHUD气象驱动数据已保存在 {args.output_dir} 目录")
    print(f"1. meteo.tsd.forc - SHUD气象配置文件")
    print(f"2. csv/ - 各点的气象数据")
    print(f"3. meteo_locations.csv - 气象点位置信息")
    print(f"4. fig/meteo_points_map.png - 点对应关系图")
    print(f"5. shud_project/ - 可直接使用的SHUD模型项目")
    print("==============================================")
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        exit(exit_code)
    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1) 
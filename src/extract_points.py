#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
提取GLDAS点位气象数据工具 
功能:
1. 读取指定的坐标点
2. 从GLDAS的nc4文件中提取这些点的气象数据
3. 按照SHUD模型要求的格式转换单位
4. 输出SHUD模型所需的CSV格式
"""

import os
import glob
import argparse
import numpy as np
import xarray as xr
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from scipy.spatial import distance
import re

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="从GLDAS数据中提取特定点的气象数据")
    parser.add_argument("--data-dir", default="data/gldas_data", help="GLDAS数据目录")
    parser.add_argument("--output-dir", default="output", help="输出目录")
    parser.add_argument("--points", nargs='+', type=str, help="指定的坐标点列表，格式为'lon,lat'，例如 '120.5,30.5'")
    parser.add_argument("--point-file", type=str, help="包含坐标点的文件，每行一个点，格式为'lon,lat'")
    parser.add_argument("--force", action="store_true", help="强制重新处理已存在的文件")
    return parser.parse_args()

def create_directories(base_dir):
    """创建必要的目录结构"""
    dirs = {
        "cache": os.path.join(base_dir, "cache"),  # 中间缓存文件（npz格式）
        "csv": os.path.join(base_dir, "csv"),  # 最终CSV文件
        "fig": os.path.join(base_dir, "fig"),  # 图表
    }
    
    for dir_path in dirs.values():
        os.makedirs(dir_path, exist_ok=True)
        
    return dirs

def get_nc4_files(data_dir, pattern="GLDAS_*.nc4"):
    """获取所有NC4文件并按时间排序"""
    files = sorted(glob.glob(os.path.join(data_dir, pattern)))
    return files

def extract_date_from_filename(filename):
    """从GLDAS文件名中提取日期时间信息"""
    # 文件名示例: GLDAS_20250401_1500.nc4
    base = os.path.basename(filename)
    
    # 尝试新格式: GLDAS_YYYYMMDD_HHMM.nc4
    match = re.match(r'GLDAS_(\d{8})_(\d{4})\.nc4', base)
    if match:
        date_str = match.group(1)  # 例如 "20250401"
        time_str = match.group(2)  # 例如 "1500"
        
        # 解析日期和时间
        year = int(date_str[0:4])
        month = int(date_str[4:6])
        day = int(date_str[6:8])
        hour = int(time_str[0:2])
        minute = int(time_str[2:4])
        
        return datetime(year, month, day, hour, minute)
    
    # 尝试旧格式: GLDAS_NOAH025_3H_EP.A20250401.1500.021.nc4
    parts = base.split(".")
    if len(parts) >= 3 and parts[0].startswith("GLDAS"):
        date_str = parts[1].replace("A", "")  # 例如 "A20250401" -> "20250401"
        time_str = parts[2]  # 例如 "1500"
        
        # 解析日期和时间
        year = int(date_str[0:4])
        month = int(date_str[4:6])
        day = int(date_str[6:8])
        hour = int(time_str[0:2])
        minute = int(time_str[2:4])
        
        return datetime(year, month, day, hour, minute)
    
    return None

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

def read_points_from_file(point_file):
    """从文件中读取坐标点"""
    points = []
    try:
        with open(point_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split(',')
                    if len(parts) >= 2:
                        try:
                            lon = float(parts[0])
                            lat = float(parts[1])
                            point_id = f"X{lon}Y{lat}"
                            points.append({
                                "id": point_id,
                                "x": lon,
                                "y": lat
                            })
                        except ValueError:
                            print(f"警告: 无法解析坐标点 '{line}'")
    except Exception as e:
        print(f"读取坐标点文件时出错: {str(e)}")
    
    return points

def parse_point_list(point_strings):
    """解析命令行参数中的点列表"""
    points = []
    for point_str in point_strings:
        try:
            lon, lat = map(float, point_str.split(','))
            point_id = f"X{lon}Y{lat}"
            points.append({
                "id": point_id,
                "x": lon,
                "y": lat
            })
        except ValueError:
            print(f"警告: 无法解析坐标点 '{point_str}'")
    
    return points

def find_nearest_gldas_points(user_points, nc_file):
    """找到最接近用户指定点的GLDAS格点"""
    print(f"查找最近的GLDAS格点...")
    
    # 打开第一个nc文件获取所有格点信息
    ds = xr.open_dataset(nc_file)
    lats = ds.lat.values
    lons = ds.lon.values
    ds.close()
    
    nearest_points = []
    for point in user_points:
        point_id = point["id"]
        x = point["x"]
        y = point["y"]
        
        # 找到最接近的经纬度点
        lat_idx = np.abs(lats - y).argmin()
        lon_idx = np.abs(lons - x).argmin()
        
        nearest_lat = lats[lat_idx]
        nearest_lon = lons[lon_idx]
        
        # 生成GLDAS点ID
        gldas_id = f"X{nearest_lon}Y{nearest_lat}"
        
        nearest_points.append({
            "original_id": point_id,
            "gldas_id": gldas_id,
            "lon": nearest_lon,
            "lat": nearest_lat,
            "lon_idx": lon_idx,
            "lat_idx": lat_idx
        })
        
        print(f"  用户点 {point_id} ({x:.3f}, {y:.3f}) -> GLDAS点 {gldas_id} ({nearest_lon:.3f}, {nearest_lat:.3f})")
    
    return nearest_points

def extract_points_to_cache(nc_files, year, cache_dir, points, force=False):
    """
    从NC文件中提取特定点的数据并保存为缓存文件
    """
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
    
    # 提取点ID和坐标索引
    point_ids = [p["original_id"] for p in points]
    gldas_ids = [p["gldas_id"] for p in points]
    lat_indices = [p["lat_idx"] for p in points]
    lon_indices = [p["lon_idx"] for p in points]
    
    # 获取第一个文件，用于检查变量
    first_ds = xr.open_dataset(nc_files[0])
    
    # 获取变量列表（确保所有需要的变量都存在）
    available_vars = list(first_ds.variables)
    variables = []
    for var in extract_vars:
        if var in available_vars:
            variables.append(var)
        else:
            print(f"警告: 变量 {var} 不在数据集中")
    
    first_ds.close()
    
    print(f"提取点数: {len(point_ids)}")
    print(f"提取变量: {variables}")
    
    # 初始化数据数组，维度为: [点数, 时间步, 变量数]
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
            gldas_ids=gldas_ids,
            variables=variables,
            times=times
        )
        print(f"缓存文件已保存: {cache_file}")
    except Exception as e:
        print(f"保存缓存文件失败: {str(e)}")
        return None
    
    return cache_file

def convert_to_rh(qair, tair, psurf):
    """
    将比湿转换为相对湿度
    """
    # 绝对零度
    t0 = 273.15  # K
    
    # 计算相对湿度 (与AutoSHUD保持一致)
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
        gldas_ids = cache_data['gldas_ids']
        variables = cache_data['variables']
        times = cache_data['times']
    except Exception as e:
        print(f"加载缓存文件失败: {str(e)}")
        return False
    
    # 处理每个点的数据
    for p_idx, point_id in enumerate(point_ids):
        # 检查是否已经存在CSV文件
        csv_file = os.path.join(csv_dir, f"GLDAS_{point_id}.csv")
        if os.path.exists(csv_file) and not force:
            print(f"  CSV文件已存在: {csv_file} (跳过)")
            continue
            
        print(f"  处理点 {p_idx+1}/{len(point_ids)}: {point_id} (GLDAS点: {gldas_ids[p_idx]})")
        
        # 提取当前点的所有时间步长的数据
        point_data = data_array[p_idx, :, :]
        
        # 创建临时数据字典
        data_dict = {}
        for var_idx, var in enumerate(variables):
            data_dict[var] = point_data[:, var_idx]
        
        # 创建DataFrame
        df = pd.DataFrame(data_dict)
        
        # 添加时间信息
        df['time'] = times
        
        # 单位转换
        # 1. 降水: kg m-2 s-1 (GLDAS) -> mm day-1 (SHUD)
        if 'Rainf_tavg' in df.columns:
            df['Precip_mm.d'] = df['Rainf_tavg'] * 86400
        else:
            print(f"  警告: 未找到降水变量 'Rainf_tavg'，将使用0值")
            df['Precip_mm.d'] = 0.0
        
        # 2. 温度: K -> C
        if 'Tair_f_inst' in df.columns:
            df['Temp_C'] = df['Tair_f_inst'] - 273.15
        else:
            print(f"  警告: 未找到气温变量，使用默认值")
            df['Temp_C'] = 15.0
        
        # 3. 相对湿度: 比湿 -> 相对湿度(0-1)
        if all(var in df.columns for var in ['Qair_f_inst', 'Tair_f_inst', 'Psurf_f_inst']):
            df['RH_1'] = convert_to_rh(df['Qair_f_inst'], df['Tair_f_inst'], df['Psurf_f_inst'])
        else:
            print(f"  警告: 未找到湿度相关变量，使用默认值")
            df['RH_1'] = 0.7
        
        # 4. 风速: 保持不变
        if 'Wind_f_inst' in df.columns:
            df['Wind_m.s'] = df['Wind_f_inst']
        else:
            print(f"  警告: 未找到风速变量，使用默认值")
            df['Wind_m.s'] = 2.0
        
        # 5. 辐射: 保持不变
        if 'Swnet_tavg' in df.columns:
            df['RN_w.m2'] = df['Swnet_tavg']
        elif 'SWdown_f_tavg' in df.columns:
            df['RN_w.m2'] = df['SWdown_f_tavg']
        else:
            print(f"  警告: 未找到辐射变量，使用0值")
            df['RN_w.m2'] = 0.0
        
        # 6. 气压: Pa，保持不变
        if 'Psurf_f_inst' in df.columns:
            df['Pres_pa'] = df['Psurf_f_inst']
        else:
            print(f"  警告: 未找到气压变量，使用默认值")
            df['Pres_pa'] = 101325.0  # 标准大气压
        
        # 保留4位小数
        output_columns = ['Precip_mm.d', 'Temp_C', 'RH_1', 'Wind_m.s', 'RN_w.m2', 'Pres_pa']
        df[output_columns] = df[output_columns].round(4)
        
        # 准备输出数据
        output_df = df[output_columns].copy()
        
        # 计算时间间隔(天)
        time_intervals = []
        for i, t in enumerate(times):
            if i == 0:
                time_intervals.append(0)
            else:
                # 计算与起始时间的间隔（以天为单位）
                delta = (t - times[0]).total_seconds() / (24 * 3600)
                time_intervals.append(delta)
        
        # 写入符合SHUD要求的CSV格式
        with open(csv_file, 'w') as f:
            # 第一行: 元数据 - 时间步数 列数 开始日期 结束日期 时间间隔(秒)
            start_date = times[0].strftime("%Y%m%d")
            end_date = times[-1].strftime("%Y%m%d")
            time_step = int((times[1] - times[0]).total_seconds())  # 秒
            num_rows = len(output_df)
            num_cols = len(output_columns) + 1  # 变量 + 时间列
            
            f.write(f"{num_rows}\t{num_cols}\t{start_date}\t{end_date}\t{time_step}\n")
            
            # 第二行: 列名
            f.write("Time_interval\t" + "\t".join(output_columns) + "\n")
            
            # 数据行
            for i, row in output_df.iterrows():
                # 使用Time_interval作为时间列
                values = [f"{time_intervals[i]:.4f}"] + [f"{val:.4f}" for val in row.values]
                f.write("\t".join(values) + "\n")
        
        print(f"  CSV文件已创建: {csv_file}")
    
    return True

def create_meteotsd_file(csv_dir, points, output_dir):
    """创建SHUD模型需要的meteo.tsd.forc文件"""
    print("创建meteo.tsd.forc文件...")
    
    # 获取第一个CSV文件的开始日期
    first_csv = os.path.join(csv_dir, f"GLDAS_{points[0]['original_id']}.csv")
    
    with open(first_csv, 'r') as f:
        first_line = f.readline().strip().split('\t')
        if len(first_line) >= 3:
            start_date = first_line[2]  # 格式如: 20250401
        else:
            print("警告: CSV文件格式不正确，使用默认日期")
            start_date = "20250401"
    
    # 创建meteo.tsd.forc文件
    meteo_file = os.path.join(output_dir, "meteo.tsd.forc")
    
    with open(meteo_file, 'w') as f:
        # 写入点数和开始日期
        f.write(f"{len(points)} {start_date}\n")
        
        # 写入相对路径
        f.write("./csv/\n")
        
        # 写入各点的文件名
        for point in points:
            f.write(f"GLDAS_{point['original_id']}.csv\n")
    
    print(f"已创建meteo.tsd.forc文件: {meteo_file}")
    return True

def create_point_locations_file(points, output_dir):
    """创建包含点位置信息的CSV文件"""
    print("创建点位置文件...")
    
    location_file = os.path.join(output_dir, "meteo_locations.csv")
    
    with open(location_file, 'w') as f:
        # 写入表头
        f.write("ID,Original_ID,GLDAS_ID,Longitude,Latitude\n")
        
        # 写入每个点的信息
        for i, point in enumerate(points):
            f.write(f"{i+1},{point['original_id']},{point['gldas_id']},{point['lon']},{point['lat']}\n")
    
    print(f"已创建点位置文件: {location_file}")
    return True

def save_points_map(user_points, gldas_points, output_dir):
    """保存用户点和GLDAS点的对应关系图"""
    print("创建点对应关系图...")
    
    plt.figure(figsize=(10, 8))
    
    # 获取用户原始点的坐标
    user_x = [float(p["original_id"].split('X')[1].split('Y')[0]) for p in gldas_points]
    user_y = [float(p["original_id"].split('Y')[1]) for p in gldas_points]
    plt.scatter(user_x, user_y, c='blue', marker='o', s=80, label='User Points')
    
    # GLDAS点
    gldas_x = [p["lon"] for p in gldas_points]
    gldas_y = [p["lat"] for p in gldas_points]
    plt.scatter(gldas_x, gldas_y, c='red', marker='x', s=100, label='GLDAS Points')
    
    # 连接对应的点
    for i in range(len(gldas_points)):
        plt.plot([user_x[i], gldas_x[i]], [user_y[i], gldas_y[i]], 'k--', alpha=0.5)
    
    # 添加点ID标签
    for i, p in enumerate(gldas_points):
        plt.annotate(p["original_id"], (user_x[i], user_y[i]), 
                    textcoords="offset points", xytext=(0,10), ha='center')
    
    for i, p in enumerate(gldas_points):
        plt.annotate(p["gldas_id"], (gldas_x[i], gldas_y[i]), 
                    textcoords="offset points", xytext=(0,-15), ha='center')
    
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.title('User Points and Corresponding GLDAS Points')
    plt.legend()
    plt.grid(True)
    
    # 保存图像
    map_file = os.path.join(output_dir, "meteo_points_map.png")
    plt.savefig(map_file)
    plt.close()
    
    print(f"已创建点对应关系图: {map_file}")
    return True

def main():
    """主函数"""
    # 解析命令行参数
    args = parse_arguments()
    
    # 创建目录结构
    dirs = create_directories(args.output_dir)
    
    # 获取用户指定的点
    user_points = []
    if args.points:
        user_points = parse_point_list(args.points)
    elif args.point_file:
        user_points = read_points_from_file(args.point_file)
    
    if not user_points:
        print("错误: 没有提供有效的坐标点。请使用--points或--point-file指定坐标点。")
        return 1
    
    print(f"用户指定了{len(user_points)}个坐标点")
    
    # 获取所有NC4文件
    print("搜索GLDAS数据文件...")
    nc4_files = get_nc4_files(args.data_dir, "*.nc4*")
    if not nc4_files:
        print("没有找到NC4文件，退出")
        return 1
    
    print(f"找到{len(nc4_files)}个NC4文件")
    
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
    
    # 从缓存文件生成CSV
    for cache_file in cache_files:
        process_cache_to_csv(cache_file, dirs["csv"], args.force)
    
    # 创建meteo.tsd.forc文件
    create_meteotsd_file(dirs["csv"], gldas_points, args.output_dir)
    
    # 创建点位置信息文件
    create_point_locations_file(gldas_points, args.output_dir)
    
    # 保存点对应关系图
    save_points_map(user_points, gldas_points, dirs["fig"])
    
    print("处理完成!")
    print(f"SHUD气象驱动数据已保存在 {args.output_dir} 目录")
    print(f"1. meteo.tsd.forc - SHUD气象配置文件")
    print(f"2. csv/ - 各点的气象数据")
    print(f"3. meteo_locations.csv - 气象点位置信息")
    print(f"4. fig/meteo_points_map.png - 点对应关系图")
    
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
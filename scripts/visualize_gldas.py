#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GLDAS数据可视化脚本 - 可视化处理后的GLDAS数据
"""

import os
import sys
import argparse
import glob
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import numpy as np

def get_parent_dir():
    """获取上级目录路径"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    return parent_dir

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="GLDAS数据可视化工具")
    
    parser.add_argument("--csv-dir", default="../output/csv", 
                        help="CSV文件目录，默认为'../output/csv'")
    
    parser.add_argument("--output-dir", default="../output/fig", 
                        help="图表输出目录，默认为'../output/fig'")
    
    parser.add_argument("--point", 
                        help="要可视化的特定点，格式为'X11.125Y43.625'")
    
    parser.add_argument("--all", action="store_true", 
                        help="可视化所有点的数据")
    
    parser.add_argument("--variable", default="all", 
                        choices=["all", "precip", "temp", "rh", "wind", "radiation", "pressure"], 
                        help="要可视化的变量，默认为'all'")
    
    return parser.parse_args()

def read_csv_file(file_path):
    """读取GLDAS CSV文件"""
    try:
        # 读取第一行元数据
        with open(file_path, 'r') as f:
            metadata = f.readline().strip().split('\t')
        
        # 解析元数据
        num_rows = int(metadata[0])
        num_cols = int(metadata[1])
        start_date_str = metadata[2]
        end_date_str = metadata[3]
        time_step = int(metadata[4])  # 秒
        
        # 解析日期
        start_date = datetime.strptime(start_date_str, "%Y%m%d")
        
        # 读取数据（跳过第一行元数据）
        df = pd.read_csv(file_path, sep='\t', skiprows=1)
        
        # 计算实际日期时间
        dates = []
        for interval in df['Time_interval']:
            delta_days = float(interval)
            dates.append(start_date + timedelta(days=delta_days))
        
        df['datetime'] = dates
        
        return df, start_date, time_step
    
    except Exception as e:
        print(f"读取CSV文件失败: {str(e)}")
        return None, None, None

def plot_variable(ax, df, variable, title, ylabel, color='blue'):
    """绘制单个变量的时间序列图"""
    ax.plot(df['datetime'], df[variable], color=color, marker='.', markersize=3, linestyle='-', linewidth=1)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.grid(True, linestyle='--', alpha=0.7)
    
    # 设置x轴日期格式
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=5))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    return ax

def visualize_point_data(csv_file, output_dir, variable="all"):
    """可视化单个点的数据"""
    point_id = os.path.basename(csv_file).replace('.csv', '')
    
    # 读取数据
    df, start_date, time_step = read_csv_file(csv_file)
    if df is None:
        return False
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    if variable == "all":
        # 创建包含所有变量的图表
        fig, axes = plt.subplots(6, 1, figsize=(10, 15), sharex=True)
        fig.suptitle(f"GLDAS数据 - 点 {point_id}", fontsize=16)
        
        # 绘制各变量
        plot_variable(axes[0], df, 'Precip_mm.d', '降水', '降水量 (mm/day)', 'blue')
        plot_variable(axes[1], df, 'Temp_C', '温度', '温度 (°C)', 'red')
        plot_variable(axes[2], df, 'RH_1', '相对湿度', '相对湿度 (0-1)', 'green')
        plot_variable(axes[3], df, 'Wind_m.s', '风速', '风速 (m/s)', 'purple')
        plot_variable(axes[4], df, 'RN_w.m2', '短波辐射', '辐射 (W/m²)', 'orange')
        plot_variable(axes[5], df, 'Pres_pa', '气压', '气压 (Pa)', 'brown')
        
        # 调整布局
        plt.tight_layout()
        plt.subplots_adjust(top=0.95)
        
        # 保存图表
        output_file = os.path.join(output_dir, f"{point_id}_all_variables.png")
        plt.savefig(output_file, dpi=300)
        plt.close()
        
        print(f"已保存图表: {output_file}")
    else:
        # 绘制单个变量
        var_map = {
            "precip": ('Precip_mm.d', '降水', '降水量 (mm/day)', 'blue'),
            "temp": ('Temp_C', '温度', '温度 (°C)', 'red'),
            "rh": ('RH_1', '相对湿度', '相对湿度 (0-1)', 'green'),
            "wind": ('Wind_m.s', '风速', '风速 (m/s)', 'purple'),
            "radiation": ('RN_w.m2', '短波辐射', '辐射 (W/m²)', 'orange'),
            "pressure": ('Pres_pa', '气压', '气压 (Pa)', 'brown')
        }
        
        if variable in var_map:
            var_col, var_title, var_ylabel, var_color = var_map[variable]
            
            fig, ax = plt.subplots(figsize=(10, 6))
            fig.suptitle(f"GLDAS数据 - 点 {point_id} - {var_title}", fontsize=16)
            
            plot_variable(ax, df, var_col, var_title, var_ylabel, var_color)
            
            # 调整布局
            plt.tight_layout()
            plt.subplots_adjust(top=0.95)
            
            # 保存图表
            output_file = os.path.join(output_dir, f"{point_id}_{variable}.png")
            plt.savefig(output_file, dpi=300)
            plt.close()
            
            print(f"已保存图表: {output_file}")
        else:
            print(f"未知变量: {variable}")
            return False
    
    return True

def main():
    """主函数"""
    args = parse_args()
    
    # 获取项目根目录
    parent_dir = get_parent_dir()
    
    # 解析CSV目录路径
    if os.path.isabs(args.csv_dir):
        csv_dir = args.csv_dir
    else:
        csv_dir = os.path.join(parent_dir, args.csv_dir.lstrip('./'))
    
    # 解析输出目录路径
    if os.path.isabs(args.output_dir):
        output_dir = args.output_dir
    else:
        output_dir = os.path.join(parent_dir, args.output_dir.lstrip('./'))
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    print("=" * 80)
    print("GLDAS数据可视化工具")
    print("=" * 80)
    print(f"CSV文件目录: {csv_dir}")
    print(f"图表输出目录: {output_dir}")
    if args.point:
        print(f"要可视化的点: {args.point}")
    print(f"要可视化的变量: {args.variable}")
    print("=" * 80)
    
    # 检查CSV目录是否存在
    if not os.path.exists(csv_dir):
        print(f"错误: CSV目录不存在: {csv_dir}")
        return 1
    
    # 获取CSV文件列表
    if args.point:
        # 可视化特定点
        csv_file = os.path.join(csv_dir, f"{args.point}.csv")
        if not os.path.exists(csv_file):
            print(f"错误: CSV文件不存在: {csv_file}")
            return 1
        
        success = visualize_point_data(csv_file, output_dir, args.variable)
        if not success:
            return 1
    else:
        # 可视化所有点或者第一个点
        csv_files = glob.glob(os.path.join(csv_dir, "X*.csv"))
        if not csv_files:
            print(f"错误: 在目录 {csv_dir} 中未找到CSV文件")
            return 1
        
        if args.all:
            # 可视化所有点
            for csv_file in csv_files:
                print(f"处理文件: {os.path.basename(csv_file)}")
                visualize_point_data(csv_file, output_dir, args.variable)
        else:
            # 只可视化第一个点
            csv_file = csv_files[0]
            print(f"处理文件: {os.path.basename(csv_file)}")
            success = visualize_point_data(csv_file, output_dir, args.variable)
            if not success:
                return 1
    
    print(f"\n可视化完成! 图表已保存到: {output_dir}")
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 
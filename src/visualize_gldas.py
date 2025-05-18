#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GLDAS点位气象数据可视化工具
功能:
1. 读取SHUD格式的CSV气象数据文件
2. 可视化各种气象变量（降水、温度、湿度、风速等）
3. 生成时间序列图表
"""

import os
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="可视化GLDAS点位气象数据")
    parser.add_argument("--csv-dir", default="output/csv", help="CSV文件目录")
    parser.add_argument("--output-dir", default="output/fig", help="图表输出目录")
    parser.add_argument("--point", required=True, help="要可视化的点ID")
    parser.add_argument("--variable", default="all", 
                        choices=["all", "precip", "temp", "rh", "wind", "radiation", "pressure"],
                        help="要可视化的变量")
    return parser.parse_args()

def read_csv_file(csv_file):
    """读取SHUD格式CSV文件"""
    try:
        # 读取第一行元数据
        with open(csv_file, 'r') as f:
            meta = f.readline().strip().split('\t')
            if len(meta) < 5:
                print(f"错误: CSV文件格式不正确: {csv_file}")
                return None, None
            
            num_rows = int(meta[0])
            num_cols = int(meta[1])
            start_date_str = meta[2]
            end_date_str = meta[3]
            time_step_sec = int(meta[4])
            
        # 读取数据（从第二行开始）
        df = pd.read_csv(csv_file, sep='\t', skiprows=1)
        
        # 解析起始日期
        start_date = datetime.strptime(start_date_str, '%Y%m%d')
        
        # 创建日期时间列
        dates = []
        for interval in df['Time_interval']:
            # 间隔以天为单位，转换为小时
            hours = interval * 24
            dates.append(start_date + timedelta(hours=hours))
        
        df['datetime'] = dates
        
        return df, time_step_sec
    
    except Exception as e:
        print(f"读取CSV文件时出错: {str(e)}")
        return None, None

def plot_variable(df, variable, output_file, point_id):
    """绘制特定变量的时间序列图"""
    if variable not in df.columns:
        print(f"错误: 变量 {variable} 不在数据中")
        return False
    
    plt.figure(figsize=(12, 6))
    
    # 设置标题和变量标签映射
    var_labels = {
        'Precip_mm.d': '降水量 (mm/day)',
        'Temp_C': '温度 (°C)',
        'RH_1': '相对湿度 (0-1)',
        'Wind_m.s': '风速 (m/s)',
        'RN_w.m2': '辐射 (W/m²)',
        'Pres_pa': '气压 (Pa)'
    }
    
    # 绘制时间序列
    plt.plot(df['datetime'], df[variable], '-o', markersize=3)
    
    # 设置图表格式
    plt.title(f"点 {point_id} 的 {var_labels.get(variable, variable)}")
    plt.xlabel('日期时间')
    plt.ylabel(var_labels.get(variable, variable))
    plt.grid(True)
    
    # 设置合理的x轴日期格式
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=5))
    plt.gcf().autofmt_xdate()
    
    # 保存图表
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    plt.close()
    
    print(f"图表已保存: {output_file}")
    return True

def plot_all_variables(df, output_dir, point_id):
    """绘制所有气象变量图"""
    variables = [
        'Precip_mm.d',
        'Temp_C',
        'RH_1',
        'Wind_m.s',
        'RN_w.m2',
        'Pres_pa'
    ]
    
    for var in variables:
        if var in df.columns:
            output_file = os.path.join(output_dir, f"{point_id}_{var}.png")
            plot_variable(df, var, output_file, point_id)

def create_summary_plot(df, output_file, point_id):
    """创建包含所有变量的总结图"""
    variables = [
        'Precip_mm.d',
        'Temp_C',
        'RH_1',
        'Wind_m.s',
        'RN_w.m2',
        'Pres_pa'
    ]
    
    var_labels = {
        'Precip_mm.d': '降水量 (mm/day)',
        'Temp_C': '温度 (°C)',
        'RH_1': '相对湿度 (0-1)',
        'Wind_m.s': '风速 (m/s)',
        'RN_w.m2': '辐射 (W/m²)',
        'Pres_pa': '气压 (Pa)'
    }
    
    # 统计有效变量的数量
    valid_vars = [var for var in variables if var in df.columns]
    n_vars = len(valid_vars)
    
    if n_vars == 0:
        print("警告: 没有有效的变量可以绘图")
        return False
    
    # 创建子图
    fig, axs = plt.subplots(n_vars, 1, figsize=(12, 3*n_vars), sharex=True)
    if n_vars == 1:
        axs = [axs]  # 确保axs是一个列表
    
    # 绘制每个变量
    for i, var in enumerate(valid_vars):
        axs[i].plot(df['datetime'], df[var], '-', color=f"C{i}")
        axs[i].set_ylabel(var_labels.get(var, var))
        axs[i].grid(True)
    
    # 设置共享的x轴格式
    axs[-1].xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    axs[-1].xaxis.set_major_locator(mdates.DayLocator(interval=5))
    plt.gcf().autofmt_xdate()
    
    # 设置总标题
    plt.suptitle(f"点 {point_id} 的气象时间序列", fontsize=16)
    plt.tight_layout()
    plt.subplots_adjust(top=0.95)
    
    # 保存图表
    plt.savefig(output_file, dpi=300)
    plt.close()
    
    print(f"总结图已保存: {output_file}")
    return True

def main():
    """主函数"""
    # 解析命令行参数
    args = parse_arguments()
    
    # 确保输出目录存在
    os.makedirs(args.output_dir, exist_ok=True)
    
    # 构造CSV文件路径
    csv_file = os.path.join(args.csv_dir, f"{args.point}.csv")
    if not os.path.exists(csv_file):
        print(f"错误: 找不到CSV文件: {csv_file}")
        return 1
    
    # 读取CSV文件
    df, time_step = read_csv_file(csv_file)
    if df is None:
        return 1
    
    # 根据用户选择的变量，绘制相应图表
    if args.variable == "all":
        # 绘制所有变量
        plot_all_variables(df, args.output_dir, args.point)
        
        # 创建总结图
        summary_file = os.path.join(args.output_dir, f"{args.point}_summary.png")
        create_summary_plot(df, summary_file, args.point)
    else:
        # 变量名映射
        var_map = {
            "precip": "Precip_mm.d",
            "temp": "Temp_C",
            "rh": "RH_1",
            "wind": "Wind_m.s",
            "radiation": "RN_w.m2",
            "pressure": "Pres_pa"
        }
        
        # 获取对应的列名
        column_name = var_map.get(args.variable)
        if column_name is None:
            print(f"错误: 不支持的变量: {args.variable}")
            return 1
        
        # 绘制单个变量
        output_file = os.path.join(args.output_dir, f"{args.point}_{column_name}.png")
        if not plot_variable(df, column_name, output_file, args.point):
            return 1
    
    print(f"点 {args.point} 的可视化完成")
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
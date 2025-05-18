#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
使用matplotlib可视化转换后的shapefile文件
"""

import os
import sys
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

def visualize_shapefile(shapefile_path, output_image=None):
    """
    可视化shapefile文件
    
    参数:
        shapefile_path: shapefile路径(.shp)
        output_image: 可选的输出图像路径，如果不提供则显示图像
    """
    try:
        # 读取shapefile
        gdf = gpd.read_file(shapefile_path)
        
        # 获取文件名作为标题
        title = os.path.basename(shapefile_path)
        
        # 创建图形
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # 判断是否有'name'列，有则用作标签
        if 'name' in gdf.columns:
            # 获取唯一名称
            unique_names = gdf['name'].unique()
            
            # 生成颜色列表
            colors = plt.cm.tab10(range(len(unique_names)))
            
            # 创建图例元素
            legend_elements = []
            
            # 为每个名称绘制不同颜色
            for i, name in enumerate(unique_names):
                subset = gdf[gdf['name'] == name]
                color = colors[i % len(colors)]
                subset.plot(ax=ax, color=color, alpha=0.7)
                
                # 添加图例项
                legend_elements.append(
                    Patch(facecolor=color, alpha=0.7, label=name)
                )
            
            # 添加图例
            ax.legend(handles=legend_elements, loc='upper right', fontsize=8)
            
        else:
            # 直接绘制
            gdf.plot(ax=ax, cmap='tab10', alpha=0.7)
        
        # 设置标题和轴标签
        ax.set_title(f"Shapefile: {title}")
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        
        # 添加网格
        ax.grid(True, linestyle='--', alpha=0.6)
        
        # 边界设置为紧凑
        plt.tight_layout()
        
        # 保存或显示
        if output_image:
            plt.savefig(output_image, dpi=300)
            print(f"图像已保存至: {output_image}")
        else:
            plt.show()
            
        return True
        
    except Exception as e:
        print(f"可视化过程中出错: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("用法: python visualize_shp.py <shapefile路径> [输出图像路径]")
        print("示例: python visualize_shp.py output/wmc_layers.shp output/wmc_map.png")
        return
    
    shapefile_path = sys.argv[1]
    
    # 检查是否提供了输出路径
    output_image = None
    if len(sys.argv) > 2:
        output_image = sys.argv[2]
    
    # 确保输出目录存在
    if output_image:
        output_dir = os.path.dirname(output_image)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    # 检查shapefile是否存在
    if not os.path.exists(shapefile_path):
        print(f"错误: Shapefile不存在: {shapefile_path}")
        return
    
    # 可视化shapefile
    visualize_shapefile(shapefile_path, output_image)

if __name__ == "__main__":
    main() 
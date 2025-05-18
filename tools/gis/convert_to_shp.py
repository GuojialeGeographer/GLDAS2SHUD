#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
将mao.json或context.wmc文件转换为shp格式
"""

import os
import sys
import json
import xml.etree.ElementTree as ET
import geopandas as gpd
from shapely.geometry import Point, Polygon, LineString
import pandas as pd
import fiona

def convert_json_to_shp(json_file, output_shp):
    """
    将mao.json文件转换为shp格式
    
    参数:
        json_file: mao.json文件路径
        output_shp: 输出shp文件路径
    """
    print(f"正在转换 {json_file} 到 {output_shp}")
    
    # 读取JSON文件
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 创建空的GeoDataFrame列表用于存储不同类型的几何图形
    points_data = []
    lines_data = []
    polygons_data = []
    
    # 解析JSON数据 - 这里需要根据mao.json的实际结构进行调整
    # 以下为通用处理方式，实际使用时需要根据文件结构调整
    
    try:
        # 如果是包含features的GeoJSON格式
        if 'features' in data:
            for feature in data['features']:
                properties = feature.get('properties', {})
                geometry = feature.get('geometry', {})
                geom_type = geometry.get('type')
                coordinates = geometry.get('coordinates')
                
                if geom_type == 'Point':
                    points_data.append({
                        'geometry': Point(coordinates),
                        **properties
                    })
                elif geom_type == 'LineString':
                    lines_data.append({
                        'geometry': LineString(coordinates),
                        **properties
                    })
                elif geom_type == 'Polygon':
                    polygons_data.append({
                        'geometry': Polygon(coordinates[0], coordinates[1:]),
                        **properties
                    })
        # 根据mao.json的特定结构进行解析
        else:
            # 此处需要根据实际的mao.json结构编写解析逻辑
            print("警告: 无法识别的JSON格式，请根据实际文件结构调整代码")
            return
            
        # 创建GeoDataFrames
        if points_data:
            points_gdf = gpd.GeoDataFrame(points_data, crs="EPSG:4326")
            points_gdf.to_file(output_shp.replace('.shp', '_points.shp'))
            print(f"点要素已保存到 {output_shp.replace('.shp', '_points.shp')}")
            
        if lines_data:
            lines_gdf = gpd.GeoDataFrame(lines_data, crs="EPSG:4326")
            lines_gdf.to_file(output_shp.replace('.shp', '_lines.shp'))
            print(f"线要素已保存到 {output_shp.replace('.shp', '_lines.shp')}")
            
        if polygons_data:
            polygons_gdf = gpd.GeoDataFrame(polygons_data, crs="EPSG:4326")
            polygons_gdf.to_file(output_shp.replace('.shp', '_polygons.shp'))
            print(f"面要素已保存到 {output_shp.replace('.shp', '_polygons.shp')}")
            
    except Exception as e:
        print(f"转换过程中出错: {e}")
    
def convert_wmc_to_shp(wmc_file, output_shp):
    """
    将context.wmc文件转换为shp格式
    
    参数:
        wmc_file: context.wmc文件路径
        output_shp: 输出shp文件路径
    """
    print(f"正在转换 {wmc_file} 到 {output_shp}")
    
    try:
        # 解析WMC (Web Map Context) XML文件
        tree = ET.parse(wmc_file)
        root = tree.getroot()
        
        # 查找命名空间
        namespaces = {'wmc': 'http://www.opengis.net/context'}
        for prefix, uri in root.attrib.items():
            if prefix.startswith('xmlns:'):
                ns_prefix = prefix.split(':')[1]
                namespaces[ns_prefix] = uri
        
        # 提取图层信息
        layers_data = []
        
        # 查找图层元素 - 根据WMC格式调整XPath
        layer_elements = root.findall('.//wmc:Layer', namespaces)
        
        if not layer_elements:
            print("在WMC文件中未找到图层信息，尝试其他XPath...")
            # 尝试其他可能的XPath
            layer_elements = root.findall('.//*[local-name()="Layer"]')
        
        for layer in layer_elements:
            layer_name = layer.find('.//wmc:Title', namespaces)
            if layer_name is None:
                layer_name = layer.find('.//*[local-name()="Title"]')
            
            layer_name = layer_name.text if layer_name is not None else "未命名图层"
            
            # 尝试获取图层的几何信息 - 这里需要根据WMC文件的具体结构进行调整
            # WMC通常不直接包含几何数据，而是包含图层的引用
            # 如果文件中包含BoundingBox信息，可以提取为Polygon
            bbox = layer.find('.//wmc:BoundingBox', namespaces)
            if bbox is None:
                bbox = layer.find('.//*[local-name()="BoundingBox"]')
            
            if bbox is not None:
                minx = float(bbox.get('minx', 0))
                miny = float(bbox.get('miny', 0))
                maxx = float(bbox.get('maxx', 0))
                maxy = float(bbox.get('maxy', 0))
                
                # 创建边界框多边形
                bbox_polygon = Polygon([
                    (minx, miny), (maxx, miny), 
                    (maxx, maxy), (minx, maxy), 
                    (minx, miny)
                ])
                
                layers_data.append({
                    'name': layer_name,
                    'geometry': bbox_polygon,
                    'type': 'bbox'
                })
            
            # 如果有其他类型的几何信息，可以在这里添加处理逻辑
        
        if layers_data:
            # 创建GeoDataFrame并保存为shp
            gdf = gpd.GeoDataFrame(layers_data, crs="EPSG:4326")
            gdf.to_file(output_shp)
            print(f"已成功将WMC文件转换为Shapefile: {output_shp}")
        else:
            print("未找到可转换的几何数据。WMC文件通常不直接包含几何数据，而是包含图层的引用。")
            print("您可能需要单独获取WMC文件引用的原始数据源。")
    
    except Exception as e:
        print(f"转换WMC文件时出错: {e}")

def main():
    if len(sys.argv) < 3:
        print("用法: python convert_to_shp.py <输入文件> <输出shp文件>")
        print("示例: python convert_to_shp.py data/shp数据/context.wmc output/result.shp")
        print("      python convert_to_shp.py data/mao.json output/result.shp")
        return
    
    input_file = sys.argv[1]
    output_shp = sys.argv[2]
    
    # 确保输出目录存在
    output_dir = os.path.dirname(output_shp)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 根据文件扩展名选择转换方法
    if input_file.lower().endswith('.json'):
        convert_json_to_shp(input_file, output_shp)
    elif input_file.lower().endswith('.wmc'):
        convert_wmc_to_shp(input_file, output_shp)
    else:
        print(f"不支持的文件类型: {input_file}")
        print("支持的文件类型: .json, .wmc")

if __name__ == "__main__":
    main() 
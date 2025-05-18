#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
将context.wmc(XML)或map.json文件转换为shp格式
依赖库：
- geopandas
- shapely
- pandas
- fiona
- lxml (用于XML解析)
"""

import os
import sys
import json
import xml.etree.ElementTree as ET
import geopandas as gpd
from shapely.geometry import Point, Polygon, LineString, box
import pandas as pd
import fiona

def convert_json_to_shp(json_file, output_shp):
    """
    将JSON文件转换为shp格式
    
    参数:
        json_file: JSON文件路径
        output_shp: 输出shp文件路径
    """
    print(f"正在转换 {json_file} 到 {output_shp}")
    
    # 读取JSON文件
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 创建空的GeoDataFrame列表用于存储不同类型的几何图形
    features = []
    
    # 解析JSON数据 - 针对MapStore格式的map.json文件
    try:
        if 'map' in data and 'layers' in data['map']:
            # 处理MapStore格式
            for layer in data['map']['layers']:
                layer_id = layer.get('id', '')
                layer_name = layer.get('name', '')
                layer_title = layer.get('title', '')
                layer_type = layer.get('type', '')
                
                # 尝试提取bbox信息
                if 'bbox' in layer and 'bounds' in layer['bbox']:
                    bounds = layer['bbox']['bounds']
                    minx = float(bounds.get('minx', 0))
                    miny = float(bounds.get('miny', 0))
                    maxx = float(bounds.get('maxx', 0))
                    maxy = float(bounds.get('maxy', 0))
                    
                    # 创建边界框几何体
                    geometry = box(minx, miny, maxx, maxy)
                    
                    # 添加到特征列表
                    features.append({
                        'geometry': geometry,
                        'id': layer_id,
                        'name': layer_name,
                        'title': layer_title,
                        'type': layer_type
                    })
        # 如果是GeoJSON格式
        elif 'features' in data:
            for feature in data['features']:
                properties = feature.get('properties', {})
                geometry_data = feature.get('geometry', {})
                geom_type = geometry_data.get('type')
                coordinates = geometry_data.get('coordinates')
                
                geometry = None
                if geom_type == 'Point':
                    geometry = Point(coordinates)
                elif geom_type == 'LineString':
                    geometry = LineString(coordinates)
                elif geom_type == 'Polygon':
                    geometry = Polygon(coordinates[0], coordinates[1:])
                
                if geometry:
                    features.append({
                        'geometry': geometry,
                        **properties
                    })
        else:
            print("警告: 无法识别的JSON格式，尝试使用其他方法...")
            
            # 尝试从地图中心和范围创建一个边界框
            if 'map' in data and 'center' in data['map']:
                center = data['map']['center']
                # 使用中心点创建一个小范围的边界框
                x = center.get('x', 0)
                y = center.get('y', 0)
                
                # 创建一个围绕中心点的边界框
                buffer = 0.1  # 约10公里的缓冲区
                geometry = box(x - buffer, y - buffer, x + buffer, y + buffer)
                
                features.append({
                    'geometry': geometry,
                    'name': 'map_extent',
                    'description': '从地图中心创建的边界框'
                })
                
        # 创建GeoDataFrame并保存
        if features:
            gdf = gpd.GeoDataFrame(features, crs="EPSG:4326")
            gdf.to_file(output_shp)
            print(f"成功将JSON文件转换为Shapefile: {output_shp}")
            return True
        else:
            print("未找到可转换的几何数据")
            return False
    
    except Exception as e:
        print(f"转换过程中出错: {e}")
        return False

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
        
        # 获取XML命名空间
        namespaces = {}
        for prefix, uri in root.attrib.items():
            if prefix.startswith('xmlns:'):
                ns_prefix = prefix.split(':')[1]
                namespaces[ns_prefix] = uri
        
        # 设置主要的命名空间
        ns = {'context': namespaces.get('', 'http://www.opengis.net/context')}
        
        # 提取边界框信息
        features = []
        
        # 先尝试从General部分获取BoundingBox
        general_bbox = root.find('.//BoundingBox')
        if general_bbox is not None:
            minx = float(general_bbox.get('minx', 0))
            miny = float(general_bbox.get('miny', 0))
            maxx = float(general_bbox.get('maxx', 0))
            maxy = float(general_bbox.get('maxy', 0))
            
            # 创建边界框几何体
            geometry = box(minx, miny, maxx, maxy)
            
            features.append({
                'geometry': geometry,
                'name': 'general_bbox',
                'description': '地图总边界框'
            })
        
        # 查找图层元素
        layer_elements = root.findall('.//Layer')
        
        for layer in layer_elements:
            # 尝试获取图层名称
            title = layer.find('.//Title')
            layer_name = title.text if title is not None else "未命名图层"
            
            # 尝试获取服务信息
            server = layer.find('.//Server')
            service_type = server.get('service', '') if server is not None else ''
            
            # 尝试获取图层的URL
            online_resource = None
            if server is not None:
                online_resource = server.find('.//OnlineResource')
            
            url = ''
            if online_resource is not None:
                url = online_resource.get('{http://www.w3.org/1999/xlink}href', '')
            
            # 尝试获取图层的边界框
            bbox = layer.find('.//ol:maxExtent', namespaces)
            if bbox is not None:
                minx = float(bbox.get('minx', 0))
                miny = float(bbox.get('miny', 0))
                maxx = float(bbox.get('maxx', 0))
                maxy = float(bbox.get('maxy', 0))
                
                # 创建边界框几何体
                geometry = box(minx, miny, maxx, maxy)
                
                features.append({
                    'geometry': geometry,
                    'name': layer_name,
                    'service': service_type,
                    'url': url
                })
        
        # 创建GeoDataFrame并保存
        if features:
            gdf = gpd.GeoDataFrame(features, crs="EPSG:3857")  # WMC通常使用Web Mercator坐标系
            gdf.to_file(output_shp)
            print(f"成功将WMC文件转换为Shapefile: {output_shp}")
            return True
        else:
            print("未找到可转换的几何数据")
            return False
    
    except Exception as e:
        print(f"转换WMC文件时出错: {e}")
        return False

def main():
    if len(sys.argv) < 3:
        print("用法: python convert_geo_to_shp.py <输入文件> <输出shp文件>")
        print("示例: python convert_geo_to_shp.py /Users/bruce/Tools/0514GLDASdown/0515/data/shp数据/context.wmc output/wmc_layers.shp")
        print("      python convert_geo_to_shp.py /Users/bruce/Tools/0514GLDASdown/0515/data/shp数据/map.json output/map_layers.shp")
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
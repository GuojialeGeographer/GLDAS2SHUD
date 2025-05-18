#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GLDAS数据处理脚本 - 将GLDAS数据转换为SHUD水文模型可用的格式
"""

import os
import sys
import argparse
import importlib.util

def get_parent_dir():
    """获取上级目录路径"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    return parent_dir

def import_module_from_file(file_path):
    """从文件路径导入模块"""
    module_name = os.path.basename(file_path).replace('.py', '')
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="GLDAS数据处理工具 - 将GLDAS数据转换为SHUD水文模型所需格式")
    
    parser.add_argument("--data-dir", default="../data/gldas_data", 
                        help="GLDAS数据目录，默认为'../data/gldas_data'")
    
    parser.add_argument("--output-dir", default="../output", 
                        help="输出目录，默认为'../output'")
    
    parser.add_argument("--bbox", nargs=4, type=float, 
                        help="研究区域边界框(xmin ymin xmax ymax)，例如: 11.0 43.5 11.5 44.0")
    
    parser.add_argument("--buffer", type=float, default=0.1, 
                        help="边界框缓冲距离(度)，默认为0.1度")
    
    parser.add_argument("--force", action="store_true", 
                        help="强制重新处理已存在的文件")
    
    return parser.parse_args()

def main():
    """主函数"""
    # 获取命令行参数
    args = parse_args()
    
    # 获取项目根目录
    parent_dir = get_parent_dir()
    
    # 导入gldas_to_shud模块
    gldas_module_path = os.path.join(parent_dir, 'src', 'gldas_to_shud.py')
    if not os.path.exists(gldas_module_path):
        print(f"错误: 未找到gldas_to_shud.py文件: {gldas_module_path}")
        return 1
    
    # 动态导入模块
    gldas_module = import_module_from_file(gldas_module_path)
    
    # 设置参数
    class Args:
        def __init__(self):
            # 解析数据目录路径
            if os.path.isabs(args.data_dir):
                self.data_dir = args.data_dir
            else:
                self.data_dir = os.path.join(parent_dir, args.data_dir.lstrip('./'))
            
            # 解析输出目录路径
            if os.path.isabs(args.output_dir):
                self.output_dir = args.output_dir
            else:
                self.output_dir = os.path.join(parent_dir, args.output_dir.lstrip('./'))
            
            self.bbox = args.bbox
            self.buffer = args.buffer
            self.force = args.force
    
    # 创建参数对象
    module_args = Args()
    
    # 确保目录存在
    os.makedirs(module_args.data_dir, exist_ok=True)
    os.makedirs(module_args.output_dir, exist_ok=True)
    
    print("=" * 80)
    print("GLDAS数据处理工具")
    print("=" * 80)
    print(f"数据目录: {module_args.data_dir}")
    print(f"输出目录: {module_args.output_dir}")
    if module_args.bbox:
        print(f"研究区域: {module_args.bbox}")
    print(f"缓冲距离: {module_args.buffer}度")
    print(f"强制重写: {'是' if module_args.force else '否'}")
    print("=" * 80)
    
    # 检查数据目录中是否有文件
    if not os.listdir(module_args.data_dir):
        print(f"警告: 数据目录 '{module_args.data_dir}' 为空!")
        print("请先下载GLDAS数据文件到该目录，或使用 download_gldas.py 脚本下载数据。")
        return 1
    
    # 调用gldas_to_shud模块的main函数
    return gldas_module.main_with_args(module_args)

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 
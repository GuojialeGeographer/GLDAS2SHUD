#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GLDAS数据下载脚本 - 从NASA GES DISC下载GLDAS数据
"""

import os
import sys
import argparse
import subprocess
import getpass
import netrc
import glob
import platform
from datetime import datetime

def get_parent_dir():
    """获取上级目录路径"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    return parent_dir

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="GLDAS数据下载工具")
    
    parser.add_argument("--data-dir", default="../data/gldas_data", 
                        help="下载数据保存目录，默认为'../data/gldas_data'")
    
    parser.add_argument("--username", 
                        help="NASA Earthdata用户名")
    
    parser.add_argument("--password", 
                        help="NASA Earthdata密码")
    
    parser.add_argument("--list-file", 
                        help="包含下载链接的文本文件，如果不提供，将使用示例文件")
    
    parser.add_argument("--skip-auth", action="store_true", 
                        help="跳过认证步骤，使用已有的.netrc配置")
    
    return parser.parse_args()

def check_wget():
    """检查wget是否已安装"""
    try:
        subprocess.run(["wget", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except FileNotFoundError:
        return False

def install_wget():
    """根据操作系统安装wget"""
    system = platform.system()
    
    if system == "Darwin":  # macOS
        print("在macOS上安装wget...")
        try:
            subprocess.run(["brew", "install", "wget"], check=True)
            return True
        except subprocess.CalledProcessError:
            print("使用Homebrew安装wget失败。请手动安装: brew install wget")
        except FileNotFoundError:
            print("未找到Homebrew。请先安装Homebrew: /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
    
    elif system == "Linux":
        # 检测Linux发行版
        try:
            if os.path.exists("/etc/debian_version"):  # Debian/Ubuntu
                print("在Debian/Ubuntu上安装wget...")
                subprocess.run(["sudo", "apt", "update"], check=True)
                subprocess.run(["sudo", "apt", "install", "-y", "wget"], check=True)
                return True
            elif os.path.exists("/etc/redhat-release"):  # RHEL/CentOS/Fedora
                print("在RHEL/CentOS/Fedora上安装wget...")
                subprocess.run(["sudo", "yum", "install", "-y", "wget"], check=True)
                return True
            else:
                print("未能识别的Linux发行版。请手动安装wget。")
        except subprocess.CalledProcessError:
            print("安装wget失败。请手动安装。")
    
    elif system == "Windows":
        print("""
在Windows上，您可以通过以下方式安装wget:
1. 使用Chocolatey: choco install wget
2. 下载二进制文件: https://eternallybored.org/misc/wget/
3. 使用WSL (Windows Subsystem for Linux)
        """)
    
    return False

def get_credentials(args):
    """获取NASA Earthdata用户名和密码"""
    username = args.username
    password = args.password
    
    if not username:
        username = input("请输入NASA Earthdata用户名: ")
    
    if not password:
        password = getpass.getpass("请输入NASA Earthdata密码: ")
    
    return username, password

def setup_netrc(username, password):
    """设置.netrc文件用于NASA Earthdata认证"""
    home_dir = os.path.expanduser("~")
    netrc_path = os.path.join(home_dir, ".netrc")
    
    # 检查是否已存在urs.earthdata.nasa.gov条目
    if os.path.exists(netrc_path):
        try:
            nrc = netrc.netrc(netrc_path)
            if 'urs.earthdata.nasa.gov' in nrc.hosts:
                print("已找到urs.earthdata.nasa.gov的认证信息，跳过.netrc设置")
                return True
        except Exception:
            # 无法解析现有.netrc，继续创建
            pass
    
    try:
        with open(netrc_path, 'a+') as f:
            f.write(f"machine urs.earthdata.nasa.gov login {username} password {password}\n")
        
        # 设置权限
        if platform.system() != "Windows":
            os.chmod(netrc_path, 0o600)
        
        print(f"已设置NASA Earthdata认证信息到: {netrc_path}")
        return True
    
    except Exception as e:
        print(f"设置.netrc文件失败: {str(e)}")
        return False

def download_data(url_list, data_dir):
    """下载GLDAS数据文件"""
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    total_files = len(url_list)
    success_count = 0
    
    for i, url in enumerate(url_list):
        url = url.strip()
        if not url or url.startswith('#'):
            continue
        
        filename = os.path.basename(url)
        outfile = os.path.join(data_dir, filename)
        
        # 检查文件是否已存在
        if os.path.exists(outfile):
            print(f"文件已存在，跳过: {filename}")
            success_count += 1
            continue
        
        print(f"下载文件 {i+1}/{total_files}: {filename}")
        
        try:
            # 使用wget下载
            result = subprocess.run(
                ["wget", "--load-cookies", "~/.urs_cookies", "--save-cookies", "~/.urs_cookies", 
                 "--keep-session-cookies", "--no-check-certificate", "-O", outfile, url],
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            
            if result.returncode == 0:
                print(f"  下载成功: {filename}")
                success_count += 1
            else:
                print(f"  下载失败: {filename}")
                print(f"  错误信息: {result.stderr}")
        
        except Exception as e:
            print(f"  下载出错: {str(e)}")
    
    print(f"\n下载完成: {success_count}/{total_files} 个文件成功")
    return success_count

def get_example_file():
    """获取示例下载链接文件"""
    parent_dir = get_parent_dir()
    example_dir = os.path.join(parent_dir, 'example')
    
    # 查找示例链接文件
    example_files = glob.glob(os.path.join(example_dir, '*GLDAS*.txt'))
    
    if example_files:
        return example_files[0]
    else:
        # 如果没有找到示例文件，创建一个
        example_file = os.path.join(example_dir, 'gldas_example_links.txt')
        with open(example_file, 'w') as f:
            # 添加一些示例链接
            f.write("# GLDAS数据下载链接示例\n")
            f.write("# 请替换为您从NASA GES DISC获取的实际链接\n")
            f.write("https://hydro1.gesdisc.eosdis.nasa.gov/data/GLDAS/GLDAS_NOAH025_3H_EP.2.1/2025/001/GLDAS_NOAH025_3H_EP.A20250101.0000.021.nc4\n")
            f.write("https://hydro1.gesdisc.eosdis.nasa.gov/data/GLDAS/GLDAS_NOAH025_3H_EP.2.1/2025/001/GLDAS_NOAH025_3H_EP.A20250101.0300.021.nc4\n")
        
        return example_file

def main():
    """主函数"""
    args = parse_args()
    
    # 获取项目根目录
    parent_dir = get_parent_dir()
    
    # 解析数据目录路径
    if os.path.isabs(args.data_dir):
        data_dir = args.data_dir
    else:
        data_dir = os.path.join(parent_dir, args.data_dir.lstrip('./'))
    
    # 确保数据目录存在
    os.makedirs(data_dir, exist_ok=True)
    
    print("=" * 80)
    print("GLDAS数据下载工具")
    print("=" * 80)
    print(f"数据保存目录: {data_dir}")
    print("=" * 80)
    
    # 检查wget
    if not check_wget():
        print("未找到wget工具，尝试安装...")
        if not install_wget():
            print("请手动安装wget后再运行此脚本。")
            return 1
    
    # 设置认证
    if not args.skip_auth:
        username, password = get_credentials(args)
        if not setup_netrc(username, password):
            print("设置NASA Earthdata认证失败，无法继续下载。")
            return 1
    
    # 获取下载链接列表
    list_file = args.list_file
    if not list_file:
        list_file = get_example_file()
        print(f"使用示例下载链接文件: {list_file}")
    
    # 读取下载链接
    try:
        with open(list_file, 'r') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        if not urls:
            print(f"下载链接文件为空: {list_file}")
            return 1
        
        print(f"共找到 {len(urls)} 个下载链接")
    except Exception as e:
        print(f"读取下载链接文件失败: {str(e)}")
        return 1
    
    # 开始下载
    success_count = download_data(urls, data_dir)
    
    if success_count > 0:
        print(f"\n数据已下载到: {data_dir}")
        print("下一步: 运行 process_gldas.py 处理数据")
        return 0
    else:
        print("\n下载失败，未成功下载任何文件。")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n下载已取消。")
        sys.exit(1)
    except Exception as e:
        print(f"\n错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 
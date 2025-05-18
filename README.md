# GLDAS2SHUD - GLDAS数据转SHUD模型工具套件

[![中文](https://img.shields.io/badge/语言-中文-red.svg)](README.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 目录

- [1. 项目概述](#1-项目概述)
- [2. 安装步骤](#2-安装步骤)
- [3. 使用教程](#3-使用教程)
  - [3.1 下载GLDAS数据](#31-下载gldas数据)
  - [3.2 定义研究区域](#32-定义研究区域)
  - [3.3 处理数据为SHUD格式](#33-处理数据为shud格式)
  - [3.4 可视化结果](#34-可视化结果)
- [4. 常见问题](#4-常见问题)
- [5. 扩展工具](#5-扩展工具)
- [6. 数据格式说明](#6-数据格式说明)
- [7. 命令参数详解](#7-命令参数详解)
- [8. 目录结构](#8-目录结构)
- [9. 许可与引用](#9-许可与引用)
- [10. 联系与支持](#10-联系与支持)

## 1. 项目概述

GLDAS2SHUD 是一个专业工具套件，用于处理 GLDAS（Global Land Data Assimilation System）气象数据并将其转换为 SHUD（Simulator for Hydrologic Unstructured Domains）水文模型所需的格式。本工具可用于全球任何区域的水文研究，让研究人员能够便捷地准备气象驱动数据。

**主要功能：**
- 下载全球范围内的GLDAS气象数据
- 提取用户自定义地点的气象数据
- 处理并转换数据为SHUD模型所需格式
- 生成数据可视化图表
- 检查数据完整性和质量

## 2. 安装步骤

### 2.1 环境要求

- Python 3.6+ 
- Git (可选，用于克隆仓库)
- 操作系统：Windows、macOS或Linux

### 2.2 获取代码

```bash
# 克隆仓库（如已下载可跳过此步骤）
git clone https://github.com/yourusername/GLDAS2SHUD.git
cd GLDAS2SHUD
```

### 2.3 安装依赖

**方法1：使用Conda（推荐）**

```bash
# 安装Anaconda或Miniconda（如已安装可跳过）
# 请访问 https://docs.conda.io/en/latest/miniconda.html 下载安装

# 创建并激活环境
conda env create -f environment.yml
conda activate gldas-env
```

**方法2：使用pip**

```bash
# 创建虚拟环境（可选但推荐）
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2.4 验证安装

```bash
# 检查是否能够导入必要模块
python -c "import numpy; import pandas; import xarray; import matplotlib; print('安装成功!')"
```

## 3. 使用教程

### 3.1 下载GLDAS数据

在下载前，您**必须**先注册NASA Earthdata账号：

1. 访问 [NASA Earthdata 登录页面](https://urs.earthdata.nasa.gov/)
2. 点击"Register"注册新账号
3. 登录后，前往 Applications -> Authorized Apps，点击"Approve More Applications"
4. 在列表中找到并添加"NASA GESDISC DATA ARCHIVE"

**方法1：使用Python脚本（推荐）**

```bash
# 下载GLDAS数据（必须提供NASA账号）
python scripts/download_gldas.py \
    --username 您的NASA用户名 \
    --password 您的NASA密码 \
    --data-dir data/gldas_data \
    --start-date 20200101 \
    --end-date 20201231
```

**方法2：使用Shell脚本**

```bash
# 下载数据（交互式输入账号密码）
./bin/download_gldas.sh
```

**下载指定时间段**

```bash
# 使用链接文件下载特定时间段
python scripts/download_gldas.py --list-only --start-date 20220101 --end-date 20220131 > my_links.txt
python scripts/download_gldas.py --list-file my_links.txt --data-dir data/gldas_data
```

### 3.2 定义研究区域

GLDAS2SHUD支持两种方式指定研究区域：

**方法1：使用坐标点列表（简单直接）**

创建一个包含坐标点的文本文件：

```bash
# 创建points.txt文件
cat > points.txt << EOF
# 格式: 经度,纬度
# 示例：以下是中国杭州湾地区的四个点
120.5,30.5
121.0,30.5
120.5,30.0
121.0,30.0
EOF
```

**方法2：使用Shapefile（适合GIS用户）**

如果您有自己的研究区域Shapefile，可以直接使用。文件应包含点要素，每个点代表一个气象数据提取位置。

### 3.3 处理数据为SHUD格式

**方法1：使用坐标点文件**

```bash
# 使用坐标点文件处理数据
python src/process_gldas_for_shud.py \
    --data-dir data/gldas_data \
    --output-dir output \
    --points-file points.txt
```

**方法2：直接在命令行指定坐标点**

```bash
# 直接指定点坐标
python src/process_gldas_for_shud.py \
    --data-dir data/gldas_data \
    --output-dir output \
    --points "120.5,30.5" "121.0,30.5" "120.5,30.0" "121.0,30.0"
```

**方法3：使用Shapefile**

```bash
# 使用Shapefile文件处理数据
python src/process_gldas_for_shud.py \
    --data-dir data/gldas_data \
    --output-dir output \
    --shp-file data/your_study_area.shp
```

**高级选项：指定日期范围**

```bash
# 指定时间范围、强制覆盖已有文件等
python src/process_gldas_for_shud.py \
    --data-dir data/gldas_data \
    --output-dir output \
    --points-file points.txt \
    --start-date 20200101 \
    --end-date 20201231 \
    --force
```

### 3.4 可视化结果

```bash
# 生成所有变量的图表
python scripts/visualize_gldas.py \
    --csv-dir output/csv \
    --fig-dir output/fig \
    --all

# 查看特定点位的降水数据
python scripts/visualize_gldas.py \
    --csv-dir output/csv \
    --fig-dir output/fig \
    --point X120.5Y30.5 \
    --variable precip
```

### 3.5 检查生成的文件

```bash
# 查看生成的文件
ls -la output/
```

处理完成后，您应该能看到以下目录和文件：

- `output/csv/`: 包含每个点的气象数据CSV文件
- `output/fig/`: 包含生成的图表
- `output/meteo.tsd.forc`: SHUD模型配置文件
- `output/meteo_locations.csv`: 点位置信息
- `output/shud_project/`: 可直接用于SHUD模型的目录

### 3.6 与SHUD模型集成

```bash
# 将数据复制到SHUD项目
cp -r output/shud_project/* /path/to/your/SHUD_project/

# 或创建符号链接（更好的选择）
ln -s $(pwd)/output/shud_project /path/to/your/SHUD_project/meteo
```

## 4. 常见问题

### 4.1 安装问题

**问题**：安装时报错`ModuleNotFoundError: No module named 'xxx'`  
**解决**：手动安装缺失的包 `pip install xxx` 或检查是否已激活正确的环境

**问题**：GDAL库安装失败  
**解决**：
- Ubuntu: `sudo apt-get install libgdal-dev`
- macOS: `brew install gdal`
- Windows: 使用预编译的轮子 `pip install GDAL==$(gdal-config --version) --find-links=https://wheelhouse.sisyphe.calc.fr/`

### 4.2 数据下载问题

**问题**：NASA授权失败  
**解决**：确保已正确添加"NASA GESDISC DATA ARCHIVE"授权

**问题**：下载中断  
**解决**：使用断点续传工具 `tools/download/resume_download.sh`

**问题**：下载速度太慢  
**解决**：
- 尝试在网络良好的环境下载
- 使用单文件下载工具分批下载
- 配置代理 `export https_proxy=http://your_proxy:port`

### 4.3 数据处理问题

**问题**：坐标点不在GLDAS范围内  
**解决**：确保坐标在GLDAS覆盖范围：-60°S至90°N，-180°W至180°E

**问题**：NC4文件读取错误  
**解决**：检查netCDF4库版本，更新到最新版：`pip install netCDF4 --upgrade`

**问题**：处理时内存不足  
**解决**：减少同时处理的点数量或增加系统内存

### 4.4 输出问题

**问题**：CSV文件格式不符合预期  
**解决**：检查输入参数，特别是坐标点格式

**问题**：图形生成失败  
**解决**：确保matplotlib正常工作，对于远程服务器使用 `export MATPLOTLIB_BACKEND=Agg`

## 5. 扩展工具

GLDAS2SHUD包含三套扩展工具，位于`tools/`目录：

### 5.1 GIS工具 (`tools/gis/`)

处理地理空间数据的工具集：

```bash
# 可视化研究区域
python tools/gis/visualize_shp.py data/watershed.shp output/watershed_map.png

# 计算研究区域面积
python tools/gis/calculate_shp_area.py data/watershed.shp

# 生成水文站点shapefile
python tools/gis/generate_hydro_stations_shp.py

# 转换格式为shapefile
python tools/gis/convert_geo_to_shp.py data/map.json data/map.shp
```

### 5.2 下载优化工具 (`tools/download/`)

用于提高下载效率和可靠性的工具：

```bash
# 下载单个GLDAS文件（先编辑脚本设置日期）
vi tools/download/download_single_file.sh  # 修改TARGET_DATE和TARGET_TIME
./tools/download/download_single_file.sh

# 支持断点续传的下载器
./tools/download/resume_download.sh data/links.txt data/gldas_data

# 修复下载链接
./tools/download/fix_links_download.sh data/bad_links.txt data/gldas_data
```

### 5.3 SHUD集成工具 (`tools/shud/`)

帮助与SHUD模型集成的工具：

```bash
# 在R环境中使用
R -e "source('tools/shud/Sub2.3_Forcing_LDAS.R')"
```

## 6. 数据格式说明

### 6.1 GLDAS原始数据格式

GLDAS数据以NetCDF4格式存储，包含以下主要变量：

| 变量 | 描述 | 原始单位 |
|------|------|---------|
| Rainf_tavg | 降水率 | kg m-2 s-1 |
| Tair_f_inst | 2米气温 | K |
| Qair_f_inst | 2米比湿 | kg kg-1 |
| Wind_f_inst | 10米风速 | m s-1 |
| SWdown_f_tavg | 短波辐射 | W m-2 |
| Psurf_f_inst | 表面气压 | Pa |

### 6.2 SHUD模型所需格式

SHUD模型需要以下格式的气象数据：

**CSV文件格式**：
```
# DATE, PRECIP, TEMP, RH, WIND, SOLAR, PRESSURE
2023-01-01 00:00, 0.0, 10.5, 0.75, 2.3, 150.0, 101.3
...
```

**meteo.tsd.forc文件格式**：
```
# MeteoStationID, Longitude, Latitude, TSDB_file, nx, ny
1, 120.5, 30.5, meteo/csv/X120.5Y30.5.csv, 1, 1
...
```

### 6.3 单位转换

| 变量 | GLDAS单位 | SHUD单位 | 转换方法 |
|------|---------|---------|---------|
| 降水 | kg m-2 s-1 | mm/day | × 86400 |
| 温度 | K | ℃ | - 273.15 |
| 比湿 | kg kg-1 | 相对湿度(0-1) | 特殊转换公式 |
| 风速 | m s-1 | m s-1 | 不变 |
| 辐射 | W m-2 | W m-2 | 不变 |
| 气压 | Pa | kPa | ÷ 1000 |

## 7. 命令参数详解

### 7.1 下载命令参数

```
python scripts/download_gldas.py 
  --username <USERNAME>    # NASA Earthdata用户名
  --password <PASSWORD>    # NASA Earthdata密码
  --data-dir <DIRECTORY>   # 数据保存目录（默认：data/gldas_data）
  --start-date <YYYYMMDD>  # 开始日期（默认：近期）
  --end-date <YYYYMMDD>    # 结束日期（默认：start-date之后一个月）
  --list-file <FILENAME>   # 包含下载链接的文件
  --list-only              # 仅生成链接不下载
  --skip-auth              # 跳过认证（使用已有.netrc文件）
```

### 7.2 处理命令参数

```
python src/process_gldas_for_shud.py
  --data-dir <DIRECTORY>   # GLDAS数据目录
  --output-dir <DIRECTORY> # 输出目录
  --points "经度1,纬度1" "经度2,纬度2" ... # 坐标点列表
  --points-file <FILENAME> # 包含坐标点的文件
  --shp-file <FILENAME>    # 包含点要素的shapefile
  --start-date <YYYYMMDD>  # 开始处理的日期（默认：全部可用数据）
  --end-date <YYYYMMDD>    # 结束处理的日期（默认：全部可用数据）
  --force                  # 强制覆盖已存在的文件
```

### 7.3 可视化命令参数

```
python scripts/visualize_gldas.py
  --csv-dir <DIRECTORY>    # CSV文件目录
  --fig-dir <DIRECTORY>    # 图像输出目录
  --point <POINT_ID>       # 指定要可视化的点ID（例如：X120.5Y30.5）
  --variable <VARIABLE>    # 要可视化的变量（precip/temp/rh/wind/radiation/pressure）
  --all                    # 可视化所有变量
  --dpi <DPI>              # 图像分辨率（默认：100）
```

## 8. 目录结构

```
GLDAS2SHUD/
├── bin/                    # 可执行脚本
│   ├── check_data_integrity.sh  # 检查数据完整性
│   ├── download_gldas.sh        # 下载数据
│   ├── run_gldas.sh             # 运行GLDAS处理
│   ├── run_gldas_points.sh      # 点数据处理
│   └── run_process_gldas.sh     # 主处理脚本
├── data/                   # 数据存储目录
│   └── gldas_data/         # 存放GLDAS原始数据
├── docs/                   # 详细文档
│   └── 完整教程.md          # 完整使用教程
├── example/                # 使用示例
│   ├── example_workflow.sh # 示例工作流脚本
│   └── sample_points.txt   # 示例坐标点文件
├── output/                 # 输出结果目录
│   ├── csv/                # 生成的CSV文件
│   ├── fig/                # 生成的图表
│   └── shud_project/       # SHUD项目文件
├── scripts/                # 辅助脚本
│   ├── download_gldas.py   # 下载GLDAS数据
│   ├── process_gldas.py    # 处理GLDAS数据
│   └── visualize_gldas.py  # 可视化工具
├── src/                    # 核心源代码
│   ├── extract_from_date.py      # 按日期提取
│   ├── extract_points.py         # 提取点数据
│   ├── gldas_to_shud.py          # GLDAS转SHUD
│   ├── process_gldas_for_shud.py # 主处理流程
│   └── visualize_gldas.py        # 可视化核心
├── tools/                  # 扩展工具集
│   ├── gis/                # 地理信息系统工具
│   ├── download/           # 下载优化工具
│   ├── shud/               # SHUD模型集成工具
│   └── README.md           # 工具说明
├── environment.yml         # Conda环境配置
├── requirements.txt        # Python依赖
├── 快速使用指南.md          # 快速入门指南
└── README.md               # 本文档
```

## 9. 许可与引用

### 9.1 许可证

本项目基于 MIT 许可证开源。

### 9.2 引用方式

如果您在研究中使用了本工具，请引用：

```
Rodell, M., et al. (2004). The Global Land Data Assimilation System. Bulletin of the American Meteorological Society, 85(3), 381-394.

Shu, L. (2020). SHUD: A Simulator for Hydrologic Unstructured Domains. Journal of Open Source Software, 5(51), 2317.
```

### 9.3 数据来源

GLDAS数据由NASA提供，通过GESDISC（Goddard Earth Sciences Data and Information Services Center）分发：
https://disc.gsfc.nasa.gov/datasets/GLDAS_NOAH025_3H_EP_2.1/summary

## 10. 联系与支持

### 10.1 获取帮助

如遇问题，请参考：
- README.md（本文档）
- [完整教程](docs/完整教程.md)
- [快速使用指南](快速使用指南.md)

### 10.2 报告问题

发现Bug或有改进建议，请通过以下方式联系：
- GitHub Issues: [https://github.com/yourusername/GLDAS2SHUD/issues](https://github.com/yourusername/GLDAS2SHUD/issues)
- 电子邮件: your.email@example.com

### 10.3 贡献代码

欢迎提交Pull Request贡献代码。请确保代码符合项目规范，并附上足够的文档说明。 
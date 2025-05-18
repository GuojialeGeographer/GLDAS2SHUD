# GLDAS2SHUD 扩展工具集

本目录包含了一系列用于扩展 GLDAS2SHUD 功能的辅助工具，这些工具可以帮助您处理地理数据、优化下载过程或与 SHUD 模型进行更好的集成。

## 目录结构

```
tools/
├── gis/            # 地理信息系统工具
├── download/       # 下载优化工具
└── shud/           # SHUD模型集成工具
```

## 1. GIS 工具 (tools/gis/)

这些工具用于处理地理空间数据，特别是在 GLDAS 数据与研究区域进行空间匹配时非常有用。

- `visualize_shp.py`: 可视化 shapefile 文件，生成点位置或区域的地图
- `convert_geo_to_shp.py`: 将 context.wmc(XML) 或 map.json 文件转换为 shapefile 格式
- `convert_to_shp.py`: 将其他格式转换为 shapefile
- `calculate_shp_area.py`: 计算 shapefile 中要素的面积
- `generate_hydro_stations_shp.py`: 从坐标列表生成水文站点的 shapefile
- `update_hydro_stations.py`: 更新已有的水文站点 shapefile

### 使用示例

```bash
# 可视化研究区域的shapefile
python tools/gis/visualize_shp.py data/study_area.shp output/study_area_map.png

# 计算研究区域面积
python tools/gis/calculate_shp_area.py data/study_area.shp
```

## 2. 下载优化工具 (tools/download/)

这些工具提供了更灵活的 GLDAS 数据下载选项，特别适用于网络不稳定或需要下载大量历史数据的情况。

- `download_single_file.sh`: 下载单个特定的 GLDAS 文件
- `continue_download.sh`: 从中断处继续下载
- `fix_links_download.sh`: 修复下载链接并重试
- `resume_download.sh`: 根据已下载文件自动恢复下载

### 使用示例

```bash
# 下载特定日期的单个文件
# 编辑脚本修改 TARGET_DATE 和 TARGET_TIME 变量
./tools/download/download_single_file.sh

# 恢复中断的下载
./tools/download/resume_download.sh data/gldas_data/links.txt data/gldas_data
```

## 3. SHUD 模型集成工具 (tools/shud/)

这些工具用于将 GLDAS 数据与 SHUD 水文模型更好地集成。

- `Sub2.3_Forcing_LDAS.R`: R脚本，可以将 LDAS 格式的气象数据集成到 SHUD 模型

### 使用示例

```bash
# 在R环境中使用
R -e "source('tools/shud/Sub2.3_Forcing_LDAS.R')"
```

## 注意事项

1. 这些工具是对主要 GLDAS2SHUD 工具集的补充，提供更专业或更灵活的选项
2. 在使用前，您可能需要根据自己的需求修改脚本中的路径或参数
3. 部分工具可能需要额外的依赖包，请查看各脚本文件开头的注释 
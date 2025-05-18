#!/bin/bash

# GLDAS数据处理脚本 - 提取shapefile中的所有坐标点
# 功能：从GLDAS数据中提取指定坐标点的气象数据，并转换为SHUD模型所需的格式
# 用法：
#   ./run_process_gldas.sh [shapefile路径]

# 设置日志文件
LOG_FILE="gldas_processing.log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "================================================================="
echo "GLDAS数据处理工具 - 生成SHUD模型驱动数据"
echo "----------------------------------------------------------------"
date
echo "================================================================="

# 激活conda环境（如果有的话）
if [ -f ~/miniconda3/etc/profile.d/conda.sh ]; then
    source ~/miniconda3/etc/profile.d/conda.sh
    conda activate gldas 2>/dev/null || echo "未找到gldas环境，使用系统Python"
fi

# 设置默认参数
DATA_DIR="data/gldas_data"
OUTPUT_DIR="output"
SHP_FILE="$1"
START_DATE="20230501"  # 从2023年5月1日开始
FORCE=""

# 检查是否提供了shapefile
if [ -z "$SHP_FILE" ]; then
    echo "警告: 未提供shapefile路径，将使用默认的坐标点"
    # 默认使用四个点，与原来的run_gldas_points.sh中相同
    POINTS_ARG="--points 11.125,43.625 11.375,43.625 11.125,43.875 11.375,43.875"
else
    if [ -f "$SHP_FILE" ]; then
        echo "使用shapefile: $SHP_FILE"
        POINTS_ARG="--shp-file $SHP_FILE"
    else
        echo "错误: 提供的shapefile不存在: $SHP_FILE"
        exit 1
    fi
fi

# 清理输出目录（如果需要）
if [ -d "$OUTPUT_DIR" ]; then
    echo "输出目录已存在，将重新生成所有数据"
    FORCE="--force"
fi

echo "================================================================="
echo "开始处理GLDAS数据"
echo "数据目录: $DATA_DIR"
echo "输出目录: $OUTPUT_DIR"
echo "开始日期: $START_DATE"
echo "参数: $POINTS_ARG $FORCE"
echo "================================================================="

# 运行Python脚本
python src/process_gldas_for_shud.py \
    --data-dir "$DATA_DIR" \
    --output-dir "$OUTPUT_DIR" \
    --start-date "$START_DATE" \
    $POINTS_ARG \
    $FORCE

# 检查执行结果
if [ $? -eq 0 ]; then
    echo "================================================================="
    echo "GLDAS数据处理成功完成!"
    echo "结果保存在: $OUTPUT_DIR"
    echo "SHUD模型驱动数据位于: $OUTPUT_DIR/shud_project"
    echo "您可以直接使用这些数据运行SHUD模型"
    
    # 列出生成的文件
    echo "----------------------------------------------------------------"
    echo "生成的CSV文件:"
    ls -l "$OUTPUT_DIR/csv"
    
    echo "----------------------------------------------------------------"
    echo "SHUD项目文件:"
    ls -l "$OUTPUT_DIR/shud_project"
    echo "================================================================="
else
    echo "================================================================="
    echo "处理过程中出现错误，请检查日志信息"
    echo "================================================================="
    exit 1
fi

# 提示下一步操作
echo "要运行SHUD模型，请将$OUTPUT_DIR/shud_project目录复制到您的SHUD模型项目中"
echo "然后配置其他参数并运行模型"
echo "=================================================================" 
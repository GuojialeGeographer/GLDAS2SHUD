#!/bin/bash

# GLDAS数据处理脚本 - 使用指定坐标点
# 功能：从GLDAS数据中提取指定坐标点的气象数据，并转换为SHUD模型所需的格式
# 用法：
#   ./run_gldas_points.sh

# 设置日志文件
LOG_FILE="output_points/run_log.txt"
mkdir -p output_points

# 输出同时显示到终端和日志文件
exec > >(tee -a "$LOG_FILE") 2>&1

# 激活conda环境
echo "尝试激活gldas环境..."
if [ -f ~/miniconda3/etc/profile.d/conda.sh ]; then
    source ~/miniconda3/etc/profile.d/conda.sh
    conda activate gldas
else
    echo "conda不可用，使用系统Python环境"
fi

# 确保输出目录存在，先清理之前的数据
OUTPUT_DIR="output_points"
rm -rf $OUTPUT_DIR
mkdir -p $OUTPUT_DIR

# GLDAS数据目录
DATA_DIR="data/gldas_data/downloads"

# 指定的坐标点（经度,纬度）
# 意大利中部地区的4个点
POINTS=(
    "11.125,43.625"
    "11.375,43.625"
    "11.125,43.875"
    "11.375,43.875"
)

# 将点列表转换为命令行参数格式
POINTS_ARGS=""
for point in "${POINTS[@]}"; do
    POINTS_ARGS="$POINTS_ARGS --points $point"
done

echo "-------------------------------------------------------------------------"
echo "开始处理GLDAS数据，提取指定点位的气象数据"
echo "数据目录: $DATA_DIR"
echo "输出目录: $OUTPUT_DIR"
echo "处理的坐标点:"
for point in "${POINTS[@]}"; do
    echo "  - $point"
done
echo "最终生成的命令行参数: $POINTS_ARGS"
echo "-------------------------------------------------------------------------"

# 运行Python脚本提取数据
echo "运行提取脚本..."
python src/gldas_to_shud.py \
    --data-dir $DATA_DIR \
    --output-dir $OUTPUT_DIR \
    $POINTS_ARGS \
    --force

# 检查运行结果
if [ $? -eq 0 ]; then
    echo "-------------------------------------------------------------------------"
    echo "GLDAS数据处理完成!"
    echo "结果保存在目录: $OUTPUT_DIR"
    echo "请查看以下文件："
    echo "  - $OUTPUT_DIR/meteo.tsd.forc: SHUD气象配置文件"
    echo "  - $OUTPUT_DIR/csv/: 各点的气象数据"
    echo "  - $OUTPUT_DIR/meteo_locations.csv: 气象点位置信息"
    echo "  - $OUTPUT_DIR/fig/meteo_points_map.png: 点对应关系图"
    
    # 检查是否生成了所有四个点的文件
    echo "验证生成的CSV文件："
    ls -l $OUTPUT_DIR/csv/
else
    echo "处理过程中出现错误，请检查日志信息。"
fi

echo "-------------------------------------------------------------------------" 
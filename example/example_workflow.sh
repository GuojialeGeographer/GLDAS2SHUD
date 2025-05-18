#!/bin/bash
# GLDAS2SHUD 示例工作流
# 本脚本演示 GLDAS2SHUD 工具的完整使用流程，从数据下载到处理为 SHUD 模型所需格式

# 设置日志文件
LOG_FILE="example_workflow.log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "================================================================="
echo "GLDAS2SHUD 工具示例工作流"
echo "开始时间: $(date)"
echo "================================================================="

# 确保我们在example目录中
cd "$(dirname "$0")"

# 激活 conda 环境（如果有的话）
if [ -f ~/miniconda3/etc/profile.d/conda.sh ]; then
    source ~/miniconda3/etc/profile.d/conda.sh
    conda activate gldas-env 2>/dev/null || echo "未找到 gldas-env 环境，使用系统 Python"
fi

# 1. 创建必要的目录
echo "步骤 1: 创建必要的目录..."
mkdir -p data/gldas_data
mkdir -p output

# 2. 下载示例数据（此处使用示例链接，实际使用时需要替换为真实链接）
# 注意：此步骤可能需要 NASA Earthdata 账号
echo "步骤 2: 下载示例 GLDAS 数据..."
echo "请输入 NASA Earthdata 用户名（如果没有，请在 https://urs.earthdata.nasa.gov/ 注册）:"
read -p "用户名: " NASA_USERNAME

# 密码处理，不显示输入内容
echo "请输入 NASA Earthdata 密码:"
read -s -p "密码: " NASA_PASSWORD
echo ""

# 创建示例下载链接文件
cat > example_links.txt << EOF
# GLDAS 示例下载链接（仅用于演示）
# 以下链接为示例，可能无效，请替换为实际链接
https://hydro1.gesdisc.eosdis.nasa.gov/data/GLDAS/GLDAS_NOAH025_3H_EP.2.1/2023/001/GLDAS_NOAH025_3H_EP.A20230101.0000.021.nc4
https://hydro1.gesdisc.eosdis.nasa.gov/data/GLDAS/GLDAS_NOAH025_3H_EP.2.1/2023/001/GLDAS_NOAH025_3H_EP.A20230101.0300.021.nc4
https://hydro1.gesdisc.eosdis.nasa.gov/data/GLDAS/GLDAS_NOAH025_3H_EP.2.1/2023/001/GLDAS_NOAH025_3H_EP.A20230101.0600.021.nc4
https://hydro1.gesdisc.eosdis.nasa.gov/data/GLDAS/GLDAS_NOAH025_3H_EP.2.1/2023/001/GLDAS_NOAH025_3H_EP.A20230101.0900.021.nc4
EOF

# 尝试下载数据
python ../scripts/download_gldas.py \
    --username "$NASA_USERNAME" \
    --password "$NASA_PASSWORD" \
    --data-dir data/gldas_data \
    --list-file example_links.txt

# 3. 创建示例研究区域坐标点
echo "步骤 3: 创建示例研究区域坐标点..."
cat > points.txt << EOF
# 格式: 经度,纬度
# 以下是中国杭州湾地区的四个点
120.5,30.5
121.0,30.5
120.5,30.0
121.0,30.0
EOF

# 4. 处理 GLDAS 数据为 SHUD 格式
echo "步骤 4: 处理 GLDAS 数据为 SHUD 格式..."
python ../src/process_gldas_for_shud.py \
    --data-dir data/gldas_data \
    --output-dir output \
    --points "120.5,30.5" "121.0,30.5" "120.5,30.0" "121.0,30.0" \
    --force

# 5. 检查处理结果
echo "步骤 5: 检查处理结果..."
if [ -d "output/csv" ]; then
    echo "已生成 CSV 文件:"
    ls -l output/csv/
else
    echo "警告: 未生成 CSV 文件，请检查处理步骤是否成功"
fi

if [ -f "output/meteo.tsd.forc" ]; then
    echo "已生成 meteo.tsd.forc 文件:"
    cat output/meteo.tsd.forc
else
    echo "警告: 未生成 meteo.tsd.forc 文件，请检查处理步骤是否成功"
fi

# 6. 可视化结果（如果有数据）
echo "步骤 6: 尝试可视化结果..."
if [ -d "output/csv" ] && [ "$(ls -A output/csv)" ]; then
    echo "生成可视化图表..."
    python ../scripts/visualize_gldas.py \
        --csv-dir output/csv \
        --fig-dir output/fig \
        --all
    
    if [ -d "output/fig" ]; then
        echo "已生成图表文件:"
        ls -l output/fig/
    fi
else
    echo "警告: 未找到 CSV 文件或目录为空，跳过可视化步骤"
fi

# 7. 总结
echo "================================================================="
echo "GLDAS2SHUD 工具示例工作流完成"
echo "结束时间: $(date)"
echo "----------------------------------------------------------------"

if [ -d "output/shud_project" ]; then
    echo "SHUD 模型输入文件已准备完成，位于:"
    echo "  $(pwd)/output/shud_project/"
    echo ""
    echo "您可以将此目录复制到 SHUD 模型项目中使用:"
    echo "  cp -r output/shud_project/* /path/to/your/SHUD_project/"
else
    echo "警告: 未生成 SHUD 项目目录，请检查处理步骤是否成功"
fi

echo "================================================================="
echo "示例工作流日志已保存到: $LOG_FILE"
echo "=================================================================" 
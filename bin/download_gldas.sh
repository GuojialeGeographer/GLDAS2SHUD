#!/bin/bash

# NASA GLDAS数据下载脚本 - 快速版
# 用法: ./download_gldas.sh [链接文件]

# 设置链接文件路径
LINKS_FILE=${1:-"data/gldas_data/subset_GLDAS_NOAH025_3H_2.1_20250515_221340_.txt"}
OUTPUT_DIR="data/gldas_data/"

# 确保输出目录存在
mkdir -p $OUTPUT_DIR

# 计数器
TOTAL=0
SUCCESS=0
SILENT_SUCCESS=5  # 前5个成功的下载静默处理

echo "=== NASA GLDAS数据快速下载 ==="
echo "链接文件: $LINKS_FILE"
echo "输出目录: $OUTPUT_DIR"
echo "============================="
echo "正在静默下载前$SILENT_SUCCESS个文件..."

# 设置wget参数 (加入quiet参数减少输出)
WGET_OPTS="--load-cookies ~/.urs_cookies --save-cookies ~/.urs_cookies --keep-session-cookies --no-check-certificate -q"

# 处理每个URL
while IFS= read -r url || [[ -n "$url" ]]; do
    # 跳过空行和注释
    [[ -z "$url" || "$url" == \#* ]] && continue
    
    # 清理URL（移除可能的前导空格）
    url=$(echo "$url" | tr -d '[:space:]')
    
    # 增加计数
    ((TOTAL++))
    
    # 从URL中提取唯一标识符生成文件名
    # 查找日期和时间信息生成文件名 (A20230513.0000)
    if [[ $url =~ A([0-9]{8})\.([0-9]{4}) ]]; then
        date="${BASH_REMATCH[1]}"
        time="${BASH_REMATCH[2]}"
        filename="GLDAS_${date}_${time}.nc4"
    else
        # 如果没找到日期格式，使用计数器作为文件名
        filename="gldas_file_${TOTAL}.nc4"
    fi
    
    output_path="$OUTPUT_DIR/$filename"
    
    # 判断是否需要静默处理
    if [ $SUCCESS -lt $SILENT_SUCCESS ]; then
        # 静默下载前几个文件
        if wget $WGET_OPTS -O "$output_path" "$url"; then
            ((SUCCESS++))
            # 只显示进度，不显示详情
            echo -ne "\r已成功下载: $SUCCESS/$SILENT_SUCCESS"
        else
            # 失败时才显示
            echo -e "\r[!] 下载失败: $filename                 "
            # 删除可能的不完整文件
            [ -f "$output_path" ] && rm "$output_path"
        fi
    else
        # 达到静默阈值后，正常显示
        echo -e "\n[$TOTAL] 下载: $filename"
        if wget $WGET_OPTS -O "$output_path" "$url"; then
            echo "  ✓ 成功: $filename"
            ((SUCCESS++))
        else
            echo "  ✗ 失败: $filename"
            # 删除可能的不完整文件
            [ -f "$output_path" ] && rm "$output_path"
        fi
    fi
    
    # 无需暂停，尽快下载
    
done < "$LINKS_FILE"

echo -e "\n============================="
echo "下载完成: $SUCCESS/$TOTAL 成功"
echo "文件保存在: $OUTPUT_DIR" 
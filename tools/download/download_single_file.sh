#!/bin/bash

# 单文件下载脚本 - 下载特定的GLDAS文件
# 用法: ./download_single_file.sh

# 目标文件
TARGET_DATE="20240117"
TARGET_TIME="2100"
TARGET_FILE="GLDAS_${TARGET_DATE}_${TARGET_TIME}.nc4"
TARGET_PATTERN="A${TARGET_DATE}\.${TARGET_TIME}"

# 设置参数
LINKS_FILE="data/gldas_data/subset_GLDAS_NOAH025_3H_2.1_20250515_221340_.txt"
CLEAN_LINKS="data/gldas_data/clean_links_new.txt"
OUTPUT_DIR="data/gldas_data/downloads"
MAX_RETRIES=5  # 增加重试次数

# 内置NASA Earthdata账号信息
NASA_USERNAME="guojiale.gis"
NASA_PASSWORD="Gjl19990223.+"

# 创建输出目录
mkdir -p $OUTPUT_DIR

echo "=== 下载单个GLDAS文件 ==="
echo "目标文件: $TARGET_FILE"
echo "============================="

# 设置NASA Earthdata认证
NETRC_FILE=~/.netrc
echo "更新NASA Earthdata认证..."
echo "machine urs.earthdata.nasa.gov login $NASA_USERNAME password $NASA_PASSWORD" > $NETRC_FILE
chmod 600 $NETRC_FILE

# 刷新cookie
rm -f ~/.urs_cookies 2>/dev/null

# 查找目标文件的URL
echo "查找文件URL..."

# 如果已有清理好的链接文件，从中查找
if [ -f "$CLEAN_LINKS" ] && [ -s "$CLEAN_LINKS" ]; then
    echo "从清理文件中查找URL..."
    TARGET_URL=$(grep "$TARGET_PATTERN" "$CLEAN_LINKS")
    
    # 如果找不到，重新生成一遍清理文件
    if [ -z "$TARGET_URL" ]; then
        echo "在清理文件中未找到目标URL，从原始文件重新搜索..."
        TARGET_URL=$(grep -A 10 "$TARGET_PATTERN" "$LINKS_FILE" | tr -d '\n' | tr -d '\r' | grep -o "https://.*$TARGET_PATTERN.*nc4" | head -1)
    fi
else
    # 直接从原始链接文件中提取
    echo "从原始链接文件中提取URL..."
    TARGET_URL=$(grep -A 10 "$TARGET_PATTERN" "$LINKS_FILE" | tr -d '\n' | tr -d '\r' | grep -o "https://.*$TARGET_PATTERN.*nc4" | head -1)
fi

# 清理URL，移除末尾的问题字符
if [ -n "$TARGET_URL" ]; then
    TARGET_URL=$(echo "$TARGET_URL" | sed 's/%0D$//')
    echo "找到URL: ${TARGET_URL:0:100}..."
else
    echo "错误: 无法找到目标文件的URL"
    exit 1
fi

# 输出文件路径
OUTPUT_FILE="$OUTPUT_DIR/$TARGET_FILE"

# 如果文件已存在，先删除
if [ -f "$OUTPUT_FILE" ]; then
    echo "移除已存在的文件: $OUTPUT_FILE"
    rm -f "$OUTPUT_FILE"
fi

# 开始下载
echo "开始下载 $TARGET_FILE..."
retry=0
success=0

while [ $retry -lt $MAX_RETRIES ] && [ $success -eq 0 ]; do
    echo "下载尝试: $((retry+1))/$MAX_RETRIES"
    
    # 使用wget下载，显示详细信息
    if wget --load-cookies ~/.urs_cookies --save-cookies ~/.urs_cookies \
        --keep-session-cookies --no-check-certificate \
        -O "$OUTPUT_FILE" "$TARGET_URL" -v; then
        
        # 检查文件是否非空
        if [ -s "$OUTPUT_FILE" ]; then
            filesize=$(du -h "$OUTPUT_FILE" | cut -f1)
            echo "成功: $TARGET_FILE (大小: $filesize)"
            success=1
        else
            echo "警告: 文件为空，重试"
            rm -f "$OUTPUT_FILE"
            ((retry++))
            sleep 5
        fi
    else
        echo "失败: $TARGET_FILE，重试"
        rm -f "$OUTPUT_FILE" 2>/dev/null
        ((retry++))
        sleep 5
    fi
done

# 检查最终结果
if [ $success -eq 1 ]; then
    echo "============================="
    echo "下载成功!"
    echo "文件: $OUTPUT_FILE"
    echo "大小: $(du -h "$OUTPUT_FILE" | cut -f1)"
    echo "============================="
    exit 0
else
    echo "============================="
    echo "下载失败: 经过 $MAX_RETRIES 次尝试后无法下载 $TARGET_FILE"
    echo "============================="
    exit 1
fi 
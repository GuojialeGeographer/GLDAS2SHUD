#!/bin/bash

# 优化的GLDAS数据下载脚本 - 从指定断点继续下载
# 用法: ./continue_download.sh

# 设置参数
LINKS_FILE="data/gldas_data/subset_GLDAS_NOAH025_3H_2.1_20250515_221340_.txt"
OUTPUT_DIR="data/gldas_data/downloads"
START_DATE="20240117_2100"  # 从这个时间点之后开始下载（上一个成功的是20240117_1800）
DOWNLOAD_THREADS=3  # 下载并行数
MAX_RETRIES=3  # 最大重试次数
SLEEP_MIN=2  # 最小暂停时间(秒)
SLEEP_MAX=5  # 最大暂停时间(秒)

# 内置NASA Earthdata账号信息
NASA_USERNAME="guojiale.gis"
NASA_PASSWORD="Gjl19990223.+"

# 创建输出目录
mkdir -p $OUTPUT_DIR

echo "=== 优化的GLDAS数据下载脚本 ==="
echo "从断点($START_DATE)继续下载"
echo "并行下载线程: $DOWNLOAD_THREADS"
echo "输出目录: $OUTPUT_DIR"
echo "============================="

# 设置NASA Earthdata认证
NETRC_FILE=~/.netrc
echo "更新NASA Earthdata认证..."
echo "machine urs.earthdata.nasa.gov login $NASA_USERNAME password $NASA_PASSWORD" > $NETRC_FILE
chmod 600 $NETRC_FILE

# 刷新cookie
rm -f ~/.urs_cookies 2>/dev/null

# 如果指定了代理服务器，则配置wget使用代理
# export http_proxy=http://your.proxy.server:port
# export https_proxy=http://your.proxy.server:port

# 先生成一个新的文件来存储清理过的链接
CLEAN_LINKS="data/gldas_data/clean_links_new.txt"
echo "正在清理链接文件，提取完整URL..."

# 检查是否已有清理好的链接文件
if [ -f "$CLEAN_LINKS" ] && [ -s "$CLEAN_LINKS" ]; then
    echo "使用已有的清理文件: $CLEAN_LINKS"
else
    echo "重新生成清理的链接文件..."
    # 清理链接文件，正确处理每个URL
    current_url=""
    line_num=0
    while IFS= read -r line || [[ -n "$line" ]]; do
        ((line_num++))
        
        # 跳过空行和注释
        [[ -z "$line" || "$line" == \#* ]] && continue
        
        # 去除行首尾空格
        line=$(echo "$line" | xargs)
        
        # 如果行以https://开头，则开始一个新URL
        if [[ "$line" == https://* ]]; then
            # 如果已有URL，先保存
            if [[ -n "$current_url" ]]; then
                # 移除末尾可能的CR字符
                current_url=$(echo "$current_url" | tr -d '\r')
                # 移除末尾可能的%0D (URL编码的CR)
                current_url=$(echo "$current_url" | sed 's/%0D$//')
                echo "$current_url" >> $CLEAN_LINKS
            fi
            current_url="$line"
        else
            # 否则，追加到当前URL (确保没有额外空格)
            current_url="${current_url}$(echo "$line" | tr -d ' ')"
        fi
        
        # 每1000行显示进度
        if (( line_num % 1000 == 0 )); then
            echo "已处理 $line_num 行..."
        fi
    done < "$LINKS_FILE"

    # 保存最后一个URL
    if [[ -n "$current_url" ]]; then
        current_url=$(echo "$current_url" | tr -d '\r')
        current_url=$(echo "$current_url" | sed 's/%0D$//')
        echo "$current_url" >> $CLEAN_LINKS
    fi

    echo "链接文件清理完成"
fi

# 计算URL总数
total_urls=$(wc -l < $CLEAN_LINKS)
echo "共找到 $total_urls 个URL"

# 创建一个临时文件存储待下载的URL
DOWNLOAD_QUEUE=$(mktemp)

# 查找开始日期之后的URL
echo "查找从 $START_DATE 之后的URL..."
found_start=0
line_num=0
remaining=0

while IFS= read -r url; do
    ((line_num++))
    
    # 提取日期和时间信息
    if [[ $url =~ A([0-9]{8})\.([0-9]{4}) ]]; then
        date="${BASH_REMATCH[1]}"
        time="${BASH_REMATCH[2]}"
        datetime="${date}_${time}"
        
        # 只添加开始日期之后的URL
        if [[ "$found_start" -eq 0 ]]; then
            if [[ "$datetime" < "$START_DATE" || "$datetime" == "$START_DATE" ]]; then
                # 仍在开始日期之前，跳过
                continue
            else
                # 找到开始日期之后的第一个URL
                found_start=1
                echo "找到开始点: $datetime，开始添加到下载队列"
            fi
        fi
        
        # 构建输出文件名
        filename="GLDAS_${date}_${time}.nc4"
        output_path="$OUTPUT_DIR/$filename"
        
        # 检查文件是否已存在且非空
        if [ -f "$output_path" ] && [ -s "$output_path" ]; then
            # 文件已存在，跳过
            continue
        fi
        
        # 添加到下载队列
        echo -e "$url\t$filename" >> $DOWNLOAD_QUEUE
        ((remaining++))
    fi
    
    # 每1000个URL显示一次进度
    if (( line_num % 1000 == 0 )); then
        echo "已处理 $line_num/$total_urls URLs..."
    fi
    
done < $CLEAN_LINKS

echo "需要下载的文件: $remaining 个"

if [ "$remaining" -eq 0 ]; then
    echo "没有需要下载的文件，任务已完成"
    rm -f $DOWNLOAD_QUEUE
    exit 0
fi

# 下载函数
download_file() {
    local url="$1"
    local filename="$2"
    local output_path="$OUTPUT_DIR/$filename"
    local retry=0
    local success=0
    
    # 检查文件是否已存在且非空
    if [ -f "$output_path" ] && [ -s "$output_path" ]; then
        echo "[$filename] 已存在，跳过"
        return 0
    fi
    
    while [ $retry -lt $MAX_RETRIES ] && [ $success -eq 0 ]; do
        echo "下载: $filename (尝试 $((retry+1))/$MAX_RETRIES)"
        
        # 使用wget下载
        if wget --load-cookies ~/.urs_cookies --save-cookies ~/.urs_cookies \
            --keep-session-cookies --no-check-certificate -q \
            -O "$output_path" "$url"; then
            
            # 检查文件是否非空
            if [ -s "$output_path" ]; then
                filesize=$(du -h "$output_path" | cut -f1)
                echo "成功: $filename (大小: $filesize)"
                success=1
            else
                echo "警告: $filename 文件为空，重试"
                rm -f "$output_path"
                ((retry++))
            fi
        else
            echo "失败: $filename，重试"
            rm -f "$output_path" 2>/dev/null
            ((retry++))
            
            # 暂停一会儿再重试
            sleep_time=$((RANDOM % (SLEEP_MAX - SLEEP_MIN + 1) + SLEEP_MIN))
            echo "等待 $sleep_time 秒后重试..."
            sleep $sleep_time
        fi
    done
    
    # 检查最终结果
    if [ $success -eq 1 ]; then
        return 0
    else
        echo "放弃: $filename 经过 $MAX_RETRIES 次尝试后仍然失败"
        return 1
    fi
}

# 导出下载函数让xargs使用
export -f download_file
export OUTPUT_DIR
export MAX_RETRIES
export SLEEP_MIN
export SLEEP_MAX

# 开始多线程下载
echo "开始下载，并行线程: $DOWNLOAD_THREADS"
cat $DOWNLOAD_QUEUE | parallel -j $DOWNLOAD_THREADS --colsep '\t' download_file {1} {2} || {
    # 如果parallel命令不存在，使用单线程下载
    echo "parallel命令不可用，使用单线程下载"
    success_count=0
    fail_count=0
    
    while IFS=$'\t' read -r url filename; do
        if download_file "$url" "$filename"; then
            ((success_count++))
        else
            ((fail_count++))
        fi
        
        # 显示进度
        echo "进度: $((success_count + fail_count))/$remaining (成功: $success_count, 失败: $fail_count)"
        
        # 随机暂停以避免请求过于频繁
        sleep_time=$((RANDOM % (SLEEP_MAX - SLEEP_MIN + 1) + SLEEP_MIN))
        echo "暂停 $sleep_time 秒..."
        sleep $sleep_time
    done < $DOWNLOAD_QUEUE
}

# 统计下载结果
total_files=$(ls -1 "$OUTPUT_DIR"/*.nc4 2>/dev/null | wc -l)
echo "============================="
echo "下载完成"
echo "下载目录: $OUTPUT_DIR"
echo "总计下载文件数: $total_files"
echo "============================="

# 清理临时文件
rm -f $DOWNLOAD_QUEUE 
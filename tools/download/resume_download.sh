#!/bin/bash

# 设置参数
LINKS_FILE="data/gldas_data/subset_GLDAS_NOAH025_3H_2.1_20250515_221340_.txt"
OUTPUT_DIR="data/gldas_data/downloads"
START_DATE="20240216_2100"  # 从这个日期开始恢复下载

# 创建输出目录
mkdir -p $OUTPUT_DIR

echo "=== 恢复下载 GLDAS 数据 ==="
echo "从日期 $START_DATE 开始恢复下载"
echo "链接文件: $LINKS_FILE"
echo "输出目录: $OUTPUT_DIR"
echo "============================="

# 预处理链接文件，修复多行URL问题
CLEAN_LINKS="data/gldas_data/clean_links.txt"
echo "正在预处理链接文件..."

# 确保没有旧的清理文件
rm -f $CLEAN_LINKS

# 读取输入文件并合并分行的URL
current_url=""
total_urls=0

while IFS= read -r line || [[ -n "$line" ]]; do
    # 跳过空行和注释
    [[ -z "$line" || "$line" == \#* ]] && continue
    
    # 如果行以https://开头，则是新URL的开始
    if [[ "$line" == https://* ]]; then
        # 如果有之前的URL，则先保存
        if [[ -n "$current_url" ]]; then
            echo "$current_url" >> $CLEAN_LINKS
            ((total_urls++))
        fi
        # 开始新URL
        current_url="$line"
    else
        # 否则，追加到当前URL
        current_url="${current_url}${line}"
    fi
done < "$LINKS_FILE"

# 保存最后一个URL
if [[ -n "$current_url" ]]; then
    echo "$current_url" >> $CLEAN_LINKS
    ((total_urls++))
fi

echo "共找到 $total_urls 个URL"

# 开始下载
echo "开始下载..."
success_count=0
fail_count=0
skipped_count=0

# 设置wget选项
WGET_OPTS="--load-cookies ~/.urs_cookies --save-cookies ~/.urs_cookies --keep-session-cookies --no-check-certificate -q"

# 刷新NASA Earthdata认证
echo "正在刷新NASA Earthdata认证..."
COOKIES_FILE=~/.urs_cookies
if [ -f "$COOKIES_FILE" ]; then
    rm -f "$COOKIES_FILE"
fi

# 读取清理后的URL进行下载
counter=0
found_start=0

while IFS= read -r url; do
    ((counter++))
    
    # 从URL中提取文件标识
    if [[ $url =~ A([0-9]{8})\.([0-9]{4}) ]]; then
        date="${BASH_REMATCH[1]}"
        time="${BASH_REMATCH[2]}"
        filename="GLDAS_${date}_${time}.nc4"
        
        # 检查是否达到了起始日期
        date_time="${date}_${time}"
        if [[ "$found_start" -eq 0 && "$date_time" < "$START_DATE" ]]; then
            if (( counter % 1000 == 0 )); then
                echo -ne "[$counter/$total_urls] 跳过已下载文件...\r"
            fi
            ((skipped_count++))
            continue
        fi
        
        found_start=1
    else
        # 如果没找到日期格式，跳过此项
        if [[ "$found_start" -eq 1 ]]; then
            echo "[$counter/$total_urls] 无法解析日期: $url"
        fi
        continue
    fi
    
    output_path="${OUTPUT_DIR}/${filename}"
    
    # 检查文件是否已存在
    if [ -f "$output_path" ]; then
        echo "[$counter/$total_urls] 已存在: $filename"
        ((success_count++))
        continue
    fi
    
    # 显示进度
    echo "[$counter/$total_urls] 下载: $filename"
    
    # 执行下载
    if wget $WGET_OPTS -O "$output_path" "$url"; then
        echo "[$counter/$total_urls] 成功: $filename"
        ((success_count++))
    else
        echo "[$counter/$total_urls] 失败: $filename - 重试"
        # 重试一次
        if wget $WGET_OPTS -O "$output_path" "$url"; then
            echo "[$counter/$total_urls] 重试成功: $filename"
            ((success_count++))
        else
            echo "[$counter/$total_urls] 彻底失败: $filename"
            rm -f "$output_path"
            ((fail_count++))
            
            # 连续失败超过10个文件，可能服务器有问题，暂停久一点
            if (( fail_count % 10 == 0 )); then
                echo "连续多次失败，等待30秒..."
                sleep 30
            fi
        fi
    fi
    
    # 防止触发服务器限制，每下载几个文件暂停一下
    if (( (success_count + fail_count) % 5 == 0 )); then
        sleep_time=$((RANDOM % 5 + 3))  # 随机暂停3-8秒
        echo "暂停 $sleep_time 秒，避免触发下载限制..."
        sleep $sleep_time
    fi
    
done < "$CLEAN_LINKS"

# 清理临时文件
rm -f $CLEAN_LINKS

echo "============================="
echo "下载统计:"
echo "  跳过: $skipped_count"
echo "  成功: $success_count"
echo "  失败: $fail_count"
echo "总文件数: $total_urls"
echo "文件保存在: $OUTPUT_DIR" 
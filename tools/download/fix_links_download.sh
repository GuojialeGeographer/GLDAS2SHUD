#!/bin/bash

# 更精确的链接修复和下载测试脚本

# 设置参数
LINKS_FILE="data/gldas_data/subset_GLDAS_NOAH025_3H_2.1_20250515_221340_.txt"
OUTPUT_DIR="data/gldas_data/downloads"
TEST_DATE="20240118"  # 要测试的日期

# 创建输出目录
mkdir -p $OUTPUT_DIR

echo "=== 修复链接并测试下载 ==="
echo "链接文件: $LINKS_FILE"
echo "测试日期: $TEST_DATE"
echo "==========================="

# 先生成一个新的临时文件来存储清理过的链接
TEMP_LINKS=$(mktemp)
echo "正在清理链接文件，提取完整URL..."

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
            echo "$current_url" >> $TEMP_LINKS
        fi
        current_url="$line"
    else
        # 否则，追加到当前URL
        current_url="${current_url}${line}"
    fi
done < "$LINKS_FILE"

# 保存最后一个URL
if [[ -n "$current_url" ]]; then
    current_url=$(echo "$current_url" | tr -d '\r')
    echo "$current_url" >> $TEMP_LINKS
fi

# 计算URL总数
total_urls=$(wc -l < $TEMP_LINKS)
echo "共找到 $total_urls 个URL"

# 提取测试日期的URL
echo "提取日期 $TEST_DATE 的URL..."
TEST_LINKS=$(mktemp)
grep "$TEST_DATE" $TEMP_LINKS > $TEST_LINKS

# 显示找到的测试URL数
test_count=$(wc -l < $TEST_LINKS)
echo "找到 $test_count 个测试URL"

if [ "$test_count" -eq 0 ]; then
    echo "未找到测试日期 $TEST_DATE 的URL，请检查日期是否正确"
    rm -f $TEMP_LINKS $TEST_LINKS
    exit 1
fi

# 提示用户输入NASA Earthdata账号信息
read -p "请输入NASA Earthdata用户名: " username
read -s -p "请输入NASA Earthdata密码: " password
echo ""

# 创建或更新.netrc文件
NETRC_FILE=~/.netrc
echo "machine urs.earthdata.nasa.gov login $username password $password" > $NETRC_FILE
chmod 600 $NETRC_FILE

echo "认证信息已更新"

# 显示测试链接（最多5个）
echo "要测试的链接："
head -n 5 $TEST_LINKS | cat -n

# 测试下载第一个链接
echo "正在下载第一个测试链接..."
test_url=$(head -n 1 $TEST_LINKS)
echo "URL (前100个字符): ${test_url:0:100}..."

# 从URL中提取文件名
if [[ $test_url =~ A([0-9]{8})\.([0-9]{4}) ]]; then
    date="${BASH_REMATCH[1]}"
    time="${BASH_REMATCH[2]}"
    filename="GLDAS_${date}_${time}.nc4"
else
    echo "无法从URL中提取文件名，使用默认名称"
    filename="test_download.nc4"
fi

output_file="$OUTPUT_DIR/$filename"

# 执行下载
wget --load-cookies ~/.urs_cookies --save-cookies ~/.urs_cookies \
     --keep-session-cookies --no-check-certificate \
     -O "$output_file" "$test_url" -v

# 检查结果
if [ -f "$output_file" ]; then
    filesize=$(du -h "$output_file" | cut -f1)
    echo "下载成功！文件: $filename，大小: $filesize"
    
    # 如果文件大小为0，可能下载失败
    if [ ! -s "$output_file" ]; then
        echo "警告：文件大小为0，下载可能失败"
    fi
else
    echo "下载失败"
fi

# 清理临时文件
rm -f $TEMP_LINKS $TEST_LINKS

echo "测试完成" 
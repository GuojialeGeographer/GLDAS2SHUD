#!/bin/bash

# 检查GLDAS数据完整性和重复性的脚本
# 用法: ./check_data_integrity.sh

DATA_DIR="data/gldas_data/downloads"
OUTPUT_LOG="data_integrity_check.log"

echo "=== GLDAS数据完整性检查 ===" | tee $OUTPUT_LOG
echo "数据目录: $DATA_DIR" | tee -a $OUTPUT_LOG
echo "===========================" | tee -a $OUTPUT_LOG

# 确保目录存在
if [ ! -d "$DATA_DIR" ]; then
    echo "错误: 数据目录不存在: $DATA_DIR" | tee -a $OUTPUT_LOG
    exit 1
fi

# 获取所有下载的文件 (仅.nc4文件)
ALL_FILES=$(find $DATA_DIR -name "GLDAS_*.nc4" -type f | sort)
FILE_COUNT=$(echo "$ALL_FILES" | wc -l)

echo "检测到 $FILE_COUNT 个GLDAS数据文件" | tee -a $OUTPUT_LOG

# 提取所有日期和时间点
echo "正在提取日期和时间点信息..." | tee -a $OUTPUT_LOG
DATE_TIMES=$(find $DATA_DIR -name "GLDAS_*.nc4" -type f | grep -o "GLDAS_[0-9]\{8\}_[0-9]\{4\}" | sed 's/GLDAS_//' | sort)

# 检查连续性
echo "检查数据连续性..." | tee -a $OUTPUT_LOG

# 提取开始和结束日期
FIRST_DATE=$(echo "$DATE_TIMES" | head -1)
LAST_DATE=$(echo "$DATE_TIMES" | tail -1)

echo "数据起始时间点: $FIRST_DATE" | tee -a $OUTPUT_LOG
echo "数据结束时间点: $LAST_DATE" | tee -a $OUTPUT_LOG

# 提取所有日期到一个临时文件
TEMP_DATES=$(mktemp)
echo "$DATE_TIMES" > $TEMP_DATES

# 统计文件大小异常的文件
echo "检查文件大小异常的文件..." | tee -a $OUTPUT_LOG
AVERAGE_SIZE=$(du -k $DATA_DIR/GLDAS_*.nc4 | awk '{sum+=$1} END {print int(sum/NR)}')
echo "平均文件大小: ${AVERAGE_SIZE}KB" | tee -a $OUTPUT_LOG

SIZE_THRESHOLD=$((AVERAGE_SIZE / 2))
SMALL_FILES=$(find $DATA_DIR -name "GLDAS_*.nc4" -size -${SIZE_THRESHOLD}k | wc -l)

if [ $SMALL_FILES -gt 0 ]; then
    echo "警告: 发现 $SMALL_FILES 个文件大小低于平均值的一半(${SIZE_THRESHOLD}KB)" | tee -a $OUTPUT_LOG
    find $DATA_DIR -name "GLDAS_*.nc4" -size -${SIZE_THRESHOLD}k | tee -a $OUTPUT_LOG
else
    echo "文件大小检查通过: 未发现异常小文件" | tee -a $OUTPUT_LOG
fi

# 检查时间间隔一致性
echo "检查时间间隔一致性..." | tee -a $OUTPUT_LOG

# 提取所有唯一的时间点
TIME_POINTS=$(echo "$DATE_TIMES" | cut -d'_' -f2 | sort -u)
TIME_POINT_COUNT=$(echo "$TIME_POINTS" | wc -l)

echo "发现 $TIME_POINT_COUNT 个唯一时间点: $TIME_POINTS" | tee -a $OUTPUT_LOG

# 假设是3小时间隔
if [ $TIME_POINT_COUNT -eq 8 ]; then
    echo "时间间隔检查通过: 发现标准的8个时间点(0000, 0300, 0600, 0900, 1200, 1500, 1800, 2100)" | tee -a $OUTPUT_LOG
else
    echo "警告: 时间点数量不是预期的8个" | tee -a $OUTPUT_LOG
fi

# 检查是否有重复文件
echo "检查文件重复性..." | tee -a $OUTPUT_LOG
DUPLICATE_COUNT=$(echo "$DATE_TIMES" | sort | uniq -d | wc -l)

if [ $DUPLICATE_COUNT -gt 0 ]; then
    echo "警告: 发现 $DUPLICATE_COUNT 个重复的日期时间点:" | tee -a $OUTPUT_LOG
    echo "$DATE_TIMES" | sort | uniq -c | grep -v '^ *1 ' | tee -a $OUTPUT_LOG
else
    echo "重复性检查通过: 未发现重复的日期时间点" | tee -a $OUTPUT_LOG
fi

# 高级检查: 检查是否有缺失的时间点
# 为简单起见，我们只检查几个关键日期前后的连续性
echo "检查关键日期的数据连续性..." | tee -a $OUTPUT_LOG

# 检查2024年1月17日前后的数据
CHECK_DATE="20240117"
echo "检查日期 $CHECK_DATE 的所有时间点..." | tee -a $OUTPUT_LOG

for TIME in "0000" "0300" "0600" "0900" "1200" "1500" "1800" "2100"; do
    FILE_CHECK="${DATA_DIR}/GLDAS_${CHECK_DATE}_${TIME}.nc4"
    if [ -f "$FILE_CHECK" ]; then
        FILE_SIZE=$(du -h "$FILE_CHECK" | cut -f1)
        echo "✓ ${CHECK_DATE}_${TIME} 存在 (大小: $FILE_SIZE)" | tee -a $OUTPUT_LOG
    else
        echo "✗ ${CHECK_DATE}_${TIME} 缺失!" | tee -a $OUTPUT_LOG
    fi
done

# 检查2024年1月18日前后的数据
CHECK_DATE="20240118"
echo "检查日期 $CHECK_DATE 的所有时间点..." | tee -a $OUTPUT_LOG

for TIME in "0000" "0300" "0600" "0900" "1200" "1500" "1800" "2100"; do
    FILE_CHECK="${DATA_DIR}/GLDAS_${CHECK_DATE}_${TIME}.nc4"
    if [ -f "$FILE_CHECK" ]; then
        FILE_SIZE=$(du -h "$FILE_CHECK" | cut -f1)
        echo "✓ ${CHECK_DATE}_${TIME} 存在 (大小: $FILE_SIZE)" | tee -a $OUTPUT_LOG
    else
        echo "✗ ${CHECK_DATE}_${TIME} 缺失!" | tee -a $OUTPUT_LOG
    fi
done

# 清理临时文件
rm -f $TEMP_DATES

echo "===========================" | tee -a $OUTPUT_LOG
echo "数据完整性检查完成，结果保存至: $OUTPUT_LOG" | tee -a $OUTPUT_LOG 
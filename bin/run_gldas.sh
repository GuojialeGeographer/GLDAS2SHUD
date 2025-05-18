#!/bin/bash

# 设置颜色
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # 无色

# 检查conda环境
if [ -z "$CONDA_DEFAULT_ENV" ] || [ "$CONDA_DEFAULT_ENV" != "gldas-env" ]; then
    echo -e "${YELLOW}警告: 您当前不在 gldas-env conda环境中.${NC}"
    echo -e "推荐使用以下命令激活环境:"
    echo -e "${BLUE}conda activate gldas-env${NC}"
    echo ""
    read -p "是否继续执行? [y/N] " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 主菜单函数
show_main_menu() {
    clear
    echo -e "${GREEN}=== GLDAS数据处理工具 ===${NC}"
    echo -e "${BLUE}1. 下载GLDAS数据${NC}"
    echo -e "${BLUE}2. 按点位提取GLDAS数据${NC}"
    echo -e "${BLUE}3. 可视化处理后的数据${NC}"
    echo -e "${BLUE}4. 退出${NC}"
    echo ""
    read -p "请选择操作 [1-4]: " choice
}

# 下载菜单
download_menu() {
    clear
    echo -e "${GREEN}=== 下载GLDAS数据 ===${NC}"
    echo "此功能将下载NASA GLDAS气象数据"
    echo "您需要提供NASA Earthdata账号才能下载数据"
    echo ""
    
    read -p "请输入NASA Earthdata用户名: " username
    read -p "请输入NASA Earthdata密码: " -s password
    echo ""
    
    read -p "请输入起始日期 (格式: YYYYMMDD): " start_date
    read -p "请输入结束日期 (格式: YYYYMMDD): " end_date
    
    echo ""
    echo -e "${YELLOW}正在下载数据，请稍候...${NC}"
    python src/download_gldas.py --username "$username" --password "$password" --start-date "$start_date" --end-date "$end_date"
    
    echo ""
    read -p "按回车键返回主菜单..."
}

# 处理菜单
process_menu() {
    clear
    echo -e "${GREEN}=== 按点位提取GLDAS数据 ===${NC}"
    echo "此功能将从GLDAS数据中提取指定点位的气象数据"
    echo "需要提供包含点位置的shapefile文件"
    echo ""
    
    read -p "请输入shapefile文件路径: " shp_file
    read -p "是否强制重新处理已存在的文件? [y/N] " -n 1 -r
    echo ""
    
    force_option=""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        force_option="--force"
    fi
    
    echo -e "${YELLOW}正在处理数据，请稍候...${NC}"
    python src/extract_points.py --shp-file "$shp_file" $force_option
    
    echo ""
    read -p "按回车键返回主菜单..."
}

# 可视化菜单
visualize_menu() {
    clear
    echo -e "${GREEN}=== 可视化处理后的数据 ===${NC}"
    echo "此功能将可视化处理后的点位气象数据"
    echo ""
    
    read -p "请输入要可视化的点ID: " point_id
    
    echo "可视化变量选项:"
    echo "1. 降水量 (precip)"
    echo "2. 温度 (temp)"
    echo "3. 相对湿度 (rh)"
    echo "4. 风速 (wind)"
    echo "5. 辐射 (radiation)"
    echo "6. 气压 (pressure)"
    echo "7. 所有变量 (all)"
    
    read -p "请选择要可视化的变量 [1-7]: " var_choice
    
    case $var_choice in
        1) variable="precip" ;;
        2) variable="temp" ;;
        3) variable="rh" ;;
        4) variable="wind" ;;
        5) variable="radiation" ;;
        6) variable="pressure" ;;
        7) variable="all" ;;
        *) echo "无效的选择"; return ;;
    esac
    
    echo -e "${YELLOW}正在生成图表，请稍候...${NC}"
    python src/visualize_gldas.py --point "$point_id" --variable "$variable"
    
    echo ""
    read -p "按回车键返回主菜单..."
}

# 主循环
while true; do
    show_main_menu
    
    case $choice in
        1) download_menu ;;
        2) process_menu ;;
        3) visualize_menu ;;
        4) echo "退出程序"; exit 0 ;;
        *) echo "无效的选择，请重试" ;;
    esac
done 
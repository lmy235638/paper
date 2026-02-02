#!/usr/bin/env python3
"""
修正工位转运时间MD文件格式并计算转运时间（分钟）
功能：
1. 修正表格中数值的对齐格式
2. 根据移动时间（秒）计算转运时间（分钟）
3. 确保表格格式统一
"""

import re
import os

def update_transport_time_md(md_file_path: str) -> None:
    """
    更新MD文件中的转运时间和格式
    :param md_file_path: MD文件路径
    """
    with open(md_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 更新表格表头，添加最小转运时间列
    header_pattern = re.compile(r'\| 起始工位 \| 目标工位 \| 曼哈顿距离 \(格\) \| 移动时间 \(秒\) \| 转运时间 \(分钟\) \|')
    content = header_pattern.sub(r'| 起始工位 | 目标工位 | 曼哈顿距离 (格) | 移动时间 (秒) | 转运时间 (分钟) | 最小转运时间 (分钟) |', content)
    
    # 更新分隔线，添加最小转运时间列的分隔
    separator_pattern = re.compile(r'\|[-]+(\|[-]+){4}\|')
    content = separator_pattern.sub(r'|---------|---------|----------------|--------------|----------------|----------------|', content)
    
    # 定义正则表达式匹配表格行
    table_row_pattern = re.compile(r'\|\s*(\w+)\s*\|\s*(\w+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(.*?)\s*\|')
    
    def format_table_row(match: re.Match) -> str:
        """
        格式化表格行，计算转运时间和最小转运时间
        :param match: 匹配对象
        :return: 格式化后的表格行
        """
        start_station = match.group(1)
        target_station = match.group(2)
        manhattan = match.group(3)
        seconds = match.group(4)
        
        # 计算转运时间（分钟）= 秒数 / 60，保留1位小数
        transport_time = round(int(seconds) / 60, 1)
        
        # 计算最小转运时间（分钟）= 转运时间 * 2，保留1位小数
        min_transport_time = round(transport_time * 2, 1)
        
        # 格式化行，确保对齐
        return f"| {start_station} | {target_station} | {manhattan} | {seconds} | {transport_time} | {min_transport_time} |"
    
    # 更新所有表格行
    updated_content = table_row_pattern.sub(format_table_row, content)
    
    # 确保文件末尾有换行
    if not updated_content.endswith('\n'):
        updated_content += '\n'
    
    # 写回文件
    with open(md_file_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print(f"✅ 已更新文件：{md_file_path}")
    print(f"   - 修正了表格格式")
    print(f"   - 计算了转运时间（分钟）")


def main():
    """
    主函数
    """
    # 项目根目录
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    md_file_path = os.path.join(project_root, 'results', '工位转运时间.md')
    
    if os.path.exists(md_file_path):
        update_transport_time_md(md_file_path)
    else:
        print(f"❌ 文件不存在：{md_file_path}")


if __name__ == "__main__":
    main()
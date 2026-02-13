import json
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, Any, List

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题


def load_analysis_report(filename: str) -> Dict[str, Any]:
    """加载分析报告
    
    Args:
        filename: 分析报告文件名
        
    Returns:
        dict: 分析报告数据
    """
    with open(filename, 'r', encoding='utf-8') as f:
        report = json.load(f)
    return report


def plot_processing_time_errors(report: Dict[str, Any], output_dir='results'):
    """绘制加工时间误差图表
    
    Args:
        report: 分析报告数据
        output_dir: 输出目录
    """
    # 提取加工时间误差数据
    processing_analyses = report.get('processing_time_analysis', [])
    
    if not processing_analyses:
        print("没有加工时间误差数据")
        return
    
    # 准备数据
    pono_list = []
    total_errors = []
    average_errors = []
    
    for analysis in processing_analyses:
        pono = analysis.get('pono', 'Unknown')
        pono_list.append(str(pono))
        total_errors.append(analysis.get('total_error', 0))
        average_errors.append(analysis.get('average_error', 0))
    
    # 创建图表
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    fig.suptitle('加工时间误差分析', fontsize=16)
    
    # 总误差柱状图
    ax1.bar(pono_list, total_errors, color='skyblue')
    ax1.set_title('总加工时间误差 (分钟)')
    ax1.set_xlabel('任务 PONO')
    ax1.set_ylabel('总误差 (分钟)')
    ax1.grid(axis='y', alpha=0.7)
    
    # 平均误差柱状图
    ax2.bar(pono_list, average_errors, color='lightgreen')
    ax2.set_title('平均加工时间误差 (分钟)')
    ax2.set_xlabel('任务 PONO')
    ax2.set_ylabel('平均误差 (分钟)')
    ax2.grid(axis='y', alpha=0.7)
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(f'{output_dir}/processing_time_errors.png')
    plt.show()


def plot_arrival_time_errors(report: Dict[str, Any], output_dir='results'):
    """绘制到达时间误差图表
    
    Args:
        report: 分析报告数据
        output_dir: 输出目录
    """
    # 提取到达时间误差数据
    arrival_analyses = report.get('arrival_time_analysis', [])
    
    if not arrival_analyses:
        print("没有到达时间误差数据")
        return
    
    # 准备数据
    pono_list = []
    total_errors = []
    average_errors = []
    late_arrivals = []
    
    for analysis in arrival_analyses:
        pono = analysis.get('pono', 'Unknown')
        pono_list.append(str(pono))
        total_errors.append(analysis.get('total_error', 0))
        average_errors.append(analysis.get('average_error', 0))
        late_arrivals.append(analysis.get('late_arrivals', 0))
    
    # 创建图表
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 12))
    fig.suptitle('到达时间误差分析', fontsize=16)
    
    # 总误差柱状图
    ax1.bar(pono_list, total_errors, color='salmon')
    ax1.set_title('总到达时间误差 (分钟)')
    ax1.set_xlabel('任务 PONO')
    ax1.set_ylabel('总误差 (分钟)')
    ax1.grid(axis='y', alpha=0.7)
    
    # 平均误差柱状图
    ax2.bar(pono_list, average_errors, color='orange')
    ax2.set_title('平均到达时间误差 (分钟)')
    ax2.set_xlabel('任务 PONO')
    ax2.set_ylabel('平均误差 (分钟)')
    ax2.grid(axis='y', alpha=0.7)
    
    # 迟到次数柱状图
    ax3.bar(pono_list, late_arrivals, color='red')
    ax3.set_title('迟到次数')
    ax3.set_xlabel('任务 PONO')
    ax3.set_ylabel('迟到次数')
    ax3.grid(axis='y', alpha=0.7)
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(f'{output_dir}/arrival_time_errors.png')
    plt.show()


def plot_summary_statistics(report: Dict[str, Any], output_dir='results'):
    """绘制摘要统计图表
    
    Args:
        report: 分析报告数据
        output_dir: 输出目录
    """
    # 提取摘要数据
    summary = report.get('summary', {})
    
    if not summary:
        print("没有摘要统计数据")
        return
    
    # 准备数据
    labels = ['加工时间误差', '到达时间误差']
    values = [
        summary.get('average_processing_time_error', 0),
        summary.get('average_arrival_time_error', 0)
    ]
    
    late_arrival_rate = summary.get('late_arrival_rate', 0)
    
    # 创建图表
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
    fig.suptitle('仿真结果摘要', fontsize=16)
    
    # 平均误差对比柱状图
    ax1.bar(labels, values, color=['blue', 'green'])
    ax1.set_title('平均时间误差 (分钟)')
    ax1.set_ylabel('平均误差 (分钟)')
    ax1.grid(axis='y', alpha=0.7)
    
    # 迟到率饼图
    ax2.pie([late_arrival_rate, 1 - late_arrival_rate], labels=['迟到', '准时'], 
            autopct='%1.1f%%', startangle=90, colors=['red', 'green'])
    ax2.set_title('迟到率')
    ax2.axis('equal')
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(f'{output_dir}/summary_statistics.png')
    plt.show()


def plot_station_level_analysis(report: Dict[str, Any], output_dir='results'):
    """绘制工位级别的误差分析图表
    
    Args:
        report: 分析报告数据
        output_dir: 输出目录
    """
    # 提取工位级别数据
    processing_analyses = report.get('processing_time_analysis', [])
    arrival_analyses = report.get('arrival_time_analysis', [])
    
    if not processing_analyses and not arrival_analyses:
        print("没有工位级别误差数据")
        return
    
    # 统计工位级别误差
    station_processing_errors = {}
    station_arrival_errors = {}
    
    # 处理加工时间误差
    for analysis in processing_analyses:
        processing_errors = analysis.get('processing_time_errors', {})
        for station_id, error_info in processing_errors.items():
            if station_id not in station_processing_errors:
                station_processing_errors[station_id] = []
            station_processing_errors[station_id].append(error_info.get('error', 0))
    
    # 处理到达时间误差
    for analysis in arrival_analyses:
        arrival_errors = analysis.get('arrival_time_errors', {})
        for station_id, error_info in arrival_errors.items():
            if station_id not in station_arrival_errors:
                station_arrival_errors[station_id] = []
            station_arrival_errors[station_id].append(error_info.get('error', 0))
    
    # 创建加工时间误差图表
    if station_processing_errors:
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # 计算每个工位的平均误差
        station_names = list(station_processing_errors.keys())
        avg_errors = [np.mean(errors) for errors in station_processing_errors.values()]
        std_errors = [np.std(errors) for errors in station_processing_errors.values()]
        
        # 绘制柱状图
        bars = ax.bar(station_names, avg_errors, yerr=std_errors, capsize=5, color='skyblue')
        ax.set_title('工位加工时间平均误差 (分钟)')
        ax.set_xlabel('工位')
        ax.set_ylabel('平均误差 (分钟)')
        ax.grid(axis='y', alpha=0.7)
        
        # 添加数值标签
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height, f'{height:.2f}',
                    ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig(f'{output_dir}/station_processing_errors.png')
        plt.show()
    
    # 创建到达时间误差图表
    if station_arrival_errors:
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # 计算每个工位的平均误差
        station_names = list(station_arrival_errors.keys())
        avg_errors = [np.mean(errors) for errors in station_arrival_errors.values()]
        std_errors = [np.std(errors) for errors in station_arrival_errors.values()]
        
        # 绘制柱状图
        bars = ax.bar(station_names, avg_errors, yerr=std_errors, capsize=5, color='salmon')
        ax.set_title('工位到达时间平均误差 (分钟)')
        ax.set_xlabel('工位')
        ax.set_ylabel('平均误差 (分钟)')
        ax.grid(axis='y', alpha=0.7)
        
        # 添加数值标签
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height, f'{height:.2f}',
                    ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig(f'{output_dir}/station_arrival_errors.png')
        plt.show()


def visualize_results(filename: str, output_dir='results'):
    """可视化分析结果
    
    Args:
        filename: 分析报告文件名
        output_dir: 输出目录
    """
    print(f"加载分析报告: {filename}")
    
    # 创建output_dir目录（如果不存在）
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    # 加载分析报告
    try:
        report = load_analysis_report(filename)
        print(f"成功加载分析报告，包含 {report.get('tasks_analyzed', 0)} 个任务的数据")
    except Exception as e:
        print(f"加载分析报告失败: {e}")
        return
    
    # 绘制各种图表
    print("\n生成加工时间误差图表...")
    plot_processing_time_errors(report, output_dir)
    
    print("\n生成到达时间误差图表...")
    plot_arrival_time_errors(report, output_dir)
    
    print("\n生成摘要统计图表...")
    plot_summary_statistics(report, output_dir)
    
    print("\n生成工位级别误差图表...")
    plot_station_level_analysis(report, output_dir)
    
    print(f"\n可视化完成！图表已保存到 {output_dir} 文件夹")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="仿真结果可视化工具")
    parser.add_argument('filename', nargs='?', default='results/analysis_report.json', 
                        help='分析报告文件名 (默认: results/analysis_report.json)')
    parser.add_argument('--output-dir', default='results', 
                        help='输出目录 (默认: results)')
    args = parser.parse_args()
    
    visualize_results(args.filename, args.output_dir)

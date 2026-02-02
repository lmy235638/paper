#!/usr/bin/env python3
# 时间工具函数

from datetime import datetime
from src.config.constants import DEFAULT_START_TIME

def time_to_str(time_obj: datetime, include_date: bool = False) -> str:
    """将datetime对象转为字符串
    
    Args:
        time_obj: datetime对象
        include_date: 是否包含日期信息，默认不包含
        
    Returns:
        格式化的时间字符串
    """
    if include_date:
        return time_obj.strftime("%Y-%m-%d %H:%M:%S")
    return time_obj.strftime("%H:%M:%S")


def str_to_time(time_str: str, base_time: datetime = None) -> datetime:
    """将HH:MM:SS字符串转为datetime对象，支持自定义基准日期"""
    time_obj = datetime.strptime(time_str, "%H:%M:%S")
    # 如果提供了基准时间，则使用其日期；否则使用默认时间的日期
    if base_time is None:
        base_time = DEFAULT_START_TIME
    return time_obj.replace(year=base_time.year, month=base_time.month, day=base_time.day)

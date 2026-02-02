"""
任务生成器模块

功能：
- 生成钢包加工任务计划
- 考虑工位可用性和转运时间
- 支持LF精炼、RH精炼和LF+RH双重精炼三种工艺
- 生成甘特图可视化
"""

import random
import json
import os
import sys
import math
import numpy as np

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict
from datetime import datetime, timedelta
import bisect
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from src.utils.time_utils import time_to_str, str_to_time


# ============================================================================
# 第一部分：数据类定义
# ============================================================================

@dataclass
class ProductionPlan:
    """生产计划数据类"""
    pono: int  # 任务编号
    start_ld: str  # 开始点(LD转炉)
    end_cc: str  # 结束连铸机
    refine_process: str  # 精炼工艺
    lf_station: Optional[str]  # LF炉工位,无则为None
    rh_station: Optional[str]  # RH炉工位,无则为None
    
    # 时间信息
    task_start_time: datetime  # 任务开始时间
    task_end_time: datetime  # 任务结束时间
    
    # 精炼时间信息
    lf_start_time: Optional[datetime]  # LF精炼开始时间
    lf_end_time: Optional[datetime]  # LF精炼结束时间
    rh_start_time: Optional[datetime]  # RH精炼开始时间
    rh_end_time: Optional[datetime]  # RH精炼结束时间
    
    # 工序耗时信息（分钟）
    lf_duration: Optional[int]  # LF精炼耗时
    rh_duration: Optional[int]  # RH精炼耗时
    
    # 转运时间信息（分钟）
    ld_to_lf_duration: Optional[int]  # LD转LF转运时间
    ld_to_rh_duration: Optional[int]  # LD转RH转运时间
    lf_to_rh_duration: Optional[int]  # LF转RH转运时间
    lf_to_cc_duration: Optional[int]  # LF转CC转运时间
    rh_to_cc_duration: Optional[int]  # RH转CC转运时间


# ============================================================================
# 第二部分：任务生成器类
# ============================================================================

class TaskGenerator:
    """
    任务生成器类
    
    用于生成钢包加工任务计划，支持多种精炼工艺和转运场景。
    
    属性：
        - start_lds: LD转炉列表
        - end_ccs: 连铸机列表
        - lf_stations: LF精炼炉列表
        - rh_stations: RH精炼炉列表
        - refine_processes: 精炼工艺类型列表
        - transport_data: 工位转运时间数据
        - station_bookings: 工位预订字典
        - ld_bookings: LD工位预订字典
    """
    
    # ========================================================================
    # 类常量定义
    # ========================================================================
    
    # 时间间隔常量
    LD_INTERVAL_MINUTES = 30      # LD最小间隔时间（分钟）
    INITIAL_LD_BOOKING_OFFSET = 40  # 初始LD预订偏移时间（分钟）
    MIN_DURATION = 1              # 最小耗时（避免0/负数）
    STATION_GAP_MINUTES = 5       # 工位预订间隙（分钟）
    
    # 随机模拟参数
    TRANSPORT_ALPHA = 0.2         # 基础上浮系数（半自动化场景）
    TRANSPORT_BETA = 0.1          # 波动系数（半自动化场景）
    DEFAULT_TRANSPORT_TIME = 10   # 默认转运时间，用于工位分配
    TASK_INTERVAL_MIN = 10        # 生成任务间隔时间最小值（分钟）
    TASK_INTERVAL_MAX = 20        # 生成任务间隔时间最大值（分钟）
    
    # ========================================================================
    # 初始化方法
    # ========================================================================
    
    def __init__(self, seed: int = None):
        """初始化任务生成器
        
        Args:
            seed: 随机数种子，用于确保任务生成的可复现性
        """
        self._init_resources()
        self._init_duration_config()
        self._init_transport_data()
        self._init_bookings()
        
        # 设置随机种子
        if seed is not None:
            self._set_random_seed(seed)
            print(f"✅ 已设置随机种子: {seed}")
        else:
            print("⚠️ 未设置随机种子，结果将不可重复")
    
    def _init_resources(self):
        """初始化基础资源配置"""
        self.start_lds = ["1LD", "2LD", "3LD"]
        self.end_ccs = ["1CC", "2CC", "3CC"]
        self.rh_stations = ["1RH", "2RH", "4RH"]
        self.lf_stations = ["1LF", "2LF", "4LF"]
        self.refine_processes = ["LF精炼", "RH精炼", "LF+RH双重精炼"]
    
    def _init_duration_config(self):
        """初始化精炼工序时长配置"""
        self.refine_duration_config: Dict[str, Dict] = {
            "LF精炼": {"base": 60, "fluctuation": 20},
            "RH精炼": {"base": 30, "fluctuation": 15},
            "LF+RH双重精炼": {
                "LF": {"base": 60, "fluctuation": 20},
                "RH": {"base": 30, "fluctuation": 15}
            }
        }
    
    def _init_transport_data(self):
        """初始化工位转运时间数据字典
        
        字段说明：
        - round_trip_min_time: 往返最快时间（分钟）
        """
        self.transport_data = {
            "LD_LF": self._create_transport_dict([
                (("1LD", "1LF"), 5.0),
                (("1LD", "2LF"), 10.4),
                (("1LD", "4LF"), 7.0),
                (("2LD", "1LF"), 6.0),
                (("2LD", "2LF"), 11.4),
                (("2LD", "4LF"), 6.0),
                (("3LD", "1LF"), 7.0),
                (("3LD", "2LF"), 12.4),
                (("3LD", "4LF"), 5.0)
            ]),
            "LD_RH": self._create_transport_dict([
                (("1LD", "1RH"), 12.6),
                (("1LD", "2RH"), 8.0),
                (("1LD", "4RH"), 12.4),
                (("2LD", "1RH"), 11.6),
                (("2LD", "2RH"), 7.0),
                (("2LD", "4RH"), 13.4),
                (("3LD", "1RH"), 10.6),
                (("3LD", "2RH"), 6.0),
                (("3LD", "4RH"), 14.4)
            ]),
            "LF_RH": self._create_transport_dict([
                (("1LF", "1RH"), 12.6),
                (("1LF", "2RH"), 8.4),
                (("1LF", "4RH"), 10.4),
                (("2LF", "1RH"), 7.6),
                (("2LF", "2RH"), 13.6),
                (("2LF", "4RH"), 5.4),
                (("4LF", "1RH"), 5.6),
                (("4LF", "2RH"), 4.0),
                (("4LF", "4RH"), 14.4)
            ]),
            "LF_CC": self._create_transport_dict([
                (("1LF", "1CC"), 7.6),
                (("1LF", "2CC"), 8.6),
                (("1LF", "3CC"), 8.0),
                (("2LF", "1CC"), 13.4),
                (("2LF", "2CC"), 14.4),
                (("2LF", "3CC"), 2.6),
                (("4LF", "1CC"), 3.6),
                (("4LF", "2CC"), 4.6),
                (("4LF", "3CC"), 12.0)
            ]),
            "RH_CC": self._create_transport_dict([
                (("1RH", "1CC"), 6.4),
                (("1RH", "2CC"), 7.4),
                (("1RH", "3CC"), 7.4),
                (("2RH", "1CC"), 2.6),
                (("2RH", "2CC"), 3.6),
                (("2RH", "3CC"), 13.0),
                (("4RH", "1CC"), 15.0),
                (("4RH", "2CC"), 16.0),
                (("4RH", "3CC"), 2.6)
            ])
        }
    
    def _create_transport_dict(self, data_list: List[Tuple[Tuple[str, str], float]]) -> Dict:
        """创建转运时间字典"""
        return {station_pair: {"round_trip_min_time": round_trip}
                for station_pair, round_trip in data_list}
    
    def _init_bookings(self):
        """初始化工位预订字典"""
        self.station_bookings: Dict[str, List[Tuple[datetime, datetime]]] = {
            **{station: [] for station in self.lf_stations},
            **{station: [] for station in self.rh_stations}
        }
        self.ld_bookings: Dict[str, datetime] = {}
    
    # ========================================================================
    # 公开方法
    # ========================================================================
    
    def _set_random_seed(self, seed: int):
        """设置随机数种子，确保任务生成的可复现性"""
        random.seed(seed)
        np.random.seed(seed)
    
    def generate_tasks(self, task_num: int, first_task_start: str = "00:00:00") -> List[ProductionPlan]:
        """生成指定数量的任务"""
        tasks = []
        last_task_start = str_to_time(first_task_start)
        
        # 为每个LD初始化LD预订字典
        self.ld_bookings = {
            station: str_to_time(first_task_start) - timedelta(minutes=self.INITIAL_LD_BOOKING_OFFSET)
            for station in self.start_lds
        }
        
        # 生成每个任务
        for pono in range(task_num):
            task = self._create_single_task(pono, first_task_start, last_task_start)
            tasks.append(task)
            last_task_start = task.task_start_time
        
        return tasks
    
    def _create_single_task(self, pono: int, first_task_start: str, last_task_start: datetime) -> ProductionPlan:
        """创建单个任务"""
        # 1. 基础资源分配
        start_ld = random.choice(self.start_lds)    # 随机选择一个LD炉
        end_cc = random.choice(self.end_ccs)    # 随机选择一个CC工位
        refine_process = random.choice(self.refine_processes)   # 随机选择一个精炼工序，并不选择具体的LF和RH工位
        
        # 2. 任务开始时间计算，使用上一个任务开始时间计算间隔
        task_start = self._calculate_task_start_time(pono, start_ld, first_task_start, last_task_start)
        
        # 3. 预计算精炼时长
        lf_duration, rh_duration = self._calculate_process_durations(refine_process)
        
        # 4. 计算实际转运时间并分配工位
        station_info = self._calculate_optimal_station(start_ld, end_cc, refine_process, task_start, lf_duration, rh_duration)
        
        # 5. 时间轴计算
        lf_start, lf_end, rh_start, rh_end, task_end = self._calculate_time_axis(
            refine_process, task_start, station_info, lf_duration, rh_duration
        )
        
        # 6. 检查时间范围
        self._check_time_range(task_start, task_end, lf_start, lf_end, rh_start, rh_end)
        
        # 7. 创建生产计划对象
        return ProductionPlan(
            pono=pono, start_ld=start_ld, end_cc=end_cc, refine_process=refine_process,
            lf_station=station_info['lf_station'], rh_station=station_info['rh_station'],
            task_start_time=task_start, task_end_time=task_end,
            lf_start_time=lf_start, lf_end_time=lf_end, rh_start_time=rh_start, rh_end_time=rh_end,
            lf_duration=lf_duration, rh_duration=rh_duration,
            ld_to_lf_duration=station_info['ld_to_lf'], ld_to_rh_duration=station_info['ld_to_rh'],
            lf_to_rh_duration=station_info['lf_to_rh'], lf_to_cc_duration=station_info['lf_to_cc'],
            rh_to_cc_duration=station_info['rh_to_cc']
        )
    
    # ========================================================================
    # 时间计算方法
    # ========================================================================
    
    def _calculate_task_start_time(self, pono: int, start_ld: str, first_task_start: str, last_task_start: datetime) -> datetime:
        """计算任务开始时间"""
        if pono == 0:
            return str_to_time(first_task_start)
        
        # 当前使用的LD炉的下一个可用时间
        min_allowed_start = self.ld_bookings[start_ld] + timedelta(minutes=self.LD_INTERVAL_MINUTES)
        # 上一个任务的开始时间+随机间隔（10-20分钟）
        base_start = last_task_start + timedelta(minutes=random.randint(self.TASK_INTERVAL_MIN, self.TASK_INTERVAL_MAX))
        return max(min_allowed_start, base_start)
    
    def _calculate_process_durations(self, refine_process: str) -> Tuple[Optional[int], Optional[int]]:
        """计算精炼时长"""
        lf_duration, rh_duration = None, None
        
        if refine_process == "LF精炼":
            lf_duration = self._calculate_single_refine_duration("LF精炼")
        elif refine_process == "RH精炼":
            rh_duration = self._calculate_single_refine_duration("RH精炼")
        elif refine_process == "LF+RH双重精炼":
            lf_duration = self._calculate_single_refine_duration("LF精炼")
            rh_duration = self._calculate_single_refine_duration("RH精炼")
        
        return lf_duration, rh_duration
    
    def _calculate_single_refine_duration(self, process_type: str) -> int:
        """计算单精炼工序时长"""
        config = self.refine_duration_config[process_type]
        return config["base"] + random.randint(-config["fluctuation"], config["fluctuation"])
    
    # ========================================================================
    # 工位分配方法
    # ========================================================================
    
    def _calculate_optimal_station(self, start_ld: str, end_cc: str, refine_process: str, 
                                   task_start: datetime, lf_duration: int, rh_duration: int) -> Dict:
        """
        根据当前任务的起始LD炉、目标连铸机、精炼工艺类型以及任务开始时间，
        综合评估所有可能的LF/RH工位组合，计算每种组合下的转运耗时与精炼等待时间，
        选出使“任务总时长（从LD出发到CC到达）”最短且工位可用的最优方案，
        并返回包含最优LF、RH工位及对应转运时间的字典。
        
        步骤概览：
        1. 按工艺类型枚举所有可行工位组合（单LF、单RH、LF+RH）。
        2. 对每种组合：
           a) 计算各段转运时间（LD→LF、LD→RH、LF→RH、LF→CC、RH→CC）。
           b) 基于工位当前已预订时段，计算最早可开始精炼时间。
           c) 累加得到任务结束时间，进而得到任务总时长。
        3. 过滤掉工位冲突或无法排程的组合。
        4. 选择总时长最短者作为最优解返回。
        
        返回字典字段：
        - lf_station/rh_station: 分配的LF/RH工位编号，无则为None
        - ld_to_lf/ld_to_rh/lf_to_rh/lf_to_cc/rh_to_cc: 对应段转运时间（分钟），无则为None
        """
        possible_combinations = []
        
        if refine_process == "LF精炼":
            possible_combinations = self._evaluate_lf_combinations(start_ld, end_cc, task_start, lf_duration)
        elif refine_process == "RH精炼":
            possible_combinations = self._evaluate_rh_combinations(start_ld, end_cc, task_start, rh_duration)
        elif refine_process == "LF+RH双重精炼":
            possible_combinations = self._evaluate_double_combinations(start_ld, end_cc, task_start, lf_duration, rh_duration)
        
        if not possible_combinations:
            raise ValueError(f"无法找到有效的工位组合: 工艺={refine_process}, LD={start_ld}, CC={end_cc}")
        
        # 选择总任务时间最短的组合
        best = min(possible_combinations, key=lambda x: x['total_time'])
        
        return {
            'lf_station': best.get('lf_station'), 'rh_station': best.get('rh_station'),
            'ld_to_lf': best.get('ld_to_lf'), 'ld_to_rh': best.get('ld_to_rh'),
            'lf_to_rh': best.get('lf_to_rh'), 'lf_to_cc': best.get('lf_to_cc'),
            'rh_to_cc': best.get('rh_to_cc')
        }
    
    def _evaluate_lf_combinations(self, start_ld: str, end_cc: str, task_start: datetime, lf_duration: int) -> List[Dict]:
        """评估LF精炼工位组合"""
        combinations = []
        for lf_st in self.lf_stations:  # 遍历所有LF工位
            try:
                # 计算LF相关的转运时间
                ld_to_lf = self._calculate_transport_duration("LD_LF", start_ld, lf_st)
                lf_to_cc = self._calculate_transport_duration("LF_CC", lf_st, end_cc)
                
                actual_lf_start = self._find_earliest_available_time(lf_st, lf_duration, task_start + timedelta(minutes=ld_to_lf))
                lf_end = actual_lf_start + timedelta(minutes=lf_duration)
                task_end = lf_end + timedelta(minutes=lf_to_cc)
                
                combinations.append({
                    'lf_station': lf_st, 'rh_station': None,
                    'ld_to_lf': ld_to_lf, 'lf_to_cc': lf_to_cc,
                    'total_time': (task_end - task_start).total_seconds() / 60
                })
            except ValueError:
                # 如果无法计算，跳过该工位
                continue
        return combinations
    
    def _evaluate_rh_combinations(self, start_ld: str, end_cc: str, task_start: datetime, rh_duration: int) -> List[Dict]:
        """评估RH精炼工位组合"""
        combinations = []
        for rh_st in self.rh_stations:
            try:
                ld_to_rh = self._calculate_transport_duration("LD_RH", start_ld, rh_st)
                rh_to_cc = self._calculate_transport_duration("RH_CC", rh_st, end_cc)
                
                actual_rh_start = self._find_earliest_available_time(rh_st, rh_duration, task_start + timedelta(minutes=ld_to_rh))
                rh_end = actual_rh_start + timedelta(minutes=rh_duration)
                task_end = rh_end + timedelta(minutes=rh_to_cc)
                
                combinations.append({
                    'lf_station': None, 'rh_station': rh_st,
                    'ld_to_rh': ld_to_rh, 'rh_to_cc': rh_to_cc,
                    'total_time': (task_end - task_start).total_seconds() / 60
                })
            except ValueError:
                continue
        return combinations
    
    def _evaluate_double_combinations(self, start_ld: str, end_cc: str, task_start: datetime, 
                                       lf_duration: int, rh_duration: int) -> List[Dict]:
        """评估双重精炼工位组合"""
        combinations = []
        for lf_st in self.lf_stations:
            for rh_st in self.rh_stations:
                try:
                    ld_to_lf = self._calculate_transport_duration("LD_LF", start_ld, lf_st)
                    lf_to_rh = self._calculate_transport_duration("LF_RH", lf_st, rh_st)
                    rh_to_cc = self._calculate_transport_duration("RH_CC", rh_st, end_cc)
                    
                    actual_lf_start = self._find_earliest_available_time(lf_st, lf_duration, task_start + timedelta(minutes=ld_to_lf))
                    lf_end = actual_lf_start + timedelta(minutes=lf_duration)
                    actual_rh_start = self._find_earliest_available_time(rh_st, rh_duration, lf_end + timedelta(minutes=lf_to_rh))
                    rh_end = actual_rh_start + timedelta(minutes=rh_duration)
                    task_end = rh_end + timedelta(minutes=rh_to_cc)
                    
                    combinations.append({
                        'lf_station': lf_st, 'rh_station': rh_st,
                        'ld_to_lf': ld_to_lf, 'lf_to_rh': lf_to_rh, 'rh_to_cc': rh_to_cc,
                        'total_time': (task_end - task_start).total_seconds() / 60
                    })
                except ValueError:
                    continue
        return combinations
    
    # ========================================================================
    # 时间轴计算方法
    # ========================================================================
    
    def _calculate_time_axis(self, refine_process: str, task_start: datetime, station_info: Dict,
                             lf_duration: Optional[int], rh_duration: Optional[int]) -> Tuple:
        """计算时间轴（考虑工位可用性）"""
        lf_station, rh_station = station_info['lf_station'], station_info['rh_station']
        ld_to_lf, ld_to_rh = station_info['ld_to_lf'], station_info['ld_to_rh']
        lf_to_rh, lf_to_cc, rh_to_cc = station_info['lf_to_rh'], station_info['lf_to_cc'], station_info['rh_to_cc']
        
        lf_start, lf_end, rh_start, rh_end = None, None, None, None
        
        if refine_process == "LF精炼":
            # 运用之前评估的最优组合，实际预定工位
            lf_start = self._find_earliest_available_time(lf_station, lf_duration, task_start + timedelta(minutes=ld_to_lf))
            lf_end = lf_start + timedelta(minutes=lf_duration)
            task_end = lf_end + timedelta(minutes=lf_to_cc)
            self._book_station(lf_station, lf_start, lf_end)
        
        elif refine_process == "RH精炼":
            rh_start = self._find_earliest_available_time(rh_station, rh_duration, task_start + timedelta(minutes=ld_to_rh))
            rh_end = rh_start + timedelta(minutes=rh_duration)
            task_end = rh_end + timedelta(minutes=rh_to_cc)
            self._book_station(rh_station, rh_start, rh_end)
        
        elif refine_process == "LF+RH双重精炼":
            lf_start = self._find_earliest_available_time(lf_station, lf_duration, task_start + timedelta(minutes=ld_to_lf))
            lf_end = lf_start + timedelta(minutes=lf_duration)
            rh_start = self._find_earliest_available_time(rh_station, rh_duration, lf_end + timedelta(minutes=lf_to_rh))
            rh_end = rh_start + timedelta(minutes=rh_duration)
            task_end = rh_end + timedelta(minutes=rh_to_cc)
            self._book_station(lf_station, lf_start, lf_end)
            self._book_station(rh_station, rh_start, rh_end)
        
        return lf_start, lf_end, rh_start, rh_end, task_end
    
    def _check_time_range(self, task_start: datetime, task_end: datetime, lf_start: Optional[datetime],
                           lf_end: Optional[datetime], rh_start: Optional[datetime], rh_end: Optional[datetime]):
        """验证子任务时间是否在任务时间范围内"""
        # 验证LF时间
        if lf_start and lf_end:
            if lf_start < task_start:
                raise ValueError(f"LF精炼开始时间 {time_to_str(lf_start)} 早于任务开始时间 {time_to_str(task_start)}")
            if lf_end > task_end:
                raise ValueError(f"LF精炼结束时间 {time_to_str(lf_end)} 晚于任务结束时间 {time_to_str(task_end)}")
        
        # 验证RH时间
        if rh_start and rh_end:
            if rh_start < task_start:
                raise ValueError(f"RH精炼开始时间 {time_to_str(rh_start)} 早于任务开始时间 {time_to_str(task_start)}")
            if rh_end > task_end:
                raise ValueError(f"RH精炼结束时间 {time_to_str(rh_end)} 晚于任务结束时间 {time_to_str(task_end)}")
    
    # ========================================================================
    # 工位管理方法
    # ========================================================================
    
    def _find_earliest_available_time(self, station_id: str, required_duration: int, earliest_possible: datetime) -> datetime:
        """查找工位最早可用的时间"""
        if station_id not in self.station_bookings or not self.station_bookings[station_id]:
            return earliest_possible
        
        bookings = self.station_bookings[station_id]
        current_start = earliest_possible
        current_end = current_start + timedelta(minutes=required_duration)
        
        # 检查时间段是否已经被预订
        if self._is_station_available(station_id, current_start, current_end):
            return current_start
        
        # 使用bisect查找插入位置，返回的是earliest_possible在booking_ends中合适的索引
        booking_ends = [booking[1] for booking in bookings]
        idx = bisect.bisect_left(booking_ends, earliest_possible)
        
        # 检查插入位置前后是否存在足够的时间间隔
        if idx > 0:
            prev_end = bookings[idx - 1][1]
            current_start = max(earliest_possible, prev_end + timedelta(minutes=self.STATION_GAP_MINUTES))
            current_end = current_start + timedelta(minutes=required_duration)
            # 任务的结束时间不能超过下一个任务的开始时间
            if current_end <= bookings[idx][0]:
                return current_start
        
        # 当前位置没有足够的时间间隔，遍历每一个预订的结束时间，找到第一个合适的时间
        for i in range(idx, len(bookings)):
            current_start = bookings[i][1] + timedelta(minutes=self.STATION_GAP_MINUTES)
            current_end = current_start + timedelta(minutes=required_duration)
            if i + 1 < len(bookings):
                if current_end <= bookings[i + 1][0]:
                    return current_start
            else:
                return current_start
        
        # 当所有前面的时间间隙检查都失败时，返回最后一个预订结束后的最早可用时间
        return bookings[-1][1] + timedelta(minutes=self.STATION_GAP_MINUTES)
    
    def _is_station_available(self, station_id: str, start_time: datetime, end_time: datetime) -> bool:
        """检查工位在指定时间段是否可用"""
        if station_id not in self.station_bookings:
            return True
        
        for booking in self.station_bookings[station_id]:
            if not (end_time < booking[0] or start_time > booking[1]):
                return False
        return True
    
    def _book_station(self, station_id: str, start_time: datetime, end_time: datetime):
        """预订工位"""
        if station_id not in self.station_bookings:
            self.station_bookings[station_id] = []
        bisect.insort(self.station_bookings[station_id], (start_time, end_time))
    
    # ========================================================================
    # 转运时间计算方法
    # ========================================================================
    
    def _calculate_transport_duration(self, transport_type: str, start_station: str, end_station: str) -> int:
        """根据起始和目标工位计算实际转运时间"""
        if transport_type in self.transport_data and (start_station, end_station) in self.transport_data[transport_type]:
            data = self.transport_data[transport_type][(start_station, end_station)]
            return self._generate_actual_transport_time(data["round_trip_min_time"])
        raise ValueError(f"未找到{transport_type}类型下{start_station}到{end_station}的转运时间数据")
    
    def _generate_actual_transport_time(self, round_trip_min_time: float) -> int:
        """根据随机模拟方法生成实际转运时间"""
        mu = round_trip_min_time * (1 + self.TRANSPORT_ALPHA)
        sigma = mu * self.TRANSPORT_BETA
        t_rand = np.random.normal(mu, sigma)
        # 向上取整
        return max(math.ceil(t_rand), int(round_trip_min_time))
    
    # ========================================================================
    # 输出方法
    # ========================================================================
    
    def save_tasks_to_json(self, tasks: List[ProductionPlan], save_path: str = "./data/tasks.json") -> bool:
        """将任务保存为JSON文件"""
        try:
            task_dicts = []
            for task in tasks:
                task_dict = {
                    "pono": task.pono, "start_ld": task.start_ld, "end_cc": task.end_cc,
                    "refine_process": task.refine_process, "lf_station": task.lf_station, "rh_station": task.rh_station,
                    "time_info": {
                        "task_start": time_to_str(task.task_start_time), "task_end": time_to_str(task.task_end_time),
                        "lf_start": time_to_str(task.lf_start_time) if task.lf_start_time else None,
                        "lf_end": time_to_str(task.lf_end_time) if task.lf_end_time else None,
                        "rh_start": time_to_str(task.rh_start_time) if task.rh_start_time else None,
                        "rh_end": time_to_str(task.rh_end_time) if task.rh_end_time else None
                    },
                    "duration_info": {"lf_duration": task.lf_duration, "rh_duration": task.rh_duration},
                    "transport_info": {
                        "ld_to_lf": self._calc_time_diff(task.task_start_time, task.lf_start_time) if task.lf_start_time else None,
                        "ld_to_rh": self._calc_time_diff(task.task_start_time, task.rh_start_time) if task.rh_start_time and task.refine_process != "LF+RH双重精炼" else None,
                        "lf_to_rh": self._calc_time_diff(task.lf_end_time, task.rh_start_time) if task.lf_end_time and task.rh_start_time else None,
                        "lf_to_cc": self._calc_time_diff(task.lf_end_time, task.task_end_time) if task.lf_end_time and task.refine_process != "LF+RH双重精炼" else None,
                        "rh_to_cc": self._calc_time_diff(task.rh_end_time, task.task_end_time) if task.rh_end_time else None
                    }
                }
                task_dicts.append(task_dict)
            
            save_dir = os.path.dirname(save_path)
            if save_dir and not os.path.exists(save_dir):
                os.makedirs(save_dir)
            
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(task_dicts, f, ensure_ascii=False, indent=4)
            
            print(f"✅ Task data saved successfully to: {os.path.abspath(save_path)}")
            return True
        except Exception as e:
            print(f"❌ Error saving task data: {e}")
            return False
    
    def _calc_time_diff(self, start: Optional[datetime], end: Optional[datetime]) -> Optional[int]:
        """计算时间差（分钟）"""
        if start and end:
            return int((end - start).total_seconds() / 60)
        return None
    
    def generate_gantt_chart(self, tasks: List[ProductionPlan], save_path: str = "./data/gantt_chart.png") -> bool:
        """生成甘特图"""
        try:
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False
            
            fig, (ax_station, ax_task) = plt.subplots(2, 1, figsize=(14, 14), sharex=True)
            
            # 任务颜色映射 - 统一使用动态生成
            def get_task_color(pono):
                # 使用HSV颜色空间动态生成颜色
                import colorsys
                hue = (pono * 0.618033988749895) % 1.0  # 黄金分割比例，生成均匀分布的色相
                saturation = 0.7 + (pono % 3) * 0.1  # 饱和度在0.7-0.9之间变化
                value = 0.8 + (pono % 2) * 0.1  # 明度在0.8-0.9之间变化
                # 转换为RGB并返回十六进制颜色
                r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
                return f'#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}'
            
            task_colors = {task.pono: get_task_color(task.pono) for task in tasks}
            
            # 工序颜色映射
            process_colors = {'transport': '#FFFF99', 'lf_process': '#1f77b4', 'rh_process': '#2ca02c'}
            
            # 上半部分：按工位展示
            all_stations = {task.lf_station for task in tasks if task.lf_station}
            all_stations.update(task.rh_station for task in tasks if task.rh_station)
            
            station_order = sorted([s for s in all_stations if 'LF' in s]) + sorted([s for s in all_stations if 'RH' in s])
            station_y = {station: i for i, station in enumerate(station_order)}
            legend_added = set()
            
            for task in tasks:
                pono, color = task.pono, task_colors.get(task.pono, 'gray')
                
                # 绘制LF精炼工序
                if task.lf_station and task.lf_start_time and task.lf_end_time:
                    label = f'任务{pono}' if pono not in legend_added else ""
                    ax_station.barh(station_y[task.lf_station], task.lf_end_time - task.lf_start_time,
                                   left=task.lf_start_time, height=0.6, color=color, edgecolor='black', alpha=0.8, label=label)
                    ax_station.text(task.lf_start_time + (task.lf_end_time - task.lf_start_time) / 2, station_y[task.lf_station],
                                   f"任务{pono}", va='center', ha='center', fontsize=9)
                    legend_added.add(pono)
                
                # 绘制RH精炼工序
                if task.rh_station and task.rh_start_time and task.rh_end_time:
                    label = f'任务{pono}' if pono not in legend_added else ""
                    ax_station.barh(station_y[task.rh_station], task.rh_end_time - task.rh_start_time,
                                   left=task.rh_start_time, height=0.6, color=color, edgecolor='black', alpha=0.8, label=label)
                    ax_station.text(task.rh_start_time + (task.rh_end_time - task.rh_start_time) / 2, station_y[task.rh_station],
                                   f"任务{pono}", va='center', ha='center', fontsize=9)
                    legend_added.add(pono)
            
            ax_station.set_yticks([station_y[s] for s in station_order])
            ax_station.set_yticklabels(station_order, fontsize=11)
            ax_station.grid(True, axis='x', alpha=0.5, linestyle='--')
            ax_station.set_title('钢包加工编排甘特图 - 按工位展示', fontsize=16, fontweight='bold')
            ax_station.set_ylabel('工位', fontsize=14)
            ax_station.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=12)
            
            # 下半部分：按任务展示
            task_y = {task.pono: i for i, task in enumerate(tasks)}
            
            for task in tasks:
                row = task_y[task.pono]
                color = task_colors.get(task.pono, 'gray')
                
                # 绘制任务整体时间范围
                ax_task.barh(row, task.task_end_time - task.task_start_time, left=task.task_start_time,
                            height=0.8, color=color, edgecolor='black', alpha=0.3)
                
                if task.refine_process == "LF精炼":
                    # 第一段：ld-lf转运
                    ax_task.barh(row, task.lf_start_time - task.task_start_time, left=task.task_start_time,
                                height=0.5, color=process_colors['transport'], edgecolor='black', alpha=0.7)
                    ax_task.text(task.task_start_time + (task.lf_start_time - task.task_start_time) / 2, row,
                                task.start_ld, va='center', ha='center', fontsize=9, color='blue')  # LD标签
                    # 第二段：lf精炼
                    ax_task.barh(row, task.lf_end_time - task.lf_start_time, left=task.lf_start_time,
                                height=0.5, color=process_colors['lf_process'], edgecolor='black', alpha=1.0)
                    # 第三段：cc-lf转运
                    ax_task.barh(row, task.task_end_time - task.lf_end_time, left=task.lf_end_time,
                                height=0.5, color=process_colors['transport'], edgecolor='black', alpha=0.7)
                    ax_task.text(task.lf_end_time + (task.task_end_time - task.lf_end_time) / 2, row,
                                task.end_cc, va='center', ha='center', fontsize=9, color='red')
                
                elif task.refine_process == "RH精炼":
                    ax_task.barh(row, task.rh_start_time - task.task_start_time, left=task.task_start_time,
                                height=0.5, color=process_colors['transport'], edgecolor='black', alpha=0.7)
                    ax_task.text(task.task_start_time + (task.rh_start_time - task.task_start_time) / 2, row,
                                task.start_ld, va='center', ha='center', fontsize=9, color='blue')
                    ax_task.barh(row, task.rh_end_time - task.rh_start_time, left=task.rh_start_time,
                                height=0.5, color=process_colors['rh_process'], edgecolor='black', alpha=1.0)
                    ax_task.barh(row, task.task_end_time - task.rh_end_time, left=task.rh_end_time,
                                height=0.5, color=process_colors['transport'], edgecolor='black', alpha=0.7)
                    ax_task.text(task.rh_end_time + (task.task_end_time - task.rh_end_time) / 2, row,
                                task.end_cc, va='center', ha='center', fontsize=9, color='red')
                
                elif task.refine_process == "LF+RH双重精炼":
                    ax_task.barh(row, task.lf_start_time - task.task_start_time, left=task.task_start_time,
                                height=0.5, color=process_colors['transport'], edgecolor='black', alpha=0.7)
                    ax_task.text(task.task_start_time + (task.lf_start_time - task.task_start_time) / 2, row,
                                task.start_ld, va='center', ha='center', fontsize=9, color='blue')
                    ax_task.barh(row, task.lf_end_time - task.lf_start_time, left=task.lf_start_time,
                                height=0.5, color=process_colors['lf_process'], edgecolor='black', alpha=1.0)
                    ax_task.barh(row, task.rh_start_time - task.lf_end_time, left=task.lf_end_time,
                                height=0.5, color=process_colors['transport'], edgecolor='black', alpha=0.7)
                    ax_task.barh(row, task.rh_end_time - task.rh_start_time, left=task.rh_start_time,
                                height=0.5, color=process_colors['rh_process'], edgecolor='black', alpha=1.0)
                    ax_task.barh(row, task.task_end_time - task.rh_end_time, left=task.rh_end_time,
                                height=0.5, color=process_colors['transport'], edgecolor='black', alpha=0.7)
                    ax_task.text(task.rh_end_time + (task.task_end_time - task.rh_end_time) / 2, row,
                                task.end_cc, va='center', ha='center', fontsize=9, color='red')
                
                ax_task.text(task.task_start_time + (task.task_end_time - task.task_start_time) / 2, row,
                            task.refine_process, va='center', ha='center', fontweight='bold')
            
            ax_task.set_yticks([task_y[t.pono] for t in tasks])
            ax_task.set_yticklabels([f"任务{t.pono}" for t in tasks], fontsize=11)
            ax_task.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            plt.xticks(rotation=45, fontsize=10)
            ax_task.grid(True, axis='x', alpha=0.5, linestyle='--')
            ax_task.set_title('钢包加工编排甘特图 - 按任务展示', fontsize=16, fontweight='bold')
            ax_task.set_xlabel('时间', fontsize=14)
            ax_task.set_ylabel('任务', fontsize=14)
            # 添加工序图例
            import matplotlib.patches as mpatches
            process_legend = [
                mpatches.Patch(facecolor=process_colors['transport'], edgecolor='black', linewidth=1, label='转运'),
                mpatches.Patch(facecolor=process_colors['lf_process'], edgecolor='black', linewidth=1, label='LF精炼'),
                mpatches.Patch(facecolor=process_colors['rh_process'], edgecolor='black', linewidth=1, label='RH精炼')
            ]
            ax_task.legend(handles=process_legend, bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=12)
            
            plt.tight_layout()
            
            save_dir = os.path.dirname(save_path)
            if save_dir and not os.path.exists(save_dir):
                os.makedirs(save_dir)
            
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"✅ 甘特图已成功保存到: {os.path.abspath(save_path)}")
            return True
        except Exception as e:
            print(f"❌ 生成甘特图失败: {e}")
            return False
    
    def check_task_time_consistency(self, tasks: List[ProductionPlan]) -> bool:
        """
        检查任务时间一致性
        
        验证每个任务的开始时间加上所有加工时间和转运时间是否等于结束时间
        
        Args:
            tasks: 生产计划任务列表
            
        Returns:
            bool: 所有任务时间是否一致
        """
        all_valid = True
        
        for task in tasks:
            # 计算实际总时间（分钟）
            actual_total_time = int((task.task_end_time - task.task_start_time).total_seconds() / 60)
            
            # 根据精炼工艺计算预期总时间
            expected_total_time = 0
            
            if task.refine_process == "LF精炼":
                # LF精炼：LD→LF转运 + LF精炼 + LF→CC转运
                expected_total_time = (task.ld_to_lf_duration or 0) + (task.lf_duration or 0) + (task.lf_to_cc_duration or 0)
            elif task.refine_process == "RH精炼":
                # RH精炼：LD→RH转运 + RH精炼 + RH→CC转运
                expected_total_time = (task.ld_to_rh_duration or 0) + (task.rh_duration or 0) + (task.rh_to_cc_duration or 0)
            elif task.refine_process == "LF+RH双重精炼":
                # LF+RH双重精炼：LD→LF转运 + LF精炼 + LF→RH转运 + RH精炼 + RH→CC转运
                expected_total_time = (task.ld_to_lf_duration or 0) + (task.lf_duration or 0) + \
                                     (task.lf_to_rh_duration or 0) + (task.rh_duration or 0) + \
                                     (task.rh_to_cc_duration or 0)
            
            # 检查时间是否一致
            if abs(actual_total_time - expected_total_time) > 1:  # 允许1分钟误差（由于四舍五入）
                all_valid = False
                print(f"❌ 任务 {task.pono} 时间计算异常:")
                print(f"   精炼工艺: {task.refine_process}")
                print(f"   开始时间: {time_to_str(task.task_start_time)}")
                print(f"   结束时间: {time_to_str(task.task_end_time)}")
                print(f"   实际总时间: {actual_total_time} 分钟")
                print(f"   预期总时间: {expected_total_time} 分钟")
                print(f"   差异: {abs(actual_total_time - expected_total_time)} 分钟")
                print(f"   转运时间详情:")
                if task.ld_to_lf_duration:
                    print(f"     - LD→LF: {task.ld_to_lf_duration} 分钟")
                if task.ld_to_rh_duration:
                    print(f"     - LD→RH: {task.ld_to_rh_duration} 分钟")
                if task.lf_to_rh_duration:
                    print(f"     - LF→RH: {task.lf_to_rh_duration} 分钟")
                if task.lf_to_cc_duration:
                    print(f"     - LF→CC: {task.lf_to_cc_duration} 分钟")
                if task.rh_to_cc_duration:
                    print(f"     - RH→CC: {task.rh_to_cc_duration} 分钟")
                print(f"   加工时间详情:")
                if task.lf_duration:
                    print(f"     - LF精炼: {task.lf_duration} 分钟")
                if task.rh_duration:
                    print(f"     - RH精炼: {task.rh_duration} 分钟")
                print()
        
        if all_valid:
            print(f"✅ 所有 {len(tasks)} 个任务时间计算正确，一致性验证通过！")
        else:
            print(f"⚠️  部分任务时间计算异常，请检查上述提示！")
        
        return all_valid


# ============================================================================# 主程序入口# ============================================================================

if __name__ == "__main__":
    # 配置参数
    task_num = 10
    first_task_start = "00:00:00"
    
    # 初始化生成器
    generator = TaskGenerator(seed=23)
    
    print(f"\n🔄 正在生成 {task_num} 个任务...")
    task_list = generator.generate_tasks(task_num=task_num, first_task_start=first_task_start)
    
    # 保存任务数据
    generator.save_tasks_to_json(task_list)
    # 检查任务时间一致性
    generator.check_task_time_consistency(task_list)
    # 生成甘特图
    generator.generate_gantt_chart(task_list)

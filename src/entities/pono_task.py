from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from src.utils.task_generator import ProductionPlan


@dataclass
class PonoTask(ProductionPlan):
    """继承自Task类，作为目标计划，添加了实际加工和到达时间的记录功能"""
    # 实际到达时间信息
    actual_ld_arrive_time: Optional[datetime] = None  # 实际到达LD转炉时间
    actual_lf_arrive_time: Optional[datetime] = None  # 实际到达LF炉时间
    actual_rh_arrive_time: Optional[datetime] = None  # 实际到达RH炉时间
    actual_cc_arrive_time: Optional[datetime] = None  # 实际到达连铸机时间

    # 实际离开时间信息
    actual_ld_leave_time: Optional[datetime] = None  # 实际离开LD转炉时间
    actual_lf_leave_time: Optional[datetime] = None  # 实际离开LF炉时间
    actual_rh_leave_time: Optional[datetime] = None  # 实际离开RH炉时间
    actual_cc_leave_time: Optional[datetime] = None  # 实际离开连铸机时间

    # 实际加工时间信息
    actual_lf_process_time: Optional[datetime] = None  # 实际LF炉加工时间
    actual_rh_process_time: Optional[datetime] = None  # 实际RH炉加工时间
    actual_cc_process_time: Optional[datetime] = None  # 实际连铸机加工时间

    # 记录任务是否被下发
    ld_to_lf_dispatched: bool = False
    ld_to_rh_dispatched: bool = False
    lf_to_rh_dispatched: bool = False
    lf_to_cc_dispatched: bool = False
    rh_to_cc_dispatched: bool = False

    # 记录任务是否被完成
    lf_completed: bool = False
    rh_completed: bool = False
    all_completed: bool = False
    
    def get_task_start_time(self) -> datetime:
        """获取任务开始时间"""
        return self.task_start_time
    
    def get_task_end_time(self) -> datetime:
        """获取任务结束时间"""
        return self.task_end_time

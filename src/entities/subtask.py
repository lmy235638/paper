from dataclasses import dataclass
from datetime import datetime


@dataclass
class Subtask:
    """子任务类，包含子任务的类型、开始时间、结束时间"""
    pono: int
    start_time: datetime
    end_time: datetime
    start_station: str
    end_station: str
    
    # 新增属性
    type: str  # 子任务类型
    generate_time: datetime  # 子任务生成时间
    process_time: int  # 加工时间（分钟）
    dispatched: bool = False  # 是否已下发
    completed: bool = False  # 是否已完成
    track_tasks: list = None  # 存储所属的 TrackTask
    
    def __post_init__(self):
        """初始化后处理"""
        if self.track_tasks is None:
            self.track_tasks = []


from dataclasses import dataclass


@dataclass
class TrackTask:
    pono: int
    type: str
    start_time: float
    end_time: float
    start_station: str
    end_station: str
    track_id: str
    vehicle_id: str
    status: str
    process_time: int = 0  # 加工时间（分钟）
    completed: bool = False  # 任务是否完成

    def mark_completed(self):
        """标记任务为已完成"""
        self.completed = True
        self.status = "completed"
        print(f"  任务 {self.pono} 已标记为完成，类型: {self.type}")

    def is_completed(self) -> bool:
        """检查任务是否已完成
        
        Returns:
            bool: 如果任务已完成返回True，否则返回False
        """
        return self.completed

    

from dataclasses import dataclass
from typing import Optional


@dataclass
class Goods:
    """货物类，用于表示在生产流程中的货物"""
    pono: int  # 任务编号
    goods_id: str  # 货物ID
    start_ld: str  # 起始工位
    end_cc: str  # 结束工位
    refine_process: str  # 精炼工艺
    current_status: str = "ready"  # 货物状态：ready, processing, completed
    is_process: bool = False  # 是否正在加工
    station_times: dict = None  # 记录每个加工工位的进出时间
    
    def __post_init__(self):
        """初始化后处理"""
        if self.station_times is None:
            self.station_times = {}

    def __str__(self):
        return f"Goods(pono={self.pono}, id={self.goods_id})"
    
    def __repr__(self):
        return self.__str__()
    
    def set_process(self, is_processing: bool):
        """设置货物的加工状态"""
        self.is_process = is_processing
        if is_processing:
            self.current_status = "processing"
        else:
            self.current_status = "ready"
    
    def record_arrival_time(self, station_id: str, time: int):
        """记录到达工位的时间
        
        Args:
            station_id: 工位ID
            time: 到达时间
        """
        if station_id not in self.station_times:
            self.station_times[station_id] = {}
        self.station_times[station_id]['in_time'] = time
    
    def record_departure_time(self, station_id: str, time: int):
        """记录离开工位的时间
        
        Args:
            station_id: 工位ID
            time: 离开时间
        """
        if station_id not in self.station_times:
            self.station_times[station_id] = {}
        self.station_times[station_id]['out_time'] = time
    
    def get_station_duration(self, station_id: str) -> Optional[int]:
        """获取在工位的停留时间
        
        Args:
            station_id: 工位ID
            
        Returns:
            停留时间，如果没有完整的时间记录则返回None
        """
        if station_id in self.station_times:
            station_time = self.station_times[station_id]
            if 'in_time' in station_time and 'out_time' in station_time:
                return station_time['out_time'] - station_time['in_time']
        return None
    
    def get_all_station_durations(self) -> dict:
        """获取所有工位的停留时间
        
        Returns:
            字典，键为工位ID，值为停留时间
        """
        durations = {}
        for station_id, times in self.station_times.items():
            if 'in_time' in times and 'out_time' in times:
                durations[station_id] = times['out_time'] - times['in_time']
        return durations
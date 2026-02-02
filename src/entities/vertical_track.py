from src.bases.base_track import Track
from typing import Tuple


class VerticalTrack(Track):
    """垂直轨道实现"""

    def __init__(self, track_id: str, track_type: str, start_point: Tuple[int, int], end_point: Tuple[int, int], registry):        
        # 调用父类构造函数，设置轨道类型为vertical
        super().__init__(track_id, track_type, start_point, end_point, registry)
        
    def get_length(self) -> float:
        """获取垂直轨道的长度"""
        return abs(self.end_point[1] - self.start_point[1])
        
    def is_point_on_track(self, point: Tuple[int, int]) -> bool:
        """检查点是否在垂直轨道上"""
        # 检查x坐标是否匹配，且y坐标在轨道范围内
        return (point[0] == self.start_point[0] and 
                min(self.start_point[1], self.end_point[1]) <= point[1] <= max(self.start_point[1], self.end_point[1]))

from src.bases.base_track import Track
from typing import Tuple


class HorizontalTrack(Track):
    """水平轨道实现"""

    def __init__(self, track_id: str, track_type: str, start_point: Tuple[int, int], end_point: Tuple[int, int], registry):
        # 调用父类构造函数，设置轨道类型为horizontal
        super().__init__(track_id, track_type, start_point, end_point, registry)
        
    def get_length(self) -> float:
        """获取水平轨道的长度"""
        return abs(self.end_point[0] - self.start_point[0])
        
    def is_point_on_track(self, point: Tuple[int, int]) -> bool:
        """检查点是否在水平轨道上"""
        # 检查y坐标是否匹配，且x坐标在轨道范围内
        return (point[1] == self.start_point[1] and 
                min(self.start_point[0], self.end_point[0]) <= point[0] <= max(self.start_point[0], self.end_point[0]))

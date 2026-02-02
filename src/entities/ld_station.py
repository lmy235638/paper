from src.bases.base_workstation import Workstation
from typing import Tuple, List, Any
from src.core.registry import EnvRegistry


class LDStation(Workstation):
    """LD工位类：负责生成货物"""
    def __init__(self, station_id: str, pos: Tuple[int, int], station_type: str, connected_tracks=None, registry: EnvRegistry = None):
        super().__init__(station_id, pos, station_type, connected_tracks, registry)
    
    def add_goods(self, goods):
        """添加货物到LD工位
        
        Args:
            goods: 要添加的货物对象
        """
        self.goods_list.append(goods)
        print(f"  工位 {self.station_id} 接收货物: {goods}")
    
    def process_goods(self):
        """LD工位不自动加工货物，只负责生成货物"""
        # LD工位不自动加工货物，直接返回
        return
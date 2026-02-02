from src.bases.base_workstation import Workstation
from typing import Tuple, List, Any
from src.core.registry import EnvRegistry


class CCStation(Workstation):
    """CC工位类：负责完成货物加工并移除货物"""
    def __init__(self, station_id: str, pos: Tuple[int, int], station_type: str, connected_tracks=None, registry: EnvRegistry = None):
        super().__init__(station_id, pos, station_type, connected_tracks, registry)
    
    def process_goods(self):
        """CC工位不自动加工货物，只负责接收和移除货物"""
        # CC工位不自动加工货物，直接返回
        return
    
    def remove_goods(self, goods):
        """从CC工位移除货物并认为加工完成
        
        Args:
            goods: 要移除的货物对象
        """
        if goods in self.goods_list:
            self.goods_list.remove(goods)
            # 从环境注册表中移除货物
            if self.registry:
                # 查找货物的ID并从注册表中移除
                goods_id = getattr(goods, 'goods_id', None)
                if goods_id:
                    self.registry.remove_object(goods_id, 'goods')
            print(f"  工位 {self.station_id} 完成货物加工并移除货物: {goods}")
            return True
        return False
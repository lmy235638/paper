from abc import ABC, abstractmethod
from typing import Tuple, List, Any, Set, Optional

from src.core.registry import EnvRegistry
from src.config.constants import StationType


class Workstation(ABC):
    """工位基类：所有工位的通用抽象
    
    主要功能：
    1. 存储货物（包括交互工位作为货物仓库）
    2. 记录货物进出工位的时间
    3. 处理货物加工（仅适用于加工工位）
    
    注意：不再管理车辆，车辆存取货物的主动权在车辆端
    """

    def __init__(self, station_id: str, pos: Tuple[int, int], station_type: str, connected_tracks, registry: EnvRegistry = None):
        self.station_id = station_id
        self.pos = pos  # 坐标（网格交点）
        self.station_type = station_type  # processing(加工) / intersection(交汇) / ld(起始) / cc(终止)
        self.connected_tracks = connected_tracks  # 连接的轨道ID集合
        self.registry = registry  # 环境注册表引用，用于访问其他对象

        self.goods_list: List[Any] = []  # 当前工位上的货物

    def is_free(self) -> bool:
        """检查工位是否空闲"""
        # 只检查是否有货物，不再检查操作和加工状态
        return len(self.goods_list) == 0

    def has_goods(self) -> bool:
        """检查工位上是否有货物
        
        Returns:
            如果工位上有货物则返回True，否则返回False
        """
        return len(self.goods_list) > 0
    
    def get_goods_by_pono(self, pono: int) -> Optional[Any]:
        """根据pono获取货物（不移除）
        
        Args:
            pono: 货物的pono
            
        Returns:
            对应的货物对象，如果未找到则返回None
        """
        for goods in self.goods_list:
            if goods.pono == pono:
                return goods
        return None

    def add_goods(self, goods, current_time=None):
        """添加货物到工位
        
        Args:
            goods: 要添加的货物对象
            current_time: 当前时间，用于记录货物进入工位的时间
        """
        self.goods_list.append(goods)
        
        # 只有加工工位才记录货物时间
        if self.station_type == StationType.PROCESS:
            # 使用货物对象的方法记录到达时间
            goods.record_arrival_time(self.station_id, current_time)
        
        print(f"  工位 {self.station_id} 接收货物: {goods}")

    def remove_goods(self, goods, current_time=None):
        """从工位移除货物
        
        Args:
            goods: 要移除的货物对象
            current_time: 当前时间，用于记录货物离开工位的时间
            
        Returns:
            如果成功移除则返回True，否则返回False
        """
        if goods in self.goods_list:
            self.goods_list.remove(goods)
            
            # 只有加工工位才记录货物时间
            if self.station_type == StationType.PROCESS:
                # 使用货物对象的方法记录离开时间
                goods.record_departure_time(self.station_id, current_time)
            
            print(f"  工位 {self.station_id} 移除货物: {goods}")
            return True
        return False

    def update(self, current_time):
        """更新工位状态
        
        Args:
            current_time: 当前时间，用于货物时间记录
        """
        # 简化后的更新方法，只需要记录时间，不需要处理操作和加工状态
        pass

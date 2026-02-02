from src.bases.base_vehicle import Vehicle
from typing import Any, Tuple


class Crane(Vehicle):
    """起重机实现"""

    def __init__(self, vehicle_id: str, vehicle_type: str, track_id: str, initial_location: Any, registry, connect_vehicles: list = None):
        # 调用父类构造函数
        super().__init__(vehicle_id, vehicle_type, track_id, initial_location, registry, connect_vehicles)
        

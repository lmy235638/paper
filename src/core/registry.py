from typing import Dict, Any, Optional, List, TypeVar, Type
from datetime import datetime, timedelta
from src.config.constants import DEFAULT_START_TIME

# 泛型类型变量，提供类型提示
T = TypeVar('T')


class EnvRegistry:
    """环境注册表，提供对象注册和查询功能，降低对象间耦合度"""

    def __init__(self):
        # 按类型存储对象
        self._objects_by_type: Dict[str, Dict[str, Any]] = {
            'vehicle': {},
            'workstation': {},
            'track': {},
            'goods': {},
            'task': {},
            'subtask': {},
            'track_task': {},
        }

        # 环境引用，用于访问环境级别的信息
        self._env = None

        # 初始化时间为默认的基准时间（可以根据需要调整基准日期）
        self.time = DEFAULT_START_TIME

    def set_env(self, env: 'Env'):
        """设置环境引用"""
        self._env = env

    def get_env(self) -> Optional['Env']:
        """获取环境引用"""
        return self._env

    def register_object(self, obj: Any, obj_id: str, obj_type: str) -> bool:
        """注册对象到注册表"""
        if obj_type not in self._objects_by_type:
            raise ValueError(f"Unknown object type: {obj_type}")
            # self._objects_by_type[obj_type] = {}

        if obj_id in self._objects_by_type[obj_type]:
            return False

        self._objects_by_type[obj_type][obj_id] = obj
        return True

    def unregister_object(self, obj_id: str, obj_type: str) -> bool:
        """从注册表中注销对象"""
        if obj_type not in self._objects_by_type:
            return False

        if obj_id in self._objects_by_type[obj_type]:
            del self._objects_by_type[obj_type][obj_id]
            return True
        return False
    
    def remove_object(self, obj_id: str, obj_type: str) -> bool:
        """从注册表中移除对象（unregister_object的别名）"""
        return self.unregister_object(obj_id, obj_type)

    def get_object(self, obj_id: str, obj_type: str) -> Optional[Any]:
        """根据ID和类型获取对象"""
        if obj_type in self._objects_by_type:
            return self._objects_by_type[obj_type].get(obj_id)
        return None

    def get_objects_by_type(self, obj_type: str) -> List[Any]:
        """根据类型获取所有对象"""
        if obj_type in self._objects_by_type:
            return list(self._objects_by_type[obj_type].values())
        return []

    def get_objects_by_type_and_class(self, obj_type: str, obj_class: Type[T]) -> List[T]:
        """根据类型和类获取所有对象"""
        objects = self.get_objects_by_type(obj_type)
        return [obj for obj in objects if isinstance(obj, obj_class)]

    def set_time(self, time: datetime) -> None:
        """设置当前时间"""
        self.time = time

    def get_time(self) -> datetime:
        """获取当前时间"""
        return self.time

    def update_time(self, delta_seconds: int = 10) -> None:
        """更新当前时间"""
        self.time += timedelta(seconds=delta_seconds)
    
    # 便捷方法：获取所有工位
    def get_workstations(self) -> List[Any]:
        """获取所有工位对象"""
        return self.get_objects_by_type('workstation')
    
    # 便捷方法：获取所有轨道
    def get_tracks(self) -> List[Any]:
        """获取所有轨道对象"""
        return self.get_objects_by_type('track')
    
    # 便捷方法：获取所有车辆
    def get_vehicles(self) -> List[Any]:
        """获取所有车辆对象"""
        return self.get_objects_by_type('vehicle')
    
    # 便捷方法：获取所有货物
    def get_goods(self) -> List[Any]:
        """获取所有货物对象"""
        return self.get_objects_by_type('goods')
    
    # 便捷方法：获取所有任务
    def get_tasks(self) -> List[Any]:
        """获取所有任务对象"""
        return self.get_objects_by_type('task')
    
    # 便捷方法：根据ID获取轨道
    def get_track_by_id(self, track_id: str) -> Optional[Any]:
        """根据ID获取轨道对象"""
        return self.get_object(track_id, 'track')
    
    # 便捷方法：根据ID获取车辆
    def get_vehicle_by_id(self, vehicle_id: str) -> Optional[Any]:
        """根据ID获取车辆对象"""
        return self.get_object(vehicle_id, 'vehicle')
    
    # 便捷方法：根据ID获取工位
    def get_workstation_by_id(self, workstation_id: str) -> Optional[Any]:
        """根据ID获取工位对象"""
        return self.get_object(workstation_id, 'workstation')

    def get_ponotask_by_id(self, task_id: str) -> Optional[Any]:
        """根据ID获取非计划任务对象"""
        return self.get_object(task_id, 'task')
from abc import ABC, abstractmethod
from typing import Tuple, List, Any, Optional

from src.core.registry import EnvRegistry
from src.config.constants import VehicleAction, VehicleStatus, TrackType


class Vehicle(ABC):
    """车对象"""

    def __init__(self, vehicle_id: str, vehicle_type: str, track_id: str, initial_location: Any, registry: EnvRegistry,
                 connect_vehicles: list = None):
        self.vehicle_id = vehicle_id
        self.vehicle_type = vehicle_type
        self.track_id = track_id
        self.current_location = initial_location
        self.connect_vehicles = connect_vehicles or []  # 连接的车辆ID列表

        self.goods = None
        self.current_task = None
        self.status = VehicleStatus.IDLE    # 用来标识车辆当前任务状态: 空闲、移动、等待

        self.registry = registry  # 环境注册表引用，用于访问其他对象

        # 位置更新参数
        self.move_speed = 1  # 移动速度，每次移动1个单位
        self._has_unloaded_goods = False # 标记已卸载货物

    def assign_task(self, task):
        """分配任务给车辆"""
        self.current_task = task
        # 根据任务类型设置车辆状态
        if task.type == 'avoid':
            self.status = VehicleStatus.WAITING  # 避让任务设置为等待状态
        else:
            self.status = VehicleStatus.MOVING  # 其他任务设置为移动状态
        # 格式化任务编号，包含工位信息
        task_name = f"{task.pono}_{task.start_station}_to_{task.end_station}"
        print(f"  车辆 {self.vehicle_id} 已接收任务: {task_name}，当前状态: {self.status}")

    def remove_task(self):
        """移除当前任务"""
        # 标记任务为已完成
        self.current_task.mark_completed()
        self.current_task = None
        self.status = VehicleStatus.IDLE
        self._has_unloaded_goods = False

    def set_operating(self, state: bool):
        """设置车辆操作状态"""
        self.is_operating = state

    def _is_at_station(self, station) -> bool:
        """检查车辆是否在指定工位的位置"""
        return self.current_location[0] == station.pos[0] and self.current_location[1] == station.pos[1]

    def _get_task_target_pos(self, task) -> tuple:
        """获取任务的目标位置
        
        Args:
            task: 当前任务
        
        Returns:
            目标位置坐标
        """
        # 获取当前轨道
        track = self.registry.get_object(self.track_id, 'track')

        # 获取起始工位和结束工位
        start_station = None
        end_station = None
        for station in track.stations:
            if station.station_id == task.start_station:
                start_station = station
            elif station.station_id == task.end_station:
                end_station = station

        # 根据车辆是否有货物确定目标位置
        if self.goods:
            # 有货物，目标是结束工位
            return end_station.pos
        else:
            # 无货物，目标是起始工位
            return start_station.pos

    def _determine_action(self) -> 'VehicleAction':
        """决定执行什么动作
        
        Returns:
            动作类型
        """
        # 车辆没有任务说明是空闲状态
        if not self.current_task:
            return VehicleAction.STOP

        # 获取当前轨道和目标位置
        track = self.registry.get_object(self.track_id, 'track')
        target_pos = self._get_task_target_pos(self.current_task)

        # 检查是否已到达目标位置（完整坐标匹配）
        if self.current_location[0] == target_pos[0] and self.current_location[1] == target_pos[1]:
            if self.goods:
                # 有货物，执行放下动作
                return VehicleAction.UNLOAD
            else:
                # 无货物，执行拿起动作
                return VehicleAction.LOAD
        else:
            # 未到达目标位置，继续移动
            # 根据轨道类型确定当前位置和目标位置
            current_pos, target_pos = self._get_position_values(track, target_pos)
            if current_pos < target_pos:
                # 目标位置在右侧，执行右移
                return VehicleAction.MOVE_RIGHT
            else:
                # 目标位置在左侧，执行左移
                return VehicleAction.MOVE_LEFT

    def _get_position_values(self, track, target_pos):
        """根据轨道类型获取当前位置和目标位置的值
        
        Args:
            track: 轨道对象
            target_pos: 目标位置坐标
            
        Returns:
            tuple: (当前位置值, 目标位置值)
        """
        if track.track_type == TrackType.HORIZONTAL:
            current_pos = self.current_location[0]
            target_pos = target_pos[0]
        else:
            current_pos = self.current_location[1]
            target_pos = target_pos[1]
        return current_pos, target_pos

    def _execute_action(self, action: 'VehicleAction', current_time):
        """执行具体动作
        
        Args:
            action: 动作类型
            current_time: 当前时间
        """
        # 获取当前轨道
        track = self.registry.get_object(self.track_id, 'track')

        if action == VehicleAction.STOP:
            # 原地不动
            pass

        elif action == VehicleAction.MOVE_LEFT:
            # 左移（坐标减小方向）
            if track.track_type == TrackType.HORIZONTAL:
                new_location = (self.current_location[0] - self.move_speed, self.current_location[1])
            else:
                new_location = (self.current_location[0], self.current_location[1] - self.move_speed)

            # 更新位置
            self.current_location = new_location
            self.status = VehicleStatus.MOVING

        elif action == VehicleAction.MOVE_RIGHT:
            # 右移（坐标增大方向）
            if track.track_type == TrackType.HORIZONTAL:
                new_location = (self.current_location[0] + self.move_speed, self.current_location[1])
            else:
                new_location = (self.current_location[0], self.current_location[1] + self.move_speed)

            # 更新位置
            self.current_location = new_location
            self.status = VehicleStatus.MOVING

        elif action == VehicleAction.LOAD:
            # 拿起货物
            print(f"  车辆 {self.vehicle_id} 开始拿起货物")
            self._complete_load_action(current_time)
            self.status = VehicleStatus.MOVING  # 直接恢复移动状态

        elif action == VehicleAction.UNLOAD:
            # 放下货物
            print(f"  车辆 {self.vehicle_id} 开始放下货物")
            self._complete_unload_action(current_time)
            self.status = VehicleStatus.MOVING  # 直接恢复移动状态
        else:
            raise ValueError(f"未知动作类型: {action}")

    def _complete_load_action(self, current_time):
        """完成拿起货物动作"""
        # 确定任务的目标工位ID
        target_station_id = self.current_task.start_station
        # 获取目标工位
        track = self.registry.get_object(self.track_id, 'track')
        current_station = track.get_station_by_id(target_station_id)

        # 添加调试日志
        if not current_station:
            raise ValueError(f"车辆 {self.vehicle_id} 尝试拿起货物，但找不到目标工位 {target_station_id}")
        elif not current_station.has_goods():
            print(f"  车辆 {self.vehicle_id} 尝试拿起货物，但工位 {current_station.station_id} 上没有货物")
        else:
            # 先获取货物
            target_goods = current_station.get_goods_by_pono(self.current_task.pono)
            
            if target_goods:
                # 然后移除货物并记录离开时间
                current_station.remove_goods(target_goods, current_time)
                # 成功找到并获取相关货物
                self.goods = target_goods
                print(f"  车辆 {self.vehicle_id} 成功拿起货物: {self.goods} (pono: {self.goods.pono})")
            else:
                # 没有找到与当前任务相关的货物
                print(f"  车辆 {self.vehicle_id} 尝试拿起货物，但工位 {current_station.station_id} 上没有与任务相关的货物 (任务pono: {self.current_task.pono})")

    def _complete_unload_action(self, current_time):
        """完成放下货物动作"""
        target_station_id = self.current_task.end_station
        
        # 使用轨道的 get_station_by_id 方法获取目标工位
        track = self.registry.get_object(self.track_id, 'track')
        current_station = track.get_station_by_id(target_station_id)

        if current_station and self.goods:
            # 将货物放到工位
            current_station.add_goods(self.goods, current_time)
            print(f"  车辆 {self.vehicle_id} 成功放下货物: {self.goods} 到工位 {current_station.station_id}")
            # 车辆清空货物
            self.goods = None
            # 标记已卸载货物
            self._has_unloaded_goods = True
        else:
            raise ValueError(f"车辆 {self.vehicle_id} 尝试放下货物，但找不到目标工位 {target_station_id}")

    def _check_task_be_completed(self):
        """检查任务是否完成，如果完成则移除当前任务"""
        if not self.current_task:
            return 
        else:
            track = self.registry.get_object(self.track_id, 'track')
            end_station = track.get_station_by_id(self.current_task.end_station)
    
            # 检查是否在目标工位点
            if not (self.current_location[0] == end_station.pos[0] and 
                    self.current_location[1] == end_station.pos[1]):
                return
            
            # 检查是否已卸载货物
            if not self._has_unloaded_goods:
                return
            
            # 任务完成，移除当前任务
            self.remove_task()
            print(f"  车辆 {self.vehicle_id} 任务已完成并移除")


    def update(self, current_time):
        """更新车辆状态
        
        Args:
            current_time: 当前时间
        """
        # 决定当前执行什么动作
        action = self._determine_action()
        # 执行动作
        self._execute_action(action, current_time)

        # 检查任务是否完成并移除
        self._check_task_be_completed()

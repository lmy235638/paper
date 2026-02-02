from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from src.core.registry import EnvRegistry


class Vehicle(ABC):
    """车对象"""
    # 动作类型定义
    ACTION_STAY = 0
    ACTION_LEFT = 1
    ACTION_RIGHT = 2
    ACTION_PICK = 3
    ACTION_DROP = 4
    
    def __init__(self, vehicle_id: str, vehicle_type: str, track_id: str, initial_location: Any, registry: EnvRegistry, connect_vehicles: list = None):
        self.vehicle_id = vehicle_id
        self.vehicle_type = vehicle_type
        self.track_id = track_id
        self.current_location = initial_location
        self.connect_vehicles = connect_vehicles or []  # 连接的车辆ID列表

        self.goods = None
        self.current_task = None
        self.status = 'idle'  # idle, moving, loading, unloading, processing
        self.is_operating = False  # 是否正在操作（由工位控制）
        self.action_time = 0  # 动作执行剩余时间
        self.registry = registry  # 环境注册表引用，用于访问其他对象
        
        # 位置更新参数
        self.move_speed = 1  # 移动速度，每次移动1个单位
        self.action_duration = 1  # 拿起/放下货物的时间

    def assign_task(self, task):
        """分配任务给车辆"""
        self.current_task = task
        self.status = 'moving'  # 任务分配后立即变为移动状态
        print(f"  车辆 {self.vehicle_id} 已接收任务: {task.pono}_{task.type}")

    def remove_task(self):
        """移除当前任务"""
        self.current_task = None
        self.status = 'idle'
        print(f"  车辆 {self.vehicle_id} 已完成任务，变为空闲状态")

    def set_operating(self, state: bool):
        """设置车辆操作状态"""
        self.is_operating = state

    def calculate_distance(self, pos1: tuple, pos2: tuple) -> int:
        """计算两点间距离"""
        if self.registry.get_object(self.track_id, 'track').track_type == 'horizontal':
            return abs(pos1[0] - pos2[0])
        else:
            return abs(pos1[1] - pos2[1])
    
    def is_at_station(self, station) -> bool:
        """检查车辆是否在指定工位的位置"""
        return self.current_location[0] == station.pos[0] and self.current_location[1] == station.pos[1]

    def _get_station_by_name(self, station_id: str):
        """根据工位ID获取工位，只支持精确匹配"""
        # 只进行精确匹配
        for track_id in self.registry.get_objects_by_type('track'):
            track = self.registry.get_object(track_id, 'track')
            for station in track.stations:
                if station.station_id == station_id:
                    return station
        
        return None
    
    def get_task_target_pos(self, task) -> tuple:
        """获取任务的目标位置
        
        Args:
            task: 当前任务
        
        Returns:
            目标位置坐标
        """
        # 获取当前轨道
        track = self.registry.get_object(self.track_id, 'track')
        if not track:
            return self.current_location
        
        # 获取起始工位和结束工位（只使用精确匹配）
        start_station = None
        end_station = None
        
        # 只进行精确匹配
        for station in track.stations:
            if station.station_id == task.start_station:
                start_station = station
            elif station.station_id == task.end_station:
                end_station = station
        
        if not start_station or not end_station:
            return self.current_location
        
        # 根据车辆是否有货物确定目标位置
        if self.goods:
            # 有货物，目标是结束工位
            return end_station.pos
        else:
            # 无货物，目标是起始工位
            return start_station.pos
    
    def determine_action(self) -> int:
        """决定执行什么动作
        
        Returns:
            动作类型：0-原地不动，1-左移，2-右移，3-拿起货物，4-放下货物
        """
        if not self.current_task:
            return self.ACTION_STAY
        
        # 获取当前轨道
        track = self.registry.get_object(self.track_id, 'track')
        if not track:
            return self.ACTION_STAY
        
        # 获取目标位置
        target_pos = self.get_task_target_pos(self.current_task)
        
        # 根据轨道类型确定当前位置和目标位置
        if track.track_type == 'horizontal':
            current_pos = self.current_location[0]
            target_pos = target_pos[0]
        else:
            current_pos = self.current_location[1]
            target_pos = target_pos[1]
        
        # 检查是否已到达目标位置
        if current_pos == target_pos:
            # 检查是否在工位上
            for station in track.stations:
                if self.is_at_station(station):
                    # 在工位上，执行装载/卸载动作
                    # 检查工位类型，如果是交互工位，则不执行拿起/放下动作
                    if station.station_type == 'interaction':
                        # 交互工位，原地不动
                        return self.ACTION_STAY
                    
                    if self.goods:
                        # 有货物，执行放下动作
                        return self.ACTION_DROP
                    else:
                        # 无货物，执行拿起动作
                        return self.ACTION_PICK
            # 不在工位上，原地不动
            return self.ACTION_STAY
        elif current_pos < target_pos:
            # 目标位置在右侧，执行右移
            return self.ACTION_RIGHT
        else:
            # 目标位置在左侧，执行左移
            return self.ACTION_LEFT

    def execute_action(self, action: int):
        """执行具体动作
        
        Args:
            action: 动作类型
        """
        # 获取当前轨道
        track = self.registry.get_object(self.track_id, 'track')
        if not track:
            return
        
        if action == self.ACTION_STAY:
            # 原地不动
            self.status = 'idle' if not self.current_task else self.status
        
        elif action == self.ACTION_LEFT:
            # 左移（坐标减小方向）
            if track.track_type == 'horizontal':
                new_location = (self.current_location[0] - self.move_speed, self.current_location[1])
            else:
                new_location = (self.current_location[0], self.current_location[1] - self.move_speed)
            
            # 更新位置
            self.current_location = new_location
            self.status = 'moving'
            print(f"  车辆 {self.vehicle_id} 左移至位置 {self.current_location}")
        
        elif action == self.ACTION_RIGHT:
            # 右移（坐标增大方向）
            if track.track_type == 'horizontal':
                new_location = (self.current_location[0] + self.move_speed, self.current_location[1])
            else:
                new_location = (self.current_location[0], self.current_location[1] + self.move_speed)
            
            # 更新位置
            self.current_location = new_location
            self.status = 'moving'
            print(f"  车辆 {self.vehicle_id} 右移至位置 {self.current_location}")
        
        elif action == self.ACTION_PICK:
            # 拿起货物
            self.status = 'loading'
            if self.action_time == 0:
                self.action_time = self.action_duration
                print(f"  车辆 {self.vehicle_id} 开始拿起货物，预计需要 {self.action_duration} 时间单位")
        
        elif action == self.ACTION_DROP:
            # 放下货物
            self.status = 'unloading'
            if self.action_time == 0:
                self.action_time = self.action_duration
                print(f"  车辆 {self.vehicle_id} 开始放下货物，预计需要 {self.action_duration} 时间单位")

    def update_action_time(self):
        """更新动作执行时间"""
        if self.action_time > 0:
            self.action_time -= 1
            if self.action_time == 0:
                # 动作执行完成
                if self.status == 'loading':
                    # 拿起货物完成
                    self._complete_pick_action()
                elif self.status == 'unloading':
                    # 放下货物完成
                    self._complete_drop_action()

    def _complete_pick_action(self):
        """完成拿起货物动作"""
        # 获取当前轨道
        track = self.registry.get_object(self.track_id, 'track')
        
        # 查找当前位置的工位
        current_station = None
        for station in track.stations:
            if self.is_at_station(station):
                current_station = station
                break
        
        # 添加调试日志
        if not current_station:
            print(f"  车辆 {self.vehicle_id} 尝试拿起货物，但不在任何工位上")
        elif not current_station.goods_list:
            print(f"  车辆 {self.vehicle_id} 尝试拿起货物，但工位 {current_station.station_id} 上没有货物")
        else:
            # 从工位获取货物
            self.goods = current_station.goods_list.pop(0)
            print(f"  车辆 {self.vehicle_id} 成功拿起货物: {self.goods}")
            # 更新货物状态
            self.goods.current_station = f"vehicle_{self.vehicle_id}"
            self.goods.current_status = "transporting"
        
        self.status = 'moving'  # 恢复移动状态

    def _complete_drop_action(self):
        """完成放下货物动作"""
        # 获取当前轨道
        track = self.registry.get_object(self.track_id, 'track')
        
        # 查找当前位置的工位
        current_station = None
        for station in track.stations:
            if self.is_at_station(station):
                current_station = station
                break
        
        if current_station and self.goods:
            # 将货物放到工位
            current_station.goods_list.append(self.goods)
            # 更新货物状态
            self.goods.current_station = current_station.station_id
            self.goods.current_status = "ready"
            print(f"  车辆 {self.vehicle_id} 成功放下货物: {self.goods} 到工位 {current_station.station_id}")
            
            # 检查是否是CC工位，如果是，则移除货物并认为加工完成
            if hasattr(current_station, 'remove_goods'):
                current_station.remove_goods(self.goods)
            
            self.goods = None
        
        # 检查任务是否完成
        if self.current_task and self._is_task_completed():
            self.remove_task()
        else:
            self.status = 'moving'  # 恢复移动状态

    def _is_task_completed(self) -> bool:
        """判断任务是否完成"""
        if not self.current_task:
            return True
        
        # 对于 ld_to_lf 类型任务，必须有货物才算任务可能完成
        if self.current_task.type == 'ld_to_lf' and not self.goods:
            return False
        
        # 获取当前轨道
        track = self.registry.get_object(self.track_id, 'track')
        if not track:
            return False
        
        # 获取目标位置（只使用精确匹配）
        end_station = None
        
        # 只进行精确匹配
        for station in track.stations:
            if station.station_id == self.current_task.end_station:
                end_station = station
                break
        
        if not end_station:
            return False
        
        # 检查是否到达终点位置
        if track.track_type == 'horizontal':
            current_pos = self.current_location[0]
            end_pos = end_station.pos[0]
        else:
            current_pos = self.current_location[1]
            end_pos = end_station.pos[1]
        
        # 检查是否已卸载货物
        if self.current_task.type != 'avoid' and self.goods is not None:
            return False
        
        # 对于 ld_to_lf 类型任务，检查是否是起始工位
        # 如果是起始工位（start_station），任务还没完成（需要拿货）
        # 如果是结束工位（end_station），任务可能完成（需要送货）
        if self.current_task.type == 'ld_to_lf':
            current_station = None
            for station in track.stations:
                if station.pos[0] == current_pos if track.track_type == 'horizontal' else station.pos[1] == current_pos:
                    current_station = station
                    break
            
            if current_station:
                # 只使用精确匹配
                if current_station.station_id == self.current_task.start_station:
                    if self.goods is None:
                        return False
                elif current_station.station_id == self.current_task.end_station:
                    if self.goods is not None:
                        return False
        
        return current_pos == end_pos

    def update(self, current_time):
        """更新车辆状态
        
        Args:
            current_time: 当前时间
        """
        # 检查是否被工位操作
        if self.is_operating:
            return
        
        # 检查动作执行时间
        self.update_action_time()
        
        # 如果正在执行动作（loading/unloading），则不进行新动作决策
        if self.status in ['loading', 'unloading']:
            return
        
        # 决定执行什么动作
        action = self.determine_action()
        
        # 执行动作
        self.execute_action(action)
        
        # 检查任务是否完成
        if self._is_task_completed() and self.current_task:
            print(f"  车辆 {self.vehicle_id} 完成任务: {self.current_task.pono}_{self.current_task.type}")
            self.remove_task()

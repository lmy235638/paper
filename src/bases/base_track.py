from abc import ABC, abstractmethod
from typing import Tuple, List, Dict, Optional
import random


class Track(ABC):
    """轨道对象"""

    def __init__(self, track_id: str, track_type: str, start_point: Tuple[int, int], end_point: Tuple[int, int],
                 registry):
        self.track_id = track_id
        self.track_type = track_type  # horizontal, vertical
        self.start_point = start_point
        self.end_point = end_point
        self.safety_distance = 1  # 安全距离

        self.vehicles = []
        self.stations = []  # 轨道上的工位
        self.tasks = []  # 轨道上的任务
        self.pending_tasks = []  # 等待分配的任务
        self.buffer = []  # 任务缓冲区，用于冲突消解时存放原任务

        self.registry = registry  # 环境注册表引用，用于访问其他对象

    def add_vehicle(self, vehicle):
        """添加车辆到轨道"""
        self.vehicles.append(vehicle)

    def add_station(self, station):
        """添加工位到轨道"""
        self.stations.append(station)
    
    def assign_task(self, task):
        """分配任务到轨道"""
        self.pending_tasks.append(task)
        print(f"  轨道 {self.track_id} 已接收任务: {task.pono}_{task.type}")

    def get_idle_vehicles(self) -> List:
        """获取轨道上的空闲车辆"""
        return [vehicle for vehicle in self.vehicles if vehicle.status == 'idle']

    def find_closest_vehicle(self, task, idle_vehicles) -> Optional:
        """找到距离任务起点最近的车辆"""
        if not idle_vehicles:
            return None
        
        # 获取起始工位和结束工位的位置
        start_station = None
        end_station = None
        for station in self.stations:
            if station.station_id == task.start_station:
                start_station = station
            elif station.station_id == task.end_station:
                end_station = station
        
        if not start_station:
            return None
        
        closest_vehicle = None
        min_distance = float('inf')
        
        for vehicle in idle_vehicles:
            # 根据轨道类型计算距离
            if self.track_type == 'horizontal':
                distance = abs(vehicle.current_location[0] - start_station.pos[0])
            else:
                distance = abs(vehicle.current_location[1] - start_station.pos[1])
            
            if distance < min_distance:
                min_distance = distance
                closest_vehicle = vehicle
        
        return closest_vehicle

    def select_vehicle(self, task, strategy='naive') -> Optional:
        """选择车辆执行任务
        
        Args:
            task: 要分配的任务
            strategy: 车辆选择策略，可选值：'naive'（朴素选择）、'random'（随机选择）、'rl'（强化学习）
            
        Returns:
            选中的车辆，None表示没有空闲车辆
        """
        idle_vehicles = self.get_idle_vehicles()
        if not idle_vehicles:
            return None
        
        if strategy == 'naive':
            # 朴素选择：选择最近的车辆
            return self.find_closest_vehicle(task, idle_vehicles)
        elif strategy == 'random':
            # 随机选择：随机分配给空闲车辆
            return random.choice(idle_vehicles)
        elif strategy == 'rl':
            # 强化学习：预留接口，暂不实现
            return self.find_closest_vehicle(task, idle_vehicles)  # 默认使用朴素选择
        else:
            # 默认使用朴素选择
            return self.find_closest_vehicle(task, idle_vehicles)

    def assign_task_to_vehicle(self, task, strategy='naive'):
        """将任务分配给具体车辆"""
        vehicle = self.select_vehicle(task, strategy)
        if vehicle:
            vehicle.assign_task(task)
            print(f"  轨道 {self.track_id} 将任务 {task.pono}_{task.type} 分配给车辆 {vehicle.vehicle_id}")
            if task in self.pending_tasks:
                self.pending_tasks.remove(task)
            return True
        return False

    def detect_conflicts(self) -> List[Dict]:
        """检测轨道上车辆间的冲突
        
        Returns:
            冲突列表，每个冲突包含两个车辆信息
        """
        conflicts = []
        # 按位置排序车辆，便于检测相邻车辆冲突
        sorted_vehicles = sorted(self.vehicles, key=lambda v: v.current_location[0] if self.track_type == 'horizontal' else v.current_location[1])
        
        for i in range(len(sorted_vehicles) - 1):
            vehicle1 = sorted_vehicles[i]
            vehicle2 = sorted_vehicles[i + 1]
            
            # 计算两车距离
            if self.track_type == 'horizontal':
                distance = abs(vehicle1.current_location[0] - vehicle2.current_location[0])
            else:
                distance = abs(vehicle1.current_location[1] - vehicle2.current_location[1])
            
            # 检测冲突（距离小于安全距离）
            if distance < self.safety_distance and vehicle1.status == 'moving' and vehicle2.status == 'moving':
                conflicts.append({
                    'vehicle1': vehicle1,
                    'vehicle2': vehicle2,
                    'distance': distance
                })
        
        return conflicts

    def resolve_conflicts(self, conflicts, current_time):
        """解决轨道上车辆间的冲突
        
        Args:
            conflicts: 冲突列表
            current_time: 当前时间
        """
        # 简化冲突处理，暂时跳过冲突检测
        # 后续可以根据实际需求实现更复杂的冲突处理逻辑
        print(f"  轨道 {self.track_id} 检测到 {len(conflicts)} 个冲突，暂时跳过处理")

    def update(self, current_time):
        """更新轨道状态
        
        Args:
            current_time: 当前时间
        """
        # 1. 将待分配任务分配给车辆
        for task in self.pending_tasks.copy():
            if self.assign_task_to_vehicle(task):
                # 任务分配成功，从待分配列表中移除
                if task in self.pending_tasks:
                    self.pending_tasks.remove(task)
        
        # 2. 检测并解决冲突
        conflicts = self.detect_conflicts()
        if conflicts:
            self.resolve_conflicts(conflicts, current_time)
        
        # 3. 恢复缓冲区中的任务
        if self.buffer and all(vehicle.status == 'idle' for vehicle in self.vehicles):
            for task in self.buffer:
                self.pending_tasks.append(task)
            self.buffer.clear()

from abc import ABC, abstractmethod
from typing import Tuple, List, Any, Set, Optional

from src.core.registry import EnvRegistry


class Workstation(ABC):
    """工位基类：所有工位的通用抽象"""

    def __init__(self, station_id: str, pos: Tuple[int, int], station_type: str, connected_tracks, registry: EnvRegistry = None):
        self.station_id = station_id
        self.pos = pos  # 坐标（网格交点）
        self.station_type = station_type  # processing(加工) / intersection(交汇) / ld(起始) / cc(终止)
        self.connected_tracks = connected_tracks  # 连接的轨道ID集合
        self.registry = registry  # 环境注册表引用，用于访问其他对象

        self.goods_list: List[Any] = []  # 当前工位上的货物
        self.vehicles: List = []  # 当前工位上的车辆
        
        # 状态变量
        self.is_operating = False  # 是否正在操作（装载/卸载）
        self.is_processing = False  # 是否正在加工
        self.processing_timer = 0  # 加工剩余时间
        self.operating_timer = 0  # 操作剩余时间
        self.operating_duration = 1  # 操作时间（拿起/放下货物）
        
        # 加工相关
        self.processing_time = 0  # 加工所需时间
        self.current_processing_goods = None  # 当前加工的货物
        self.last_processed_pono = None  # 上一个处理的pono

    def capture_vehicle(self, vehicle):
        """捕获车辆到工位"""
        self.vehicles.append(vehicle)
        vehicle.set_operating(True)
        print(f"  工位 {self.station_id} 捕获车辆 {vehicle.vehicle_id}")

    def release_vehicle(self, vehicle):
        """释放车辆"""
        if vehicle in self.vehicles:
            self.vehicles.remove(vehicle)
            vehicle.set_operating(False)
            # 只有在非LD工位且车辆没有货物时才移除任务
            if 'LD' not in self.station_id and not vehicle.goods:
                vehicle.remove_task()
            print(f"  工位 {self.station_id} 释放车辆 {vehicle.vehicle_id}")

    def set_operating(self, new_state: bool):
        """设置工位操作状态"""
        self.is_operating = new_state
        if new_state:
            self.operating_timer = self.operating_duration

    def set_processing(self, new_state: bool, process_time: int = 0):
        """设置工位加工状态"""
        self.is_processing = new_state
        if new_state:
            self.processing_timer = process_time
            self.processing_time = process_time

    def handle_goods_transfer(self):
        """处理货物交接（仅适用于交互工位）"""
        if self.station_type != 'interaction' or len(self.vehicles) < 2:
            return
        
        # 检查所有车辆的pono是否匹配
        pono = None
        pono_mismatch = False
        for i, vehicle in enumerate(self.vehicles):
            if not vehicle.current_task:
                return
            vehicle_pono = vehicle.current_task.pono
            if pono is None:
                pono = vehicle_pono
            elif vehicle_pono != pono:
                pono_mismatch = True
                break
        
        if pono_mismatch:
            return
        
        # 找到有货物和无货物的车辆
        has_goods_vehicle = None
        no_goods_vehicle = None
        for vehicle in self.vehicles:
            if vehicle.goods:
                has_goods_vehicle = vehicle
            else:
                no_goods_vehicle = vehicle
        
        if has_goods_vehicle and no_goods_vehicle:
            # 进行货物交接
            no_goods_vehicle.goods = has_goods_vehicle.goods
            has_goods_vehicle.goods = None
            print(f"  工位 {self.station_id} 完成货物交接：从车辆 {has_goods_vehicle.vehicle_id} 到车辆 {no_goods_vehicle.vehicle_id}")

    def process_goods(self):
        """处理货物加工（仅适用于加工工位）"""
        # 只有LF和RH这样的真正加工工位才会自动处理货物，LD和CC工位不自动加工
        if self.station_type != 'processing' or not self.goods_list:
            return
        
        # 检查工位ID，只有LF和RH工位才自动加工，LD和CC工位不自动加工
        station_id = self.station_id
        if 'LD' in station_id or 'CC' in station_id:
            return
        
        if not self.is_processing:
            # 开始加工新货物
            self.current_processing_goods = self.goods_list.pop(0)
            
            # 尝试从车辆任务中获取加工时间
            process_time = 5  # 默认加工时间
            for vehicle in self.vehicles:
                if vehicle.current_task and hasattr(vehicle.current_task, 'process_time'):
                    process_time = vehicle.current_task.process_time
                    break
            
            self.set_processing(True, process_time)
            print(f"  工位 {self.station_id} 开始加工货物: {self.current_processing_goods}, 预计加工时间: {process_time}")
        
    def update_processing(self):
        """更新加工状态"""
        if self.is_processing:
            self.processing_timer -= 1
            if self.processing_timer <= 0:
                # 加工完成
                self.last_processed_pono = getattr(self.current_processing_goods, 'pono', None)
                self.goods_list.append(self.current_processing_goods)
                self.current_processing_goods = None
                self.set_processing(False)
                print(f"  工位 {self.station_id} 完成货物加工")

    def update_operating(self):
        """更新操作状态"""
        if self.is_operating:
            self.operating_timer -= 1
            if self.operating_timer <= 0:
                # 操作完成，释放车辆
                if self.station_type == 'intersection':
                    # 交互工位释放所有车辆
                    for vehicle in self.vehicles[:]:
                        self.release_vehicle(vehicle)
                elif self.station_type == 'processing':
                    # 加工工位释放所有车辆，无需等待加工完成
                    for vehicle in self.vehicles[:]:
                        self.release_vehicle(vehicle)
                
                self.set_operating(False)

    def check_captive_vehicle_pono(self) -> bool:
        """检查捕获的车辆pono是否匹配"""
        if not self.vehicles:
            return True
        
        pono = self.vehicles[0].current_task.pono
        
        for vehicle in self.vehicles[1:]:
            vehicle_pono = vehicle.current_task.pono
            if vehicle_pono != pono:
                return False
        
        return True

    def is_free(self) -> bool:
        """检查工位是否空闲"""
        if self.goods_list or self.is_operating or self.is_processing:
            return False
        return True

    def update(self, current_time):
        """更新工位状态
        
        Args:
            current_time: 当前时间
        """
        # 更新操作状态
        self.update_operating()
        
        # 更新加工状态
        self.update_processing()
        
        # 检查是否需要捕获车辆（先捕获车辆，再处理货物交接）
        self._check_vehicle_capture()
        
        # 处理货物交接（仅交互工位）
        if self.station_type == 'interaction':
            pono_match = self.check_captive_vehicle_pono()
            if pono_match:
                self.handle_goods_transfer()
        
        # 处理货物加工（仅加工工位）
        if self.station_type == 'processing' and not self.is_processing:
            self.process_goods()
        
        # 检查是否需要释放车辆
        self._check_vehicle_release()

    def _check_vehicle_capture(self):
        """检查是否需要捕获车辆"""
        # 遍历所有连接的轨道
        for track_id in self.connected_tracks:
            track = self.registry.get_object(track_id, 'track')
            if not track:
                continue
            
            # 检查轨道上的车辆
            for vehicle in track.vehicles:
                # 检查车辆是否有任务，且任务目标是当前工位
                if vehicle.current_task and not vehicle.is_operating:
                    # 计算车辆与工位的距离
                    distance = 0
                    if track.track_type == 'horizontal':
                        distance = abs(vehicle.current_location[0] - self.pos[0])
                    else:
                        distance = abs(vehicle.current_location[1] - self.pos[1])
                    
                    # 距离为0时捕获车辆
                    if distance == 0 and vehicle not in self.vehicles:
                        self.capture_vehicle(vehicle)

    def _check_vehicle_release(self):
        """检查是否需要释放车辆"""
        # 对于交互工位，在完成货物交接后释放车辆
        if self.station_type == 'interaction' and self.vehicles:
            # 检查是否有车辆有货物
            has_goods = any(vehicle.goods for vehicle in self.vehicles)
            # 如果有货物，说明货物交接已经完成，释放车辆
            if has_goods:
                for vehicle in self.vehicles[:]:
                    self.release_vehicle(vehicle)
        
        # 对于LD工位，捕获后立即释放车辆（让车辆继续执行任务）
        if 'LD' in self.station_id and self.vehicles:
            for vehicle in self.vehicles[:]:
                self.release_vehicle(vehicle)
        
        # 对于CC工位，车辆完成放下货物后释放
        if 'CC' in self.station_id and self.vehicles:
            for vehicle in self.vehicles[:]:
                # 如果车辆已经放下货物（即没有货物），释放它
                if not vehicle.goods:
                    self.release_vehicle(vehicle)
        
        # 对于加工工位（LF、RH等），车辆放下货物后释放
        if self.station_type == 'processing' and self.station_id and not ('LD' in self.station_id or 'CC' in self.station_id):
            if self.vehicles:
                for vehicle in self.vehicles[:]:
                    # 如果车辆没有货物（已经放下），释放它
                    if not vehicle.goods:
                        self.release_vehicle(vehicle)

from datetime import datetime
from src.config.constants import DEFAULT_START_TIME
from src.core.registry import EnvRegistry
from src.core.task_dispatcher import TaskDispatcher
from src.core.task_split_buffer import TaskSplitBuffer
from src.core.task_allocator import TaskAllocator
from src.bases.base_track import Track
from src.bases.base_vehicle import Vehicle
from src.bases.base_workstation import Workstation
from src.entities.crane import Crane
from src.entities.trolley import Trolley
from src.entities.vertical_track import VerticalTrack
from src.entities.horizontal_track import HorizontalTrack
from src.entities.processing_station import ProcessingStation
from src.entities.interaction_station import InteractionStation
from src.entities.ld_station import LDStation
from src.entities.cc_station import CCStation
from src.core.path_planner import PathPlanner


class Env:
    """环境类，承载所有对象"""
    def __init__(self, config, tasks):
        # 初始化当前时间为默认的基准时间
        self.current_time = DEFAULT_START_TIME
        self.task_dispatcher = None
        self.task_decomposer = None
        self.path_planner = None
        self.task_allocator = None
        
        # 设置配置
        self.config = config
        self.tasks = tasks
        
        # 创建环境注册表实例
        self.registry = EnvRegistry()
        self.registry.set_env(self)
        self.registry.set_time(self.current_time)

        self._create_objects()

    def reset(self) -> None:
        """重置环境状态"""
        self.current_time = DEFAULT_START_TIME
        self.registry.set_time(self.current_time)
        
        # 初始化任务下发器，并传递外部任务和注册表
        self.task_dispatcher = TaskDispatcher(self.tasks, self.registry)
        # 初始化任务拆分缓冲器
        self.task_split_buffer = TaskSplitBuffer(self.registry)
        # 初始化路径规划器
        self.path_planner = PathPlanner(self.registry)
        # 初始化任务分配器
        self.task_allocator = TaskAllocator(self.registry)

    def step(self) -> None:
        # 获取当前时间
        self.current_time = self.registry.get_time()
        time_str = self.current_time.strftime('%H:%M:%S')
        print(f"\n{'='*60}")
        print(f"{' ' * 15}===== 当前时间: {time_str} =====")
        print(f"{'='*60}")

        # 1. 任务下发：将到达下发时间的任务下发
        self.task_dispatcher.dispatch_tasks(self.current_time)

        # 2. 任务分解：扫描所有已注册的PonoTask任务，将到达分解时间的任务拆分成子任务
        self.task_split_buffer.scan(self.current_time)
        
        # 3. 路径规划：为分解后的子任务规划路径
        track_tasks, planned_subtasks = self.path_planner.scan()

        # 4. 任务分配：将TrackTask分配到各个轨道
        allocated_tasks = self.task_allocator.allocate_tasks(self.current_time)

        # 5. 轨道更新：处理轨道上的任务和冲突
        print(f"\n=== 轨道更新 ===")
        for track in self.registry.get_objects_by_type('track'):
            # 更新轨道状态
            track.update(self.current_time)

        # 6. 车辆更新：执行任务
        print(f"\n=== 车辆更新 ===")
        for vehicle in self.registry.get_objects_by_type('vehicle'):
            vehicle.update(self.current_time)

        # 7. 工位更新：处理工位上的加工和货物交接
        print(f"\n=== 工位更新 ===")
        for workstation in self.registry.get_objects_by_type('workstation'):
            workstation.update(self.current_time)

        # 更新时间
        self.registry.update_time()

    def _create_objects(self) -> None:
        """创建环境中的所有对象"""
        self._create_tracks()
        self._create_vehicles()
        self._create_workstations()

    def _create_tracks(self) -> None:
        """创建环境中的所有轨道"""
        # 创建轨道
        for track_config in self.config['tracks']:
            track_id = track_config['id']
            track_type = track_config['type']
            start_point = tuple(track_config['start_pos'])
            end_point = tuple(track_config['end_pos'])
            if track_type == "horizontal":
                track = HorizontalTrack(track_id, track_type, start_point, end_point, self.registry)
            else:
                track = VerticalTrack(track_id, track_type, start_point, end_point, self.registry)
            self.registry.register_object(track, track_id, 'track')
    
    def _create_vehicles(self) -> None:
        """创建环境中的所有车辆"""
        # 创建车辆
        for vehicle_config in self.config['vehicles']:
            vehicle_id = vehicle_config['id']
            vehicle_type = vehicle_config['type']
            initial_location = tuple(vehicle_config['init_pos'])
            track_id = vehicle_config['track']
            connect_vehicles = vehicle_config.get('connect_vehicles', [])
            if vehicle_type == "trolley":
                vehicle = Trolley(vehicle_id, vehicle_type, track_id, initial_location, self.registry, connect_vehicles)
            else:
                vehicle = Crane(vehicle_id, vehicle_type, track_id, initial_location, self.registry, connect_vehicles)
            self.registry.register_object(vehicle, vehicle_id, 'vehicle')

            # 添加车辆到轨道
            self.registry.get_track_by_id(track_id).add_vehicle(vehicle)

    def _create_workstations(self) -> None:
        """创建环境中的所有工位"""
        # 创建工位
        for station_config in self.config['workstations']:
            station_id = station_config['id']
            pos = tuple(station_config['pos'])
            station_type = station_config['type']
            connected_tracks = set(station_config.get('connected_tracks', []))
            
            # 根据工位ID创建不同类型的工位实例
            if station_type == 'interaction':
                workstation = InteractionStation(station_id, pos, station_type, connected_tracks, self.registry)
            elif 'LD' in station_id:
                # 创建LD工位实例
                workstation = LDStation(station_id, pos, station_type, connected_tracks, self.registry)
            elif 'CC' in station_id:
                # 创建CC工位实例
                workstation = CCStation(station_id, pos, station_type, connected_tracks, self.registry)
            else:
                # 对于其他加工工位，创建ProcessingStation实例
                workstation = ProcessingStation(station_id, pos, station_type, connected_tracks, self.registry)
            
            self.registry.register_object(workstation, station_id, 'workstation')

            # 添加工位进轨道
            for connected_track in connected_tracks:
                self.registry.get_track_by_id(connected_track).add_station(workstation)



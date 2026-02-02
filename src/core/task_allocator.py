from datetime import datetime
from typing import List, Dict, Tuple
from src.entities.track_task import TrackTask


class TaskAllocator:
    """任务分配器，负责将TrackTask分配到各个轨道"""
    
    def __init__(self, registry) -> None:
        """初始化任务分配器
        
        Args:
            registry: 环境注册表，用于获取和存储对象
        """
        self.registry = registry
    
    def allocate_tasks(self, current_time: datetime) -> Dict[str, List[TrackTask]]:
        """分配任务到各个轨道
        
        Args:
            current_time: 当前时间
            
        Returns:
            分配结果，key为轨道ID，value为分配到该轨道的TrackTask列表
        """
        # 从registry中获取所有待分配的TrackTask（状态为pending的任务）
        all_track_tasks = self.registry.get_objects_by_type('track_task')
        pending_track_tasks = [task for task in all_track_tasks if task.status == 'pending']
        
        # 只有当有待分配的任务时，才输出详细信息
        if pending_track_tasks:
            print(f"\n=== 任务分配 ===")
            print(f"时间 {current_time.strftime('%H:%M:%S')}, 待分配TrackTask数量: {len(pending_track_tasks)}")
            
            # 按轨道ID分组TrackTask
            track_tasks_by_track = {}
            for track_task in pending_track_tasks:
                track_id = track_task.track_id
                if track_id not in track_tasks_by_track:
                    track_tasks_by_track[track_id] = []
                track_tasks_by_track[track_id].append(track_task)
            
            # 分配任务到各个轨道
            allocated_tasks = {}
            for track_id, tasks in track_tasks_by_track.items():
                track = self.registry.get_object(track_id, 'track')
                if track:
                    # 为轨道分配任务
                    for task in tasks:
                        track.assign_task(task)
                        # 更新TrackTask状态为assigned
                        task.status = 'assigned'
                        print(f"  将TrackTask {task.pono}_{task.type} 分配到轨道 {track_id}, 车辆 {task.vehicle_id}")
                    
                    allocated_tasks[track_id] = tasks
            
            print(f"已分配 {sum(len(tasks) for tasks in allocated_tasks.values())} 个TrackTask到 {len(allocated_tasks)} 个轨道")
        else:
            # 没有待分配的任务，返回空字典
            allocated_tasks = {}
            track_tasks_by_track = {}
        
        return allocated_tasks

from typing import List, Dict, Optional
from src.entities.track_task import TrackTask
from src.entities.subtask import Subtask


class Node:
    """路径节点类，用于BFS路径搜索"""
    def __init__(self, name: str):
        self.name = name
        self.connected_nodes: List[str] = []  # 连接的节点名称列表
        self.is_occupied: bool = False  # 是否被占用
        self.has_visited: bool = False  # BFS中是否已访问
        self.prev_node: Optional['Node'] = None  # BFS中的前驱节点

    def set_occupied(self, new_state: bool):
        self.is_occupied = new_state


class PathPlanner:
    """路径规划器，负责根据任务和资源生成路径"""
    def __init__(self, registry) -> None:
        self.registry = registry
        self.nodes: Dict[str, Node] = {}  # 节点网络，key为车辆ID
        self.station_adjacent_nodes: Dict[str, List[str]] = {}  # 工位相邻的节点，key为工位ID
        self._generate_nodes()  # 初始化生成节点网络
        # self.print_node_info()  # 输出节点关联信息，用于调试（已注释）
    
    def print_node_info(self) -> None:
        """输出节点关联信息，用于调试配置文件"""
        print("\n=== 节点关联信息 ===")
        
        # 输出所有节点
        print(f"\n1. 所有节点 ({len(self.nodes)} 个):")
        for node_id, node in self.nodes.items():
            print(f"   - 节点 {node_id}, 连接节点: {node.connected_nodes}, 占用状态: {node.is_occupied}")
        
        # 输出工位相邻节点映射
        print(f"\n2. 工位相邻节点映射 ({len(self.station_adjacent_nodes)} 个工位):")
        for station_id, adjacent_nodes in self.station_adjacent_nodes.items():
            print(f"   - 工位 {station_id}, 相邻节点: {adjacent_nodes}")
        
        # 检查是否有节点没有连接关系
        print(f"\n3. 无连接关系的节点:")
        no_connection_nodes = [node_id for node_id, node in self.nodes.items() if not node.connected_nodes]
        if no_connection_nodes:
            print(f"   - 发现 {len(no_connection_nodes)} 个节点没有连接关系: {no_connection_nodes}")
        else:
            print(f"   - 所有节点都有连接关系")
        
        # 检查是否有工位没有相邻节点
        print(f"\n4. 无相邻节点的工位:")
        no_adjacent_nodes = [station_id for station_id, adjacent_nodes in self.station_adjacent_nodes.items() if not adjacent_nodes]
        if no_adjacent_nodes:
            print(f"   - 发现 {len(no_adjacent_nodes)} 个工位没有相邻节点: {no_adjacent_nodes}")
        else:
            print(f"   - 所有工位都有相邻节点")
        
        print("\n=== 节点关联信息结束 ===")
    
    def _generate_nodes(self) -> None:
        """根据环境中的车辆和工位生成节点网络"""
        # 获取所有车辆
        vehicles = self.registry.get_objects_by_type('vehicle')
        
        # 为每个车辆创建节点
        for vehicle in vehicles:
            node = Node(vehicle.vehicle_id)
            self.nodes[vehicle.vehicle_id] = node
        
        # 设置节点之间的连接关系
        for vehicle in vehicles:
            vehicle_id = vehicle.vehicle_id
            node = self.nodes[vehicle_id]
            connect_vehicles = getattr(vehicle, 'connect_vehicles', [])
            
            for connected_vehicle_id in connect_vehicles:
                if connected_vehicle_id in self.nodes:
                    # 添加双向连接
                    if connected_vehicle_id not in node.connected_nodes:
                        node.connected_nodes.append(connected_vehicle_id)
                    
                    # 为连接的节点也添加反向连接
                    connected_node = self.nodes[connected_vehicle_id]
                    if vehicle_id not in connected_node.connected_nodes:
                        connected_node.connected_nodes.append(vehicle_id)
        
        # 获取所有工位
        workstations = self.registry.get_objects_by_type('workstation')
        
        # 为每个工位建立相邻节点映射
        for workstation in workstations:
            station_id = workstation.station_id
            self.station_adjacent_nodes[station_id] = []
            
            # 获取连接到该工位的轨道
            connected_tracks = getattr(workstation, 'connected_tracks', set())
            
            # 确保connected_tracks是可迭代的集合
            if isinstance(connected_tracks, str):
                connected_tracks = {connected_tracks}
            elif connected_tracks is None:
                connected_tracks = set()
            
            for track_id in connected_tracks:
                # 获取轨道上的车辆
                track = self.registry.get_object(track_id, 'track')
                if track:
                    for vehicle in track.vehicles:
                        self.station_adjacent_nodes[station_id].append(vehicle.vehicle_id)
        
        # 检查是否所有节点都有连接关系
        all_nodes_have_connections = all(len(node.connected_nodes) > 0 for node in self.nodes.values())
        
        # 只输出最基本的成功信息
        print("✅ 节点网络生成成功：")
        print(f"   - 所有 {len(self.nodes)} 个节点都已成功创建")
        print(f"   - 所有节点都有链接节点") if all_nodes_have_connections else print(f"   - 警告：部分节点没有链接节点")
    
    def _update_node_occupied(self) -> None:
        """更新节点的占用状态"""
        vehicles = self.registry.get_objects_by_type('vehicle')
        for vehicle in vehicles:
            if vehicle.vehicle_id in self.nodes:
                # 如果车辆有任务，则节点被占用
                self.nodes[vehicle.vehicle_id].is_occupied = vehicle.current_task is not None
    
    def scan(self) -> tuple[List[TrackTask], List[Subtask]]:
        """扫描环境中的子任务，为需要规划路径的子任务规划路径
        
        Returns:
            tuple[List[TrackTask], List[Subtask]]: (规划好路径的轨道任务列表, 成功规划的子任务列表)
        """
        # 从registry中获取所有子任务
        all_subtasks = self.registry.get_objects_by_type('subtask')
        
        # 过滤出需要规划路径的子任务（已生成但未下发且未完成）
        pending_subtasks = [subtask for subtask in all_subtasks if not subtask.dispatched and not subtask.completed]
        
        # 调用路径规划器进行路径规划
        track_tasks, planned_subtasks = self.plan_path(pending_subtasks)
        
        # 从registry获取当前时间
        current_time = self.registry.get_time()
        
        # 打印路径规划信息，使用HH:MM:SS格式显示时间
        current_time_str = current_time.strftime("%H:%M:%S")
        if pending_subtasks:
            pending_pono_list = [subtask.pono for subtask in pending_subtasks]
            print(f"🗺️  开始规划 {len(pending_subtasks)} 个路径，时间 {current_time_str}，待规划PONO编号: {list(set(pending_pono_list))}")
        
        if track_tasks:
            # 打印规划成功的信息，明确标识生成的TrackTask
            print(f"✅ 生成 {len(track_tasks)} 个TrackTask，时间 {current_time_str}")
        
        return track_tasks, planned_subtasks
    
    def plan_path(self, subtasks: List[Subtask]) -> tuple[List[TrackTask], List[Subtask]]:
        """为子任务规划路径
        
        Args:
            subtasks: 需要规划路径的子任务列表
            
        Returns:
            tuple[List[TrackTask], List[Subtask]]: (规划好路径的轨道任务列表, 成功规划的子任务列表)
        """
        track_tasks = []
        planned_subtasks = []  # 存储成功规划的子任务
        
        # 更新节点占用状态
        self._update_node_occupied()
        
        for i, subtask in enumerate(subtasks):
            # 为当前子任务寻找路径
            path_solution = self._find_path_bfs(subtask)
            
            if path_solution:
                # 根据路径解决方案生成TrackTask
                for path_segment in path_solution:
                    # 转换时间为float类型（Unix时间戳）
                    start_time_float = subtask.start_time.timestamp()
                    end_time_float = subtask.end_time.timestamp()
                    
                    # 生成TrackTask对象，使用正确的字段和默认值
                    track_task = TrackTask(
                        pono=subtask.pono,
                        type=subtask.type,  # 使用子任务类型
                        start_time=start_time_float,
                        end_time=end_time_float,
                        start_station=path_segment['start'],
                        end_station=path_segment['end'],
                        track_id=path_segment['track'],
                        vehicle_id=path_segment['vehicle'],  # 当前车辆ID
                        status="pending",  # 默认状态为pending
                        process_time=subtask.process_time  # 传递加工时间
                    )
                    
                    # 将TrackTask添加到对应的Subtask的track_tasks列表中
                    subtask.track_tasks.append(track_task)
                    
                    track_tasks.append(track_task)
                    # 注册到注册表
                    self.registry.register_object(track_task, f"track_task_{subtask.pono}_{track_task.track_id}", 'track_task')
                
                # 标记子任务为已下发（规划成功）
                subtask.dispatched = True
                # 将成功规划的子任务添加到列表
                planned_subtasks.append(subtask)
        
        return track_tasks, planned_subtasks
    
    def _find_path_bfs(self, subtask: Subtask) -> List[Dict]:
        """使用BFS算法为子任务寻找路径
        
        Args:
            subtask: 子任务对象
            
        Returns:
            List[Dict]: 路径解决方案列表，每个元素包含路径段信息
        """
        # 获取起始工位和目标工位
        start_station = subtask.start_station
        end_station = subtask.end_station
        
        # 检查起始工位和目标工位是否有相邻节点
        if start_station not in self.station_adjacent_nodes:
            raise ValueError(f"起始工位 {start_station} 没有相邻节点映射")
        if end_station not in self.station_adjacent_nodes:
            raise ValueError(f"目标工位 {end_station} 没有相邻节点映射")
        
        # 获取起始工位和目标工位的相邻节点
        start_adjacent_nodes = self.station_adjacent_nodes[start_station]
        end_adjacent_nodes = self.station_adjacent_nodes[end_station]
        
        if not start_adjacent_nodes:
            raise ValueError(f"起始工位 {start_station} 没有相邻节点")
        if not end_adjacent_nodes:
            raise ValueError(f"目标工位 {end_station} 没有相邻节点")
        
        solution = []
        
        # 初始化所有节点
        for node in self.nodes.values():
            node.has_visited = False
            node.prev_node = None
        
        # BFS队列
        queue = []
        
        # 将起始工位的相邻节点加入队列
        for start_node_name in start_adjacent_nodes:
            start_node = self.nodes.get(start_node_name)
            if start_node and not start_node.is_occupied:
                start_node.has_visited = True
                queue.append(start_node)
        
        # 目标节点
        target_node = None
        
        # BFS遍历
        while queue:
            current_node = queue.pop(0)
            
            # 检查是否到达目标工位的相邻节点
            if current_node.name in end_adjacent_nodes:
                target_node = current_node
                break
            
            # 遍历当前节点的连接节点
            if not current_node.connected_nodes:
                raise ValueError(f"节点 {current_node.name} 没有连接关系，无法进行BFS遍历")
            
            for neighbor_name in current_node.connected_nodes:
                neighbor_node = self.nodes.get(neighbor_name)
                if neighbor_node and not neighbor_node.has_visited and not neighbor_node.is_occupied:
                    neighbor_node.has_visited = True
                    neighbor_node.prev_node = current_node
                    queue.append(neighbor_node)
        
        # 如果找到目标节点，生成路径
        if target_node:
            # 回溯路径
            path = []
            current = target_node
            while current:
                path.append(current.name)
                current = current.prev_node
            
            # 反转路径，从起始节点到目标节点
            path.reverse()
            
            # 生成路径段
            if len(path) == 1:
                # 只有一个节点的情况：直接从起始工位到结束工位
                current_node_name = path[0]
                current_vehicle = self.registry.get_object(current_node_name, 'vehicle')
                
                # 通过registry获取track对象
                track = self.registry.get_object(current_vehicle.track_id, 'track')
                if track:
                    # 检查车辆是否能直接到达起始和结束工位
                    start_station_obj = track.get_station_by_id(start_station)
                    end_station_obj = track.get_station_by_id(end_station)
                    
                    if start_station_obj and end_station_obj:
                        solution.append({
                            'start': start_station,
                            'end': end_station,
                            'track': current_vehicle.track_id,
                            'vehicle': current_vehicle.vehicle_id
                        })
                    else:
                        # 车辆无法直接到达两个工位，返回空列表
                        print(f"⚠️  车辆 {current_vehicle.vehicle_id} 无法直接从 {start_station} 到达 {end_station}，跳过本轮规划")
                        return []
                else:
                    # 无法获取轨道对象，返回空列表
                    print(f"⚠️  无法获取轨道 {current_vehicle.track_id}，跳过本轮规划")
                    return []
            else:
                # 多个节点的情况
                for i in range(len(path)):
                    current_node_name = path[i]
                    current_vehicle = self.registry.get_object(current_node_name, 'vehicle')
                    
                    if i == 0:
                        # 第一个节点：从起始工位到与下一个节点的共同工位
                        next_node_name = path[i + 1]
                        next_vehicle = self.registry.get_object(next_node_name, 'vehicle')
                        common_station = self._get_common_reachable_stations(current_vehicle, next_vehicle)
                        
                        solution.append({
                            'start': start_station,
                            'end': common_station,
                            'track': current_vehicle.track_id,
                            'vehicle': current_vehicle.vehicle_id
                        })
                    elif i == len(path) - 1:
                        # 最后一个节点：从与前一个节点的共同工位到结束工位
                        prev_node_name = path[i - 1]
                        prev_vehicle = self.registry.get_object(prev_node_name, 'vehicle')
                        common_station = self._get_common_reachable_stations(prev_vehicle, current_vehicle)
                        
                        solution.append({
                            'start': common_station,
                            'end': end_station,
                            'track': current_vehicle.track_id,
                            'vehicle': current_vehicle.vehicle_id
                        })
                    else:
                        # 中间节点：从与前一个节点的共同工位到与下一个节点的共同工位
                        prev_node_name = path[i - 1]
                        next_node_name = path[i + 1]
                        prev_vehicle = self.registry.get_object(prev_node_name, 'vehicle')
                        next_vehicle = self.registry.get_object(next_node_name, 'vehicle')
                        prev_common_station = self._get_common_reachable_stations(prev_vehicle, current_vehicle)
                        next_common_station = self._get_common_reachable_stations(current_vehicle, next_vehicle)
                        
                        solution.append({
                            'start': prev_common_station,
                            'end': next_common_station,
                            'track': current_vehicle.track_id,
                            'vehicle': current_vehicle.vehicle_id
                        })
        else:
            # 无法找到路径，返回空列表
            print(f"⚠️  无法找到从 {start_station} 到 {end_station} 的路径，跳过本轮规划")
            return []
        
        return solution
    
    def _get_common_reachable_stations(self, vehicle1, vehicle2) -> str:
        """获取两个车辆共同可达的工位
        
        Args:
            vehicle1: 第一辆车
            vehicle2: 第二辆车
            
        Returns:
            str: 共同可达的工位ID
        """
        # 获取两辆车的轨道
        track1 = self.registry.get_object(vehicle1.track_id, 'track')
        track2 = self.registry.get_object(vehicle2.track_id, 'track')
        
        if not track1 or not track2:
            return ""  # 返回空字符串表示未找到
        
        # 获取两辆轨道上的所有工位ID
        stations1 = set()
        for station in track1.stations:
            stations1.add(station.station_id)
            
        stations2 = set()
        for station in track2.stations:
            stations2.add(station.station_id)
        
        # 获取共同的工位
        common_stations = stations1.intersection(stations2)
        
        if common_stations:
            return next(iter(common_stations))  # 返回第一个共同工位
        
        return ""  # 未找到共同工位
        
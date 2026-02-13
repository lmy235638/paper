from typing import List, Optional
from datetime import datetime
from src.utils.task_generator import ProductionPlan, str_to_time
from src.entities.pono_task import PonoTask
from src.entities.goods import Goods
from src.core.registry import EnvRegistry


class TaskDispatcher:
    """任务下发器，负责根据时间下发任务"""
    def __init__(self, tasks, registry: EnvRegistry):
        self.tasks: List[PonoTask] = []                 # 所有任务
        self.undispatched_tasks: List[PonoTask] = []    # 未下发任务
        self.dispatched_tasks: List[PonoTask] = []      # 已下发任务
        self.registry = registry  # 环境注册表引用
        
        # 将tasks字典转换为PonoTask对象
        self._create_tasks_from_dict_list(tasks)
    
    def _create_tasks_from_dict_list(self, task_data):
        """从任务字典列表创建PonoTask对象"""
        try:
            # 创建PonoTask对象并存储
            for task_dict in task_data:
                # 解析时间信息
                time_info = task_dict.get("time_info")
                duration_info = task_dict.get("duration_info")
                transport_info = task_dict.get("transport_info")
                
                task = PonoTask(
                    pono=task_dict["pono"],
                    start_ld=task_dict["start_ld"],
                    end_cc=task_dict["end_cc"],
                    refine_process=task_dict["refine_process"],
                    lf_station=task_dict["lf_station"],
                    rh_station=task_dict["rh_station"],
                    
                    # 时间信息
                    task_start_time=str_to_time(time_info["task_start"]),
                    task_end_time=str_to_time(time_info["task_end"]),
                    
                    # 精炼时间信息
                    lf_start_time=str_to_time(time_info["lf_start"]) if time_info["lf_start"] else None,
                    lf_end_time=str_to_time(time_info["lf_end"]) if time_info["lf_end"] else None,
                    rh_start_time=str_to_time(time_info["rh_start"]) if time_info["rh_start"] else None,
                    rh_end_time=str_to_time(time_info["rh_end"]) if time_info["rh_end"] else None,
                    
                    # 工序耗时信息
                    lf_duration=duration_info["lf_duration"],
                    rh_duration=duration_info["rh_duration"],
                    
                    # 转运时间信息
                    ld_to_lf_duration=transport_info["ld_to_lf"],
                    ld_to_rh_duration=transport_info["ld_to_rh"],
                    lf_to_rh_duration=transport_info["lf_to_rh"],
                    lf_to_cc_duration=transport_info["lf_to_cc"],
                    rh_to_cc_duration=transport_info["rh_to_cc"]
                )
                
                self.tasks.append(task)
                self.undispatched_tasks.append(task)
            
            print(f"✅ Successfully loaded {len(self.tasks)} tasks from external data")
        except Exception as e:
            print(f"❌ Error loading tasks: {e}")
    
    def dispatch_tasks(self, current_time: datetime) -> List[PonoTask]:
        """根据当前时间下发任务
        
        Args:
            current_time: 当前时间（datetime对象）
            
        Returns:
            List[Task]: 下发的任务列表
        """
        dispatched = []
        remaining = []
        
        # 检查每个未下发的任务
        for task in self.undispatched_tasks:
            # 直接比较datetime对象
            if task.get_task_start_time() <= current_time:
                # 任务到达下发时间，添加到下发列表
                dispatched.append(task)
                self.dispatched_tasks.append(task)
                
                # 注册任务到环境注册表
                self.registry.register_object(task, f"pono_{task.pono}", "task")
                
                # 创建货物对象
                goods = Goods(
                    pono=task.pono,
                    goods_id=f"goods_{task.pono}",
                    start_ld=task.start_ld,
                    end_cc=task.end_cc,
                    refine_process=task.refine_process
                )
                
                # 注册货物到环境注册表
                self.registry.register_object(goods, goods.goods_id, "goods")
                
                # 将货物添加到起始工位的goods_list中
                # 直接根据工位ID获取工位对象
                workstation = self.registry.get_workstation_by_id(task.start_ld)
                if workstation:
                    # 调用工位的add_goods方法添加货物，传递当前时间
                    workstation.add_goods(goods, current_time)
                else:
                    raise ValueError(f"未找到起始工位 {task.start_ld}，货物 {goods} 未添加")
            else:
                # 任务未到达下发时间，保留在未下发列表
                remaining.append(task)
        
        # 更新未下发任务列表
        self.undispatched_tasks = remaining
        
        if dispatched:
            # 打印已下发任务信息，使用HH:MM:SS格式显示时间
            current_time_str = current_time.strftime("%H:%M:%S")
            print(f"📤 Dispatched {len(dispatched)} tasks at time {current_time_str}, 任务PONO编号: {[task.pono for task in dispatched]}")
        
        return dispatched
    
    def get_all_tasks(self) -> List[PonoTask]:
        """获取所有任务"""
        return self.tasks
    
    def get_undispatched_tasks(self) -> List[PonoTask]:
        """获取未下发的任务"""
        return self.undispatched_tasks
    
    def get_dispatched_tasks(self) -> List[PonoTask]:
        """获取已下发的任务"""
        return self.dispatched_tasks

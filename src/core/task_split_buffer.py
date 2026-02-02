from typing import List, Dict, Optional
from datetime import datetime, timedelta
from src.entities.pono_task import PonoTask
from src.entities.subtask import Subtask
from src.core.registry import EnvRegistry


class TaskSplitBuffer:
    """任务拆分缓冲，将PonoTask拆分成转运子任务并控制下发时机"""
    
    def __init__(self, registry: EnvRegistry):
        self.registry = registry
        self.buffer: Dict[str, Subtask] = {}  # 存储已生成的子任务，key为subtask_id
        self.subtask_status: Dict[int, Dict[str, dict]] = {}  # 存储每个pono的子任务状态，格式: {pono: {subtask_type: {generated: bool, dispatched: bool, completed: bool}}}
        
    def scan(self, current_time: datetime) -> List[Subtask]:
        """扫描所有已注册的PonoTask任务，将到达分解时间的任务拆分成子任务
        
        Args:
            current_time: 当前时间
            
        Returns:
            List[Subtask]: 新生成的子任务列表
        """
        new_subtasks: List[Subtask] = []
        
        all_tasks = self.registry.get_tasks()
        
        for pono_task in all_tasks:
            # print(f"检查任务: PONO={pono_task.pono}, 精炼工艺={pono_task.refine_process}")
            if not isinstance(pono_task, PonoTask):
                continue
                
            subtask_configs = self._get_subtask_configs(pono_task)
            # print(f"  生成子任务配置: {[config['type'] for config in subtask_configs]}")
            
            # 确保该pono的子任务状态存在
            if pono_task.pono not in self.subtask_status:
                self.subtask_status[pono_task.pono] = {}
            
            for i, subtask_config in enumerate(subtask_configs):
                subtask_type = subtask_config['type']
                
                # 初始化子任务状态
                if subtask_type not in self.subtask_status[pono_task.pono]:
                    # 初始状态：未生成，未下发，未完成
                    self.subtask_status[pono_task.pono][subtask_type] = {
                        'generated': getattr(pono_task, subtask_config['dispatched_flag'], False),  # 这里暂时使用dispatched_flag来兼容旧数据
                        'dispatched': False,
                        'completed': False
                    }
                
                # 获取当前子任务状态
                subtask_state = self.subtask_status[pono_task.pono][subtask_type]
                # print(f"  检查子任务: 类型={subtask_type}, 已生成={subtask_state['generated']}, 已下发={subtask_state['dispatched']}")
                
                # 检查是否已经生成
                if subtask_state['generated']:
                    continue
                    
                # 检查是否满足生成条件
                can_generate = self._can_generate(pono_task, subtask_config, subtask_configs, i, current_time)
                # print(f"  能否生成: {can_generate}")
                if can_generate:
                    subtask = self._create_subtask(pono_task, subtask_config, current_time)
                    if subtask:
                        subtask_id = f"subtask_{pono_task.pono}_{subtask_type}"
                        self.buffer[subtask_id] = subtask
                        self.registry.register_object(subtask, subtask_id, 'subtask')
                        
                        # 更新子任务状态
                        subtask_state['generated'] = True
                        setattr(pono_task, subtask_config['dispatched_flag'], True)  # 兼容旧代码
                        
                        new_subtasks.append(subtask)
        
        if new_subtasks:
            # 打印已分解任务信息，使用HH:MM:SS格式显示时间
            current_time_str = current_time.strftime("%H:%M:%S")
            pono_list = [subtask.pono for subtask in new_subtasks]
            subtask_types = [subtask.type for subtask in new_subtasks]
            print(f"📝 分解任务 {len(new_subtasks)} 个，时间 {current_time_str}，PONO编号: {list(set(pono_list))}，子任务类型: {subtask_types}")
        
        return new_subtasks
    
    def _get_subtask_configs(self, pono_task: PonoTask) -> List[Dict]:
        """根据精炼工艺类型获取子任务配置列表"""
        configs = []
        refine_process = pono_task.refine_process
        
        if refine_process == "LF精炼":
            if pono_task.start_ld and pono_task.lf_station and pono_task.ld_to_lf_duration is not None:
                configs.append({
                    'type': 'ld_to_lf',
                    'start_station': pono_task.start_ld,
                    'end_station': pono_task.lf_station,
                    'start_time': pono_task.task_start_time,
                    'duration': pono_task.ld_to_lf_duration,
                    'dispatched_flag': 'ld_to_lf_dispatched',
                    'next_stage': 'lf'
                })
            if pono_task.lf_station and pono_task.end_cc and pono_task.lf_to_cc_duration is not None:
                configs.append({
                    'type': 'lf_to_cc',
                    'start_station': pono_task.lf_station,
                    'end_station': pono_task.end_cc,
                    'start_time': pono_task.lf_end_time,
                    'duration': pono_task.lf_to_cc_duration,
                    'dispatched_flag': 'lf_to_cc_dispatched',
                    'next_stage': 'cc'
                })
                
        elif refine_process == "RH精炼":
            if pono_task.start_ld and pono_task.rh_station and pono_task.ld_to_rh_duration is not None:
                configs.append({
                    'type': 'ld_to_rh',
                    'start_station': pono_task.start_ld,
                    'end_station': pono_task.rh_station,
                    'start_time': pono_task.task_start_time,
                    'duration': pono_task.ld_to_rh_duration,
                    'dispatched_flag': 'ld_to_rh_dispatched',
                    'next_stage': 'rh'
                })
            if pono_task.rh_station and pono_task.end_cc and pono_task.rh_to_cc_duration is not None:
                configs.append({
                    'type': 'rh_to_cc',
                    'start_station': pono_task.rh_station,
                    'end_station': pono_task.end_cc,
                    'start_time': pono_task.rh_end_time,
                    'duration': pono_task.rh_to_cc_duration,
                    'dispatched_flag': 'rh_to_cc_dispatched',
                    'next_stage': 'cc'
                })
                
        elif refine_process == "LF+RH双重精炼":
            if pono_task.start_ld and pono_task.lf_station and pono_task.ld_to_lf_duration is not None:
                configs.append({
                    'type': 'ld_to_lf',
                    'start_station': pono_task.start_ld,
                    'end_station': pono_task.lf_station,
                    'start_time': pono_task.task_start_time,
                    'duration': pono_task.ld_to_lf_duration,
                    'dispatched_flag': 'ld_to_lf_dispatched',
                    'next_stage': 'lf'
                })
            if pono_task.lf_station and pono_task.rh_station and pono_task.lf_to_rh_duration is not None:
                configs.append({
                    'type': 'lf_to_rh',
                    'start_station': pono_task.lf_station,
                    'end_station': pono_task.rh_station,
                    'start_time': pono_task.lf_end_time,
                    'duration': pono_task.lf_to_rh_duration,
                    'dispatched_flag': 'lf_to_rh_dispatched',
                    'next_stage': 'rh'
                })
            if pono_task.rh_station and pono_task.end_cc and pono_task.rh_to_cc_duration is not None:
                configs.append({
                    'type': 'rh_to_cc',
                    'start_station': pono_task.rh_station,
                    'end_station': pono_task.end_cc,
                    'start_time': pono_task.rh_end_time,
                    'duration': pono_task.rh_to_cc_duration,
                    'dispatched_flag': 'rh_to_cc_dispatched',
                    'next_stage': 'cc'
                })
        
        return configs
    
    def _can_generate(self, pono_task: PonoTask, subtask_config: Dict, all_subtask_configs: List[Dict], current_index: int, current_time: datetime) -> bool:
        """检查子任务是否满足生成条件
        
        Args:
            pono_task: PonoTask对象
            subtask_config: 当前子任务配置
            all_subtask_configs: 所有子任务配置列表
            current_index: 当前子任务在列表中的索引
            current_time: 当前时间
            
        Returns:
            bool: 是否可以生成
        """
        # 检查子任务的开始时间是否已到
        start_time = subtask_config['start_time']
        if start_time is None or start_time > current_time:
            return False
        
        # 检查前一个子任务是否存在且已完成
        if current_index > 0:
            # 获取前一个子任务配置
            prev_subtask_config = all_subtask_configs[current_index - 1]
            prev_subtask_type = prev_subtask_config['type']
            
            # 获取前一个子任务状态
            if prev_subtask_type not in self.subtask_status[pono_task.pono]:
                return False
            
            prev_subtask_state = self.subtask_status[pono_task.pono][prev_subtask_type]
            
            # 前一个子任务必须已生成且已完成
            if not prev_subtask_state['generated'] or not prev_subtask_state['completed']:
                return False
        
        return True
    
    def mark_subtask_completed(self, pono: int, subtask_type: str) -> bool:
        """标记子任务为已完成
        
        Args:
            pono: 任务编号
            subtask_type: 子任务类型
            
        Returns:
            bool: 标记是否成功
        """
        if pono in self.subtask_status and subtask_type in self.subtask_status[pono]:
            self.subtask_status[pono][subtask_type]['completed'] = True
            # print(f"标记子任务为已完成: PONO={pono}, 类型={subtask_type}")
            return True
        return False
    
    def _create_subtask(self, pono_task: PonoTask, subtask_config: Dict, current_time: datetime) -> Optional[Subtask]:
        """创建Subtask实例"""
        try:
            start_time = subtask_config['start_time']
            duration = subtask_config['duration']
            
            if start_time is None or duration is None:
                # print(f"跳过创建子任务: PONO={pono_task.pono}, 类型={subtask_config['type']}, start_time或duration为None")
                return None
            
            end_time = start_time + timedelta(minutes=duration)
            
            return Subtask(
                pono=pono_task.pono,
                start_time=start_time,
                end_time=end_time,
                start_station=subtask_config['start_station'],
                end_station=subtask_config['end_station'],
                type=subtask_config['type'],
                generate_time=current_time,
                process_time=duration
            )
        except Exception as e:
            # print(f"Error creating subtask for PONO {pono_task.pono}: {e}")
            return None
    
    def get_buffered_subtasks(self) -> List[Subtask]:
        """获取buffer中存储的所有子任务"""
        return list(self.buffer.values())
    
    def get_subtask_by_id(self, subtask_id: str) -> Optional[Subtask]:
        """根据ID获取buffer中的子任务"""
        return self.buffer.get(subtask_id)
    
    def mark_subtask_completed(self, pono: int, subtask_type: str) -> bool:
        """标记子任务为已完成
        
        Args:
            pono: 任务编号
            subtask_type: 子任务类型
            
        Returns:
            bool: 标记是否成功
        """
        if pono in self.subtask_status and subtask_type in self.subtask_status[pono]:
            self.subtask_status[pono][subtask_type]['completed'] = True
            # print(f"标记子任务为已完成: PONO={pono}, 类型={subtask_type}")
            return True
        return False
    
    def update_subtask_status(self, subtask_id: str, completed: bool = None, generated: bool = None, dispatched: bool = None) -> bool:
        """更新子任务状态
        
        Args:
            subtask_id: 子任务ID
            completed: 是否完成
            generated: 是否已生成
            dispatched: 是否已下发
            
        Returns:
            bool: 更新是否成功
        """
        if subtask_id not in self.buffer:
            return False
        
        # 更新buffer中的子任务状态
        subtask = self.buffer[subtask_id]
        if completed is not None:
            subtask.completed = completed
        if dispatched is not None:
            subtask.dispatched = dispatched
        
        # 更新内部状态记录
        # 从subtask_id中解析pono和type
        parts = subtask_id.split('_')
        if len(parts) >= 3:
            pono = int(parts[1])
            subtask_type = '_'.join(parts[2:])
            if pono in self.subtask_status and subtask_type in self.subtask_status[pono]:
                if completed is not None:
                    self.subtask_status[pono][subtask_type]['completed'] = completed
                if generated is not None:
                    self.subtask_status[pono][subtask_type]['generated'] = generated
                if dispatched is not None:
                    self.subtask_status[pono][subtask_type]['dispatched'] = dispatched
        
        return True
    
    def get_generated_subtasks(self) -> List[Subtask]:
        """获取所有已生成的子任务
        
        Returns:
            List[Subtask]: 所有已生成的子任务列表
        """
        generated_subtasks = []
        for subtask in self.buffer.values():
            generated_subtasks.append(subtask)
        return generated_subtasks

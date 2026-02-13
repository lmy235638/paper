from src.core.registry import EnvRegistry


class TaskScanner:
    """任务扫描器，用于扫描轨道级子任务的完成情况
    
    当轨道级子任务完成时，将其上级任务标记为阶段完成
    """
    
    def __init__(self, registry: EnvRegistry):
        self.registry = registry
    
    def scan(self, current_time):    
        # print(f"\n=== 任务扫描器: 开始扫描 ===")
        # 从registry中获取所有已完成的TrackTask
        completed_track_tasks = self._get_completed_track_tasks()
        # print(f"  找到 {len(completed_track_tasks)} 个已完成的TrackTask")
        
        # 收集需要处理的tracktask和对应的subtask
        # 使用字典来确保每个subtask只被处理一次
        subtask_to_tracktasks = {}
        
        for track_task in completed_track_tasks:
            # 找到对应的Subtask
            subtask = self._find_subtask(track_task)
            
            if subtask:
                # 使用subtask的pono和type作为键（可哈希）
                subtask_key = (subtask.pono, subtask.type)
                # 将tracktask添加到对应subtask的列表中
                if subtask_key not in subtask_to_tracktasks:
                    subtask_to_tracktasks[subtask_key] = {
                        'subtask': subtask,
                        'tracktasks': []
                    }
                subtask_to_tracktasks[subtask_key]['tracktasks'].append(track_task)
            else:
                # 即使找不到Subtask，也移除已完成的TrackTask
                self._remove_task(f"track_task_{track_task.pono}_{track_task.track_id}", 'track_task')
        
        # 处理每个subtask及其对应的tracktasks
        print(f"  开始处理收集到的subtask: 共 {len(subtask_to_tracktasks)} 个")
        for data in subtask_to_tracktasks.values():
            subtask = data['subtask']
            tracktasks = data['tracktasks']
            
            # 检查该subtask的所有tracktask是否都已完成
            all_tracktasks_completed = all(tt.is_completed() for tt in subtask.track_tasks)
            
            # 只有当所有tracktask都已完成时，才标记subtask为已完成
            if all_tracktasks_completed:
                # 标记Subtask为已完成
                self._mark_subtask_completed(subtask)
                
                # 更新PonoTask的相关信息
                self._update_pono_task(subtask, current_time)
                
                # 从registry中移除已完成的tracktasks和subtask
                for track_task in tracktasks:
                    self._remove_task(f"track_task_{track_task.pono}_{track_task.track_id}", 'track_task')
                
                # 移除subtask（只移除一次）
                self._remove_task(f"subtask_{subtask.pono}_{subtask.type}", 'subtask')
    
    def _get_completed_track_tasks(self):
        """获取所有已完成的TrackTask
        
        Returns:
            list: 已完成的TrackTask列表
        """
        return [task for task in self.registry.get_objects_by_type('track_task') if task.is_completed()]
    
    def _find_subtask(self, track_task):
        """根据TrackTask找到对应的Subtask"""
        # 根据id直接从registry中获取Subtask
        subtask_id = f"subtask_{track_task.pono}_{track_task.type}"
        return self.registry.get_object(subtask_id, 'subtask')
    
    def _mark_subtask_completed(self, subtask):
        """标记Subtask为已完成
        
        Args:
            subtask: Subtask对象
        """
        # 标记Subtask为已完成
        subtask.completed = True
        subtask.dispatched = True  # 同时标记为已下发
        
        print(f"  子任务 {subtask.pono} 类型 {subtask.type} 已标记为完成")
        
        # 更新task_split_buffer中的状态
        env = self.registry.get_env()
        env.task_split_buffer.mark_subtask_completed(subtask.pono, subtask.type)
    
    def _update_pono_task(self, subtask, current_time):
        """更新PonoTask的相关信息
        
        Args:
            subtask: Subtask对象
            current_time: 当前时间
        """
        # 从registry中获取所有PonoTask
        for pono_task in self.registry.get_objects_by_type('task'):
            if pono_task.pono == subtask.pono:
                # 根据子任务类型更新PonoTask的相关信息
                subtask_type = subtask.type
                
                # 更新到达和离开时间
                if subtask_type == 'ld_to_lf':
                    pono_task.actual_lf_arrive_time = current_time
                elif subtask_type == 'ld_to_rh':
                    pono_task.actual_rh_arrive_time = current_time
                elif subtask_type == 'lf_to_rh':
                    pono_task.actual_rh_arrive_time = current_time
                    pono_task.lf_completed = True
                elif subtask_type == 'lf_to_cc':
                    pono_task.actual_cc_arrive_time = current_time
                    pono_task.lf_completed = True
                elif subtask_type == 'rh_to_cc':
                    pono_task.actual_cc_arrive_time = current_time
                    pono_task.rh_completed = True
                
                # 检查是否所有任务都已完成
                if pono_task.lf_completed and pono_task.rh_completed:
                    pono_task.all_completed = True
                    print(f"  任务 {pono_task.pono} 已全部完成")
                
                print(f"  更新任务 {pono_task.pono} 的状态: {subtask_type} 阶段完成")
                break
    
    def _remove_task(self, task_id, task_type):
        """从registry中移除任务
        
        Args:
            task_id: 任务ID
            task_type: 任务类型
        """
        if self.registry.unregister_object(task_id, task_type):
            print(f"  从registry中移除已完成的{task_type}: {task_id}")

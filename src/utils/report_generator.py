from datetime import datetime, timedelta


def generate_report(env):
    """生成仿真报告
    
    Args:
        env: 环境对象
    """
    print("\n" + "="*80)
    print("                            仿真报告")
    print("="*80)
    
    # 获取所有货物
    all_goods = env.registry.get_objects_by_type('goods')
    print(f"\n总货物数量: {len(all_goods)}")
    
    # 打印每个货物的完成情况
    print("\n货物任务完成情况:")
    print("-"*80)
    print(f"{'货物ID':<15} {'起始工位':<10} {'结束工位':<10} {'状态':<10} {'完成时间':<15}")
    print("-"*80)
    
    completed_count = 0
    for goods in all_goods:
        # 检查货物是否到达CC工位（通过station_times记录）
        cc_station_reached = False
        completion_time = "-"
        
        if hasattr(goods, 'station_times'):
            for station_id, times in goods.station_times.items():
                if 'CC' in station_id and 'in_time' in times and times['in_time'] is not None:
                    cc_station_reached = True
                    completion_time = times['in_time'].strftime('%H:%M:%S')
                    break
        
        if cc_station_reached:
            status = "已完成"
            completed_count += 1
        else:
            status = "进行中"
        
        print(f"{goods.goods_id:<15} {goods.start_ld:<10} {goods.end_cc:<10} {status:<10} {completion_time:<15}")
        
        # 打印每个货物的工位时间记录
        if hasattr(goods, 'station_times') and goods.station_times:
            print(f"{'':<15} {'':<10} {'':<10} {'':<10} {'工位时间记录':<15}")
            for station_id, times in goods.station_times.items():
                in_time = times.get('in_time', '-')
                out_time = times.get('out_time', '-')
                if isinstance(in_time, datetime):
                    in_time_str = in_time.strftime('%H:%M:%S')
                else:
                    in_time_str = str(in_time)
                if isinstance(out_time, datetime):
                    out_time_str = out_time.strftime('%H:%M:%S')
                else:
                    out_time_str = str(out_time)
                print(f"{'':<15} {'':<10} {'':<10} {'':<10} {station_id:<15} 到达: {in_time_str}, 离开: {out_time_str}")
    
    print("-"*80)
    print(f"\n已完成任务: {completed_count}/{len(all_goods)}")
    
    print("="*80)


def get_latest_task_end_time(env):
    """获取最晚的任务结束时间
    
    Args:
        env: 环境对象
    
    Returns:
        datetime: 最晚的任务结束时间
    """
    latest_time = None
    task_dispatcher = env.task_dispatcher
    if task_dispatcher:
        for task in task_dispatcher.tasks:
            task_end_time = task.get_task_end_time()
            if latest_time is None or task_end_time > latest_time:
                latest_time = task_end_time
    return latest_time


def check_all_tasks_completed(env):
    """检查是否所有任务都已完成
    
    Args:
        env: 环境对象
    
    Returns:
        bool: 如果所有任务都已完成返回True，否则返回False
    """
    all_goods = env.registry.get_objects_by_type('goods')
    for goods in all_goods:
        # 检查货物是否到达CC工位（通过station_times记录）
        cc_station_reached = False
        for station_id in goods.station_times:
            if 'CC' in station_id and 'in_time' in goods.station_times[station_id]:
                cc_station_reached = True
                break
        if not cc_station_reached:
            return False
    return True

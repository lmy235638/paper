import argparse
from datetime import timedelta
from src.core.env import Env
from src.core.simulator import Simulator
from src.core.report_generator import generate_report, get_latest_task_end_time, check_all_tasks_completed
from src.utils.file_utils import load_config, load_tasks
from src.utils.analyze_results import analyze_simulation_results


if __name__ == "__main__":
    # 添加命令行参数
    parser = argparse.ArgumentParser(description="钢铁厂物流仿真系统")
    parser.add_argument('--no-render', action='store_true', help='禁用渲染')
    args = parser.parse_args()
    
    # 加载配置和任务
    config = load_config('src/config/env.yaml')
    tasks = load_tasks('data/tasks.json')
    
    # 创建环境
    env = Env(config, tasks)
    env.reset()
    
    # 创建仿真器
    render_mode = None if args.no_render else "human"
    simulator = Simulator(render_mode=render_mode)
    simulator.set_env(env)
    
    print("仿真启动...")
    if not args.no_render:
        print("按ESC键退出...")
    
    # 获取最晚任务结束时间
    latest_task_end_time = get_latest_task_end_time(env)
    if latest_task_end_time:
        # 计算超时时间（最晚任务时间+2小时）
        timeout_time = latest_task_end_time + timedelta(hours=2)
    else:
        raise ValueError("未找到任何任务结束时间")
    
    # 运行仿真循环
    running = True
    while running:
        # 执行一步仿真
        simulator.step()
        
        # 检查是否需要退出
        if simulator.check_for_exit():
            running = False
        
        # 检查是否所有任务完成
        if check_all_tasks_completed(env):
            print("\n所有任务已完成，仿真结束")
            running = False
        
        # 检查是否超时
        current_time = env.registry.get_time()
        if latest_task_end_time and current_time > timeout_time:
            print("\n仿真超时，超过最晚任务时间2小时，仿真结束")
            running = False
    
    # 生成报告
    generate_report(env)
    
    # 关闭仿真器和渲染器
    simulator.close()
    print("仿真结束")
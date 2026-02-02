from src.core.env import Env
from src.core.simulator import Simulator
from src.utils.file_utils import load_config, load_tasks


if __name__ == "__main__":
    # 加载配置和任务
    config = load_config('src/config/env.yaml')
    tasks = load_tasks('data/tasks.json')
    
    # 创建环境
    env = Env(config, tasks)
    env.reset()
    
    # 创建仿真器（带渲染）
    simulator = Simulator(render_mode="human")
    simulator.set_env(env)
    
    print("仿真启动，按ESC键退出...")
    
    # 运行仿真循环
    running = True
    while running:
        # 执行一步仿真
        simulator.step()
        
        # 检查是否需要退出
        if simulator.check_for_exit():
            running = False
    
    # 关闭仿真器和渲染器
    simulator.close()
    print("仿真结束")
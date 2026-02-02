from src.visualization.renderer import RailRenderer
from typing import Optional

class Simulator:
    def __init__(self, render_mode: Optional[str] = None) -> None:
        self.render_mode = render_mode
        self.renderer = RailRenderer(render_mode)
        self.env = None
        
    def set_env(self, env):
        self.env = env
        self.renderer.set_registry(env.registry)
    
    def step(self) -> None:
        # 执行环境步骤
        if self.env is not None:
            self.env.step()
        
        # 渲染当前帧
        if self.render_mode is not None:
            self.renderer.render_frame()
            
    def check_for_exit(self) -> bool:
        """
        检查是否需要退出仿真
        
        Returns:
            如果需要退出，则返回True；否则返回False
        """
        return self.renderer.check_for_exit() if self.render_mode is not None else False
    
    def close(self) -> None:
        """
        关闭仿真器和渲染器
        """
        self.renderer.close()



import pygame
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional


class RailRenderer:
    """
    轨道运输环境渲染器
    
    负责将环境状态渲染为可视化动画，支持human和rgb_array两种渲染模式。
    采用30x30网格布局，自适应屏幕大小。
    """
    metadata = {
        "render_modes": ["human", "rgb_array"],
        "render_fps": 10,
    }
    
    def __init__(self, render_mode: Optional[str] = None):
        """
        初始化渲染器
        
        Args:
            render_mode: 渲染模式，可选值为"human"、"rgb_array"或None
        """
        self.render_mode = render_mode
        self.registry = None
        self.cell_size = None
        self.screen = None
        self.clock = None
        self.font = None
        self.COLORS = None
        
        # 固定30x30网格：x/y范围 0-29（共30单位）
        self.grid_size = 30  # 网格总单位数
        self.min_grid = 0  # 网格最小坐标
        self.max_grid = 29  # 网格最大坐标
        
        # 如果指定了渲染模式，则初始化渲染资源
        if self.render_mode is not None:
            self._render_init()
    
    def set_registry(self, registry):
        """
        设置环境注册表，用于获取需要渲染的对象
        
        Args:
            registry: EnvRegistry实例
        """
        self.registry = registry
    
    def _render_init(self) -> None:
        """
        初始化渲染资源（30x30网格专用，自适应屏幕）
        """
        # 初始化Pygame
        pygame.init()
        pygame.display.init()
        pygame.font.init()  # 初始化字体模块
        
        # 获取显示器最大分辨率（留10%边距，避免超出屏幕）
        display_info = pygame.display.Info()
        max_display_w = display_info.current_w * 0.9
        max_display_h = display_info.current_h * 0.9
        
        # 自动调整cell_size，确保30x30网格完整显示在屏幕内
        self.cell_size = int(min(
            max_display_w / (self.max_grid - self.min_grid + 2),  # 按宽度适配
            max_display_h / (self.max_grid - self.min_grid + 2)  # 按高度适配
        ))
        
        # 确保cell_size不小于最小值（避免网格过小导致元素看不清）
        self.cell_size = max(self.cell_size, 10)  # 最小10像素/单位
        
        # 设置字体（根据单元格大小自适应）
        font_size = max(12, int(self.cell_size * 0.8))  # 字体大小不小于12
        self.font = pygame.font.SysFont(["SimHei", "WenQuanYi Micro Hei", "Heiti TC"], font_size)
        
        # 最终屏幕尺寸（30x30网格+右侧信息面板）
        grid_screen_w = (self.max_grid - self.min_grid + 2) * self.cell_size
        info_panel_w = 250  # 信息面板宽度
        final_screen_w = grid_screen_w + info_panel_w
        final_screen_h = (self.max_grid - self.min_grid + 2) * self.cell_size
        
        # 颜色定义（参照layout_visualizer.py的颜色方案）
        self.COLORS = {
            'background': (240, 240, 240),  # 浅灰背景
            'track_horizontal': (100, 150, 200),  # 蓝色横向轨道
            'track_vertical': (200, 150, 100),  # 橙色纵向轨道
            'vehicle_crane': (0, 0, 255),  # 蓝色起重机
            'vehicle_trolley': (0, 255, 0),  # 绿色台车
            'cargo': (255, 0, 0),  # 红色货物
            'station_process': (0, 255, 0),  # 绿色加工工位
            'station_interact': (255, 255, 0),  # 黄色交互工位
            'text': (0, 0, 0),  # 黑色文字
            'info_background': (220, 220, 220),  # 信息面板背景
            'processing_time': (255, 165, 0)  # 加工时间显示颜色
        }
        
        # 创建适配后的屏幕（30x30网格+右侧信息面板）
        self.screen = pygame.display.set_mode((final_screen_w, final_screen_h))
        pygame.display.set_caption("Rail Transport Environment")
        self.clock = pygame.time.Clock()
        
        # 保存网格和信息面板的尺寸
        self.grid_screen_w = grid_screen_w
        self.info_panel_w = info_panel_w
    
    def render_frame(self) -> Optional[np.ndarray]:
        """
        渲染一帧环境状态
        
        Returns:
            如果render_mode为"rgb_array"，则返回RGB数组；否则返回None
        """
        if self.render_mode is None or self.registry is None:
            return None
        
        # 清空屏幕
        self.screen.fill(self.COLORS['background'])
        
        # -------------------------- 1. 绘制轨道 --------------------------
        tracks = self.registry.get_tracks()
        for track in tracks:
            # 网格X坐标不变，Y坐标翻转：(max_grid - y) 转换左下角原点到Pygame坐标系
            adj_start_x = (track.start_point[0] + 1) * self.cell_size + self.cell_size // 2
            adj_start_y = (self.max_grid - track.start_point[1] + 1) * self.cell_size + self.cell_size // 2
            adj_end_x = (track.end_point[0] + 1) * self.cell_size + self.cell_size // 2
            adj_end_y = (self.max_grid - track.end_point[1] + 1) * self.cell_size + self.cell_size // 2
            
            line_width = 5 if self.cell_size >= 20 else int(self.cell_size * 0.25)
            
            # 选择轨道颜色
            if track.track_type == "horizontal":
                track_color = self.COLORS['track_horizontal']
            else:
                track_color = self.COLORS['track_vertical']
            
            pygame.draw.line(self.screen, track_color,
                             (adj_start_x, adj_start_y), (adj_end_x, adj_end_y), line_width)
            
            # 绘制轨道ID
            mid_x = (adj_start_x + adj_end_x) // 2
            mid_y = (adj_start_y + adj_end_y) // 2
            track_text = self.font.render(track.track_id, True, self.COLORS['text'])
            self.screen.blit(track_text, (mid_x - track_text.get_width() // 2, mid_y - track_text.get_height() // 2))
        
        # -------------------------- 2. 绘制工位 --------------------------
        workstations = self.registry.get_workstations()
        for station in workstations:
            adj_x = (station.pos[0] + 1) * self.cell_size + self.cell_size // 2
            adj_y = (self.max_grid - station.pos[1] + 1) * self.cell_size + self.cell_size // 2
            
            if station.station_type == "processing":
                radius = 15 if self.cell_size >= 30 else int(self.cell_size * 0.5)
                pygame.draw.circle(self.screen, self.COLORS['station_process'], (adj_x, adj_y), radius)
            else:
                square_size = 20 if self.cell_size >= 30 else int(self.cell_size * 0.67)
                pygame.draw.rect(self.screen, self.COLORS['station_interact'],
                                 (adj_x - square_size // 2, adj_y - square_size // 2, square_size, square_size))
            
            # 绘制工位ID
            station_text = self.font.render(station.station_id, True, self.COLORS['text'])
            self.screen.blit(station_text, (adj_x + 10, adj_y - station_text.get_height() // 2))
            
            # 绘制加工时间（如果正在加工）
            if hasattr(station, 'is_processing') and station.is_processing:
                process_text = self.font.render(f"加工中: {station.processing_timer}", True, self.COLORS['processing_time'])
                self.screen.blit(process_text, (adj_x - process_text.get_width() // 2, adj_y + 20))
        
        # -------------------------- 3. 绘制车辆 --------------------------
        vehicles = self.registry.get_vehicles()
        for vehicle in vehicles:
            adj_x = (vehicle.current_location[0] + 1) * self.cell_size + self.cell_size // 2
            adj_y = (self.max_grid - vehicle.current_location[1] + 1) * self.cell_size + self.cell_size // 2
            
            veh_size = int(self.cell_size * 0.8)
            
            # 选择车辆颜色
            if vehicle.vehicle_type == "crane":
                veh_color = self.COLORS['vehicle_crane']
            else:  # trolley
                veh_color = self.COLORS['vehicle_trolley']
            
            pygame.draw.rect(self.screen, veh_color,
                             (adj_x - veh_size // 2, adj_y - veh_size // 2, veh_size, veh_size))
            
            # 检查车辆是否有货物（使用goods属性）
            if hasattr(vehicle, 'goods') and vehicle.goods is not None:
                cargo_radius = int(veh_size * 0.3)
                pygame.draw.circle(self.screen, self.COLORS['cargo'],
                                   (adj_x, adj_y - veh_size // 2 - cargo_radius), cargo_radius)
            
            # 绘制车辆ID
            vehicle_text = self.font.render(vehicle.vehicle_id, True, self.COLORS['text'])
            self.screen.blit(vehicle_text, (adj_x + veh_size // 2 + 5, adj_y - vehicle_text.get_height() // 2))
            
            # 绘制车辆状态
            if hasattr(vehicle, 'status'):
                status_text = self.font.render(vehicle.status, True, self.COLORS['text'])
                self.screen.blit(status_text, (adj_x - status_text.get_width() // 2, adj_y + veh_size // 2 + 5))
        
        # -------------------------- 绘制当前时间 --------------------------
        current_time = self.registry.get_time()
        time_text = self.font.render(f"当前时间: {self.format_time(current_time)}", True, self.COLORS['text'])
        # 显示在屏幕左上角（留出10像素边距）
        self.screen.blit(time_text, (10, 10))
        
        # -------------------------- 绘制右侧信息面板 --------------------------
        self.draw_info_panel()
        
        pygame.display.flip()
        self.clock.tick(self.metadata["render_fps"])
        
        if self.render_mode == "rgb_array":
            return np.transpose(np.array(pygame.surfarray.pixels3d(self.screen)), axes=(1, 0, 2))
        return None
    
    def format_time(self, time: datetime) -> str:
        """
        将datetime对象转换为HH:MM:SS格式
        
        Args:
            time: datetime对象
            
        Returns:
            格式化的时间字符串
        """
        return time.strftime("%H:%M:%S")
    
    def draw_info_panel(self):
        """绘制右侧信息面板"""
        # 右侧面板背景
        right_panel_x = self.grid_screen_w
        pygame.draw.rect(self.screen, self.COLORS['info_background'], 
                         (right_panel_x, 0, self.info_panel_w, self.screen.get_height()))
        
        # 绘制标题
        title_font = pygame.font.SysFont(["SimHei", "WenQuanYi Micro Hei", "Heiti TC"], 16)
        title = title_font.render("轨道运输仿真", True, self.COLORS['text'])
        self.screen.blit(title, (right_panel_x + 20, 20))
        
        # 绘制统计信息
        info_lines = [
            f"轨道数量: {len(self.registry.get_tracks())} 条",
            f"车辆数量: {len(self.registry.get_vehicles())} 台",
            f"工位数量: {len(self.registry.get_workstations())} 个",
            f"当前时间: {self.format_time(self.registry.get_time())}",
            f"仿真速度: {self.metadata['render_fps']} FPS"
        ]
        
        for i, line in enumerate(info_lines):
            info_text = self.font.render(line, True, self.COLORS['text'])
            self.screen.blit(info_text, (right_panel_x + 20, 60 + i * 25))
        
        # 绘制图例
        legend_x = right_panel_x + 20
        legend_y = 200
        
        legend_title = self.font.render("图例", True, self.COLORS['text'])
        self.screen.blit(legend_title, (legend_x, legend_y))
        
        legend_items = [
            (self.COLORS['track_horizontal'], "横向轨道"),
            (self.COLORS['track_vertical'], "纵向轨道"),
            (self.COLORS['vehicle_crane'], "起重机"),
            (self.COLORS['vehicle_trolley'], "台车"),
            (self.COLORS['station_process'], "加工工位"),
            (self.COLORS['station_interact'], "交互工位"),
            (self.COLORS['cargo'], "货物"),
            (self.COLORS['processing_time'], "加工中")
        ]
        
        for i, (color, text) in enumerate(legend_items):
            # 绘制颜色块
            pygame.draw.rect(self.screen, color, 
                             (legend_x, legend_y + 30 + i * 30, 20, 20))
            # 绘制文字
            legend_item_text = self.font.render(text, True, self.COLORS['text'])
            self.screen.blit(legend_item_text, (legend_x + 30, legend_y + 30 + i * 30))
        
        # 绘制控制说明
        control_title = self.font.render("控制说明", True, self.COLORS['text'])
        self.screen.blit(control_title, (right_panel_x + 20, 450))
        
        control_lines = [
            "空格键: 暂停/继续",
            "上下键: 调整速度",
            "S键: 保存布局图",
            "ESC键: 退出"
        ]
        
        for i, line in enumerate(control_lines):
            control_text = self.font.render(line, True, self.COLORS['text'])
            self.screen.blit(control_text, (right_panel_x + 20, 480 + i * 25))
    
    def check_for_exit(self) -> bool:
        """
        检查是否有退出事件（如按ESC键或关闭窗口）
        
        Returns:
            如果需要退出，则返回True；否则返回False
        """
        if self.render_mode is None:
            return False
            
        for event in pygame.event.get():
            if event.type == pygame.QUIT:  # 窗口关闭事件
                return True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return True
        return False
    
    def close(self) -> None:
        """
        关闭渲染器，清理资源
        """
        if self.render_mode is not None:
            pygame.display.quit()
            pygame.quit()

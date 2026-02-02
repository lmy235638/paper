from enum import Enum, unique
from datetime import datetime

# 默认初始时间配置
DEFAULT_START_TIME = datetime(2026, 1, 1, 0, 0, 0)


# 车辆动作
@unique
class VehicleAction(Enum):
    STOP = 0
    MOVE_LEFT = 1
    MOVE_RIGHT = 2
    MOVE_UP = 3
    MOVE_DOWN = 4
    LOAD = 5
    UNLOAD = 6


# 轨道类型
@unique  # 确保枚举值唯一
class TrackType(Enum):
    HORIZONTAL = 0  # 横向轨道
    VERTICAL = 1  # 纵向轨道


# 车辆类型
@unique  # 确保枚举值唯一
class VehicleType(Enum):
    CRANE = 0  # 桥式起重机（横向轨道，移动x坐标）
    TROLLEY = 1  # 小车（纵向轨道，移动y坐标）


@unique
class VehicleStatus(Enum):
    IDLE = 0
    WORKING = 1
    WAITING = 2


# 工位类型
@unique
class StationType(Enum):
    PROCESS = 0
    INTERACT = 1


# 任务类型
@unique
class TaskType(Enum):
    TRANSPORT = 0  # 运输任务
    LOAD = 1  # 装载任务（拾取货物）
    UNLOAD = 2  # 卸载任务（放下货物）


@unique
class TaskStatus(Enum):
    PENDING = 0  # 等待分配
    ASSIGNED = 1  # 已分配
    COMPLETED = 2  # 已完成

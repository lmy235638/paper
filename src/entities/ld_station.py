from src.bases.base_workstation import Workstation
from typing import Tuple, List, Any
from src.core.registry import EnvRegistry


class LDStation(Workstation):
    """LD工位类：负责生成货物"""
    def __init__(self, station_id: str, pos: Tuple[int, int], station_type: str, connected_tracks=None, registry: EnvRegistry = None):
        super().__init__(station_id, pos, station_type, connected_tracks, registry)
    
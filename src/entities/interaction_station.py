from src.bases.base_workstation import Workstation
from typing import Tuple, List, Any, Set

from src.core.registry import EnvRegistry


class InteractionStation(Workstation):
    """交互工位类：负责货物的交接和转运"""

    def __init__(self, station_id: str, pos: Tuple[int, int], station_type: str, connected_tracks: Set[str] = None,
                 registry: EnvRegistry = None):
        super().__init__(station_id, pos, station_type, connected_tracks, registry)

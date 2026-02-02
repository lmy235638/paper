from dataclasses import dataclass


@dataclass
class TrackTask:
    pono: str
    type: str
    start_time: float
    end_time: float
    start_station: str
    end_station: str
    track_id: str
    vehicle_id: str
    last_vehicle_id: str
    status: str
    process_time: int = 0  # 加工时间（分钟）

    

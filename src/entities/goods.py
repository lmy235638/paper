from dataclasses import dataclass
from typing import Optional


@dataclass
class Goods:
    """货物类，用于表示在生产流程中的货物"""
    pono: int  # 任务编号
    goods_id: str  # 货物ID
    start_ld: str  # 起始工位
    end_cc: str  # 结束工位
    refine_process: str  # 精炼工艺
    current_status: str = "ready"  # 货物状态：ready, processing, completed
    current_station: Optional[str] = None  # 当前所在工位
    is_process: bool = False  # 是否正在加工

    def __str__(self):
        return f"Goods(pono={self.pono}, id={self.goods_id})"
    
    def __repr__(self):
        return self.__str__()
    
    def set_process(self, is_processing: bool):
        """设置货物的加工状态"""
        self.is_process = is_processing
        if is_processing:
            self.current_status = "processing"
        else:
            self.current_status = "ready"
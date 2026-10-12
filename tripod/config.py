from dataclasses import dataclass


@dataclass
class Config:
    camera_name: str = "iPhone"
    width: int = 1280
    height: int = 720
    hfov: float = 70.0

    model: str = "yolo11n.pt"
    device: str = "mps"
    conf: float = 0.4
    imgsz: int = 640

    # боксы, которые начинаются ниже этой доли кадра - головы слушателей
    max_box_top: float = 0.6
    min_iou: float = 0.2
    max_jump: float = 1.5  # в ширинах бокса
    max_missed: int = 15

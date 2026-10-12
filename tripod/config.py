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

    # зоны в градусах от центра кадра
    stop_deg: float = 4.0
    warn_deg: float = 12.0
    edge_deg: float = 24.0

    alpha: float = 0.5
    beta: float = 0.05
    predict_time: float = 0.6
    confirm_time: float = 0.3

    settle_time: float = 0.3
    blink_time: float = 0.3
    lost_hold: float = 1.5

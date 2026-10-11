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

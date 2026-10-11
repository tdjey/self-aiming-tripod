from dataclasses import dataclass


@dataclass
class Config:
    camera_name: str = "iPhone"
    width: int = 1280
    height: int = 720
    hfov: float = 70.0

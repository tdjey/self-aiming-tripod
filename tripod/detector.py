from ultralytics import YOLO

PERSON = 0


class Detector:
    def __init__(self, model_path, device="mps", conf=0.4, imgsz=640):
        self.model = YOLO(model_path)
        self.device = device
        self.conf = conf
        self.imgsz = imgsz

    def detect(self, frame):
        res = self.model.predict(frame, classes=[PERSON], conf=self.conf, imgsz=self.imgsz,
                                 device=self.device, verbose=False)[0]
        return res.boxes.xyxy.cpu().numpy().tolist()

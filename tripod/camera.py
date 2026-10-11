import threading
import time

import AVFoundation as av
import CoreMedia
import libdispatch
import numpy as np
import objc
import Quartz
from Foundation import NSObject

# cv2.VideoCapture выбирает камеру по индексу и может открыть камеру мака,
# поэтому iPhone ищется по имени через AVFoundation


def list_cameras():
    return list(av.AVCaptureDevice.devicesWithMediaType_(av.AVMediaTypeVideo))


def find_camera(name):
    for dev in list_cameras():
        if name.lower() in str(dev.localizedName()).lower():
            return dev
    return None


def ask_permission():
    status = av.AVCaptureDevice.authorizationStatusForMediaType_(av.AVMediaTypeVideo)
    if status == av.AVAuthorizationStatusAuthorized:
        return True
    if status != av.AVAuthorizationStatusNotDetermined:
        return False
    done = threading.Event()
    answer = []

    def handler(granted):
        answer.append(granted)
        done.set()

    av.AVCaptureDevice.requestAccessForMediaType_completionHandler_(av.AVMediaTypeVideo, handler)
    done.wait(60)
    return bool(answer and answer[0])


def pixel_buffer_to_bgr(pixbuf):
    Quartz.CVPixelBufferLockBaseAddress(pixbuf, Quartz.kCVPixelBufferLock_ReadOnly)
    try:
        h = Quartz.CVPixelBufferGetHeight(pixbuf)
        w = Quartz.CVPixelBufferGetWidth(pixbuf)
        row = Quartz.CVPixelBufferGetBytesPerRow(pixbuf)
        data = Quartz.CVPixelBufferGetBaseAddress(pixbuf).as_buffer(row * h)
        # строка может быть шире картинки из-за выравнивания
        img = np.frombuffer(data, np.uint8).reshape(h, row // 4, 4)[:, :w, :3]
        return img.copy()
    finally:
        Quartz.CVPixelBufferUnlockBaseAddress(pixbuf, Quartz.kCVPixelBufferLock_ReadOnly)


class FrameDelegate(NSObject, protocols=[objc.protocolNamed("AVCaptureVideoDataOutputSampleBufferDelegate")]):
    def initWithCamera_(self, camera):
        self = objc.super(FrameDelegate, self).init()
        if self is None:
            return None
        self.camera = camera
        return self

    def captureOutput_didOutputSampleBuffer_fromConnection_(self, output, buffer, connection):
        with objc.autorelease_pool():
            pixbuf = CoreMedia.CMSampleBufferGetImageBuffer(buffer)
            if pixbuf is not None:
                self.camera.on_frame(pixel_buffer_to_bgr(pixbuf))


class Camera:
    def __init__(self, name, width=1280, height=720):
        if not ask_permission():
            raise RuntimeError("no camera permission")
        self.name = name
        self.preset = getattr(av, "AVCaptureSessionPreset%dx%d" % (width, height))
        self.frame = None
        self.stamp = 0.0
        self.frame_id = 0
        self.cond = threading.Condition()
        self.delegate = FrameDelegate.alloc().initWithCamera_(self)
        self.queue = libdispatch.dispatch_queue_create(b"tripod.camera", None)
        self.session = None
        self.start()

    def start(self):
        dev = find_camera(self.name)
        if dev is None:
            names = [str(d.localizedName()) for d in list_cameras()]
            raise RuntimeError("camera '%s' not found, available: %s" % (self.name, names))
        inp, err = av.AVCaptureDeviceInput.deviceInputWithDevice_error_(dev, None)
        if inp is None:
            raise RuntimeError("can't open camera: %s" % err)

        out = av.AVCaptureVideoDataOutput.alloc().init()
        out.setVideoSettings_({Quartz.kCVPixelBufferPixelFormatTypeKey: Quartz.kCVPixelFormatType_32BGRA})
        out.setAlwaysDiscardsLateVideoFrames_(True)
        out.setSampleBufferDelegate_queue_(self.delegate, self.queue)

        session = av.AVCaptureSession.alloc().init()
        if session.canSetSessionPreset_(self.preset):
            session.setSessionPreset_(self.preset)
        session.addInput_(inp)
        session.addOutput_(out)
        session.startRunning()
        self.session = session
        print("camera:", dev.localizedName())

    def on_frame(self, frame):
        with self.cond:
            self.frame = frame
            self.stamp = time.monotonic()
            self.frame_id += 1
            self.cond.notify_all()

    def read(self, last_id=0, timeout=1.0):
        with self.cond:
            self.cond.wait_for(lambda: self.frame_id != last_id, timeout)
            if self.frame_id != last_id:
                return self.frame, self.stamp, self.frame_id
            silent = time.monotonic() - self.stamp
        # continuity camera иногда отваливается, пробуем подключиться заново
        if self.frame_id > 0 and silent > 3:
            print("no frames for %.0f s, restarting camera" % silent)
            self.session.stopRunning()
            try:
                self.start()
            except RuntimeError as e:
                print(e)
            self.stamp = time.monotonic()
        return None, 0.0, last_id

    def close(self):
        if self.session is not None:
            self.session.stopRunning()


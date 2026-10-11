from tripod.camera import list_cameras

for dev in list_cameras():
    print(dev.localizedName(), "-", dev.deviceType())

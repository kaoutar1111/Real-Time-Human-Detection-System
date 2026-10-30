from hik_camera import HikCamera

# 创建相机对象
camera = HikCamera()

# 枚举相机
print("开始枚举相机...")
cameras = camera.enum_cameras()
print(f"枚举完成，找到 {len(cameras)} 个相机")
print("相机列表:")
for i, cam in enumerate(cameras):
    print(f"  {i}: {cam}")

# 尝试连接第一个相机
if cameras:
    print("\n尝试连接第一个相机...")
    success = camera.connect(0)
    if success:
        print("相机连接成功")
        # 断开连接
        camera.disconnect()
        print("相机已断开连接")
    else:
        print("相机连接失败")
else:
    print("没有找到相机")

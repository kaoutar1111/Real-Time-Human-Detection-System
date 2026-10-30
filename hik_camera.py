import os
import sys
import ctypes
from ctypes import *
import numpy as np
import cv2

SDK_PATH = "C:\\Program Files (x86)\\Common Files\\MVS\\Runtime\\Win64_x64"

os.environ['PATH'] = SDK_PATH + ';' + os.environ.get('PATH', '')
print(f"SDK path added to environment: {SDK_PATH}")

if not os.path.exists(SDK_PATH):
    print(f"SDK path does not exist: {SDK_PATH}")
else:
    print(f"SDK path exists: {SDK_PATH}")

dll_path = os.path.join(SDK_PATH, "MvCameraControl.dll")
if not os.path.exists(dll_path):
    print(f"MvCameraControl.dll does not exist: {dll_path}")
else:
    print(f"MvCameraControl.dll exists: {dll_path}")


class MVCC_INTVALUE(Structure):
    _fields_ = [
        ("nCurValue", c_uint),
        ("nMax", c_uint),
        ("nMin", c_uint),
        ("nInc", c_uint)
    ]


class MVCC_FLOATVALUE(Structure):
    _pack_ = 1
    _fields_ = [
        ("fCurValue", c_float),
        ("fMax", c_float),
        ("fMin", c_float),
        ("fInc", c_float),
        ("nReserved", c_uint * 4)
    ]


class MV_FRAME_OUT_INFO_EX(Structure):
    _fields_ = [
        ("nWidth", c_ushort),
        ("nHeight", c_ushort),
        ("enPixelType", c_uint),
        ("nFrameNum", c_uint),
        ("nDevTimeStampHigh", c_uint),
        ("nDevTimeStampLow", c_uint),
        ("nHostTimeStamp", c_uint64),
        ("nImageSize", c_uint),
        ("nLostPacket", c_uint),
        ("nLostFrame", c_uint),
        ("nReserved", c_uint * 8)
    ]


class MV_GIGE_DEVICE_INFO(Structure):
    _fields_ = [
        ("nIpCfgOption", c_uint),
        ("nIpCfgCurrent", c_uint),
        ("nCurrentIp", c_uint),
        ("nCurrentSubNetMask", c_uint),
        ("nDefultGateWay", c_uint),
        ("chManufacturerName", c_char * 32),
        ("chModelName", c_char * 32),
        ("chDeviceVersion", c_char * 32),
        ("chManufacturerSpecificInfo", c_char * 48),
        ("chSerialNumber", c_char * 16),
        ("chUserDefinedName", c_char * 16),
        ("nNetExport", c_uint),
        ("nReserved", c_uint * 4),
    ]


class MV_USB3_DEVICE_INFO(Structure):
    _fields_ = [
        ("nVendorID", c_ushort),
        ("nProductID", c_ushort),
        ("nDeviceNumber", c_uint),
        ("nDeviceGUID", c_uint * 4),
        ("nDeviceClass", c_uint),
        ("nDeviceSubClass", c_uint),
        ("nDeviceProtocol", c_uint),
        ("nCurrentSpeed", c_uint),
        ("nDeviceVersion", c_uint),
        ("nManufacturerNameLength", c_uint),
        ("chManufacturerName", c_char * 48),
        ("nProductNameLength", c_uint),
        ("chProductName", c_char * 48),
        ("nSerialNumberLength", c_uint),
        ("chSerialNumber", c_char * 48),
        ("nDeviceLocationLength", c_uint),
        ("chDeviceLocation", c_char * 256),
        ("nReserved", c_uint * 8),
    ]


class DeviceInfo(Union):
    _fields_ = [
        ("stGigEInfo", MV_GIGE_DEVICE_INFO),
        ("stUsb3VInfo", MV_USB3_DEVICE_INFO),
    ]


class MV_CC_DEVICE_INFO(Structure):
    _pack_ = 1
    _fields_ = [
        ("nMajorVer", c_ushort),
        ("nMinorVer", c_ushort),
        ("nMacAddrHigh", c_uint),
        ("nMacAddrLow", c_uint),
        ("nTLayerType", c_uint),
        ("nReserved", c_uint * 4),
        ("SpecialInfo", DeviceInfo),
    ]


class MV_CC_DEVICE_INFO_LIST(Structure):
    _fields_ = [
        ("nDeviceNum", c_uint),
        ("pDeviceInfo", POINTER(MV_CC_DEVICE_INFO) * 256),
    ]


try:
    print(f"Loading SDK: {dll_path}")
    MvCameraControl = cdll.LoadLibrary(dll_path)

    MvCameraControl.MV_CC_Initialize.argtypes = []
    MvCameraControl.MV_CC_Initialize.restype = c_int
    MvCameraControl.MV_CC_EnumDevices.argtypes = [c_uint, POINTER(MV_CC_DEVICE_INFO_LIST)]
    MvCameraControl.MV_CC_EnumDevices.restype = c_int
    MvCameraControl.MV_CC_CreateHandle.argtypes = [POINTER(c_void_p), POINTER(MV_CC_DEVICE_INFO)]
    MvCameraControl.MV_CC_CreateHandle.restype = c_int
    MvCameraControl.MV_CC_OpenDevice.argtypes = [c_void_p, c_uint]
    MvCameraControl.MV_CC_OpenDevice.restype = c_int
    MvCameraControl.MV_CC_StartGrabbing.argtypes = [c_void_p]
    MvCameraControl.MV_CC_StartGrabbing.restype = c_int
    MvCameraControl.MV_CC_StopGrabbing.argtypes = [c_void_p]
    MvCameraControl.MV_CC_StopGrabbing.restype = c_int
    MvCameraControl.MV_CC_CloseDevice.argtypes = [c_void_p]
    MvCameraControl.MV_CC_CloseDevice.restype = c_int
    MvCameraControl.MV_CC_DestroyHandle.argtypes = [c_void_p]
    MvCameraControl.MV_CC_DestroyHandle.restype = c_int
    MvCameraControl.MV_CC_GetSDKVersion.argtypes = [POINTER(c_int)]
    MvCameraControl.MV_CC_GetSDKVersion.restype = c_int
    MvCameraControl.MV_CC_GetIntValue.argtypes = [c_void_p, c_char_p, POINTER(MVCC_INTVALUE)]
    MvCameraControl.MV_CC_GetIntValue.restype = c_int
    MvCameraControl.MV_CC_SetEnumValue.argtypes = [c_void_p, c_char_p, c_uint]
    MvCameraControl.MV_CC_SetEnumValue.restype = c_int
    MvCameraControl.MV_CC_SetFloatValue.argtypes = [c_void_p, c_char_p, c_float]
    MvCameraControl.MV_CC_SetFloatValue.restype = c_int
    MvCameraControl.MV_CC_GetFloatValue.argtypes = [c_void_p, c_char_p, POINTER(MVCC_FLOATVALUE)]
    MvCameraControl.MV_CC_GetFloatValue.restype = c_int
    MvCameraControl.MV_CC_SetCommandValue.argtypes = [c_void_p, c_char_p]
    MvCameraControl.MV_CC_SetCommandValue.restype = c_int
    MvCameraControl.MV_CC_GetOneFrameTimeout.argtypes = [
        c_void_p, POINTER(c_ubyte), c_uint, POINTER(MV_FRAME_OUT_INFO_EX), c_int
    ]
    MvCameraControl.MV_CC_GetOneFrameTimeout.restype = c_int
    MvCameraControl.MV_CC_GetEnumValue.argtypes = [c_void_p, c_char_p, POINTER(c_uint)]
    MvCameraControl.MV_CC_GetEnumValue.restype = c_int

    print("SDK loaded successfully")

    ret = MvCameraControl.MV_CC_Initialize()
    if ret == 0:
        print("SDK initialized successfully")
    else:
        print(f"SDK initialization failed, error code: {ret}")

    try:
        version_ptr = c_int()
        ret = MvCameraControl.MV_CC_GetSDKVersion(byref(version_ptr))
        if ret == 0:
            version = version_ptr.value
            major = (version >> 24) & 0xFF
            minor = (version >> 16) & 0xFF
            revision = (version >> 8) & 0xFF
            build = version & 0xFF
            print(f"SDK version: {major}.{minor}.{revision}.{build}")
    except Exception as e:
        print(f"Error getting SDK version: {e}")

except Exception as e:
    print(f"Failed to load Hikvision SDK: {e}")
    MvCameraControl = None


class HikCamera:
    def __init__(self):
        self.device_list = []
        self.camera_handle = c_void_p()
        self.is_opened = False
        self.frame_info = MV_FRAME_OUT_INFO_EX()
        self.image_buffer = None
        self.buffer_size = 0
        self.device_info_list = None
        self.last_pixel_format = None
        self.frame_count = 0
        self.failed_frame_count = 0
        
        print(f"MV_FRAME_OUT_INFO_EX struct size: {sizeof(MV_FRAME_OUT_INFO_EX)}")
        for name, typ in MV_FRAME_OUT_INFO_EX._fields_:
            offset = getattr(MV_FRAME_OUT_INFO_EX, name).offset
            print(f"  {name}: offset={offset}, size={sizeof(typ)}")

    def enum_cameras(self):
        if MvCameraControl is None:
            print("SDK not loaded, cannot enumerate cameras")
            return []

        self.device_list = []

        try:
            self.device_info_list = MV_CC_DEVICE_INFO_LIST()

            ret = MvCameraControl.MV_CC_EnumDevices(c_uint(1), byref(self.device_info_list))
            if ret != 0:
                print(f"Failed to enumerate GigE devices, error code: {ret}")
                ret = MvCameraControl.MV_CC_EnumDevices(c_uint(2), byref(self.device_info_list))
                if ret != 0:
                    print(f"Failed to enumerate USB devices, error code: {ret}")
                    return []

            device_num = self.device_info_list.nDeviceNum
            print(f"Found {device_num} device(s)")

            if device_num == 0:
                return []

            for i in range(device_num):
                try:
                    dev_info = self.device_info_list.pDeviceInfo[i]
                    if dev_info is None:
                        print(f"Device {i} info is empty")
                        continue
                    
                    dev_type_value = dev_info.contents.nTLayerType
                    if dev_type_value == 1:
                        dev_type = "GigE"
                        gige_info = dev_info.contents.SpecialInfo.stGigEInfo
                        device_name = gige_info.chUserDefinedName.decode('gbk', errors='ignore').strip('\x00')
                        if not device_name:
                            device_name = gige_info.chModelName.decode('gbk', errors='ignore').strip('\x00')
                        ip_int = gige_info.nCurrentIp
                        ip_str = f"{(ip_int >> 24) & 0xFF}.{(ip_int >> 16) & 0xFF}.{(ip_int >> 8) & 0xFF}.{ip_int & 0xFF}"
                    elif dev_type_value == 2:
                        dev_type = "USB"
                        usb_info = dev_info.contents.SpecialInfo.stUsb3VInfo
                        device_name = usb_info.chProductName.decode('gbk', errors='ignore').strip('\x00')
                        if not device_name:
                            device_name = usb_info.chSerialNumber.decode('gbk', errors='ignore').strip('\x00')
                        ip_str = "USB"
                    else:
                        dev_type = "Unknown"
                        device_name = f"Unknown_Camera_{i}"
                        ip_str = "Unknown"

                    print(f"Device {i}: {device_name} ({ip_str}) [{dev_type}]")

                    self.device_list.append({
                        'name': device_name,
                        'ip': ip_str,
                        'index': i,
                        'type': dev_type,
                        'dev_info': dev_info
                    })
                except Exception as e:
                    print(f"Error processing device {i}: {e}")
                    import traceback
                    traceback.print_exc()
                    continue

        except Exception as e:
            print(f"Error enumerating cameras: {e}")
            import traceback
            traceback.print_exc()

        return [f"{d['name']} ({d['ip']})" for d in self.device_list]

    def connect(self, camera_identifier):
        if MvCameraControl is None:
            print("SDK not loaded")
            return False

        if isinstance(camera_identifier, int):
            camera_index = camera_identifier
        else:
            camera_index = -1
            for i, d in enumerate(self.device_list):
                display_name = f"{d['name']} ({d['ip']})"
                if display_name == camera_identifier or d['name'] == camera_identifier:
                    camera_index = i
                    break
        
        if camera_index < 0 or camera_index >= len(self.device_list):
            print(f"Invalid camera: {camera_identifier}, available devices: {len(self.device_list)}")
            return False

        try:
            dev_info = self.device_list[camera_index]['dev_info']
            print(f"Connecting to camera: {self.device_list[camera_index]['name']}")

            print("Creating camera handle...")
            ret = MvCameraControl.MV_CC_CreateHandle(byref(self.camera_handle), dev_info)
            if ret != 0:
                print(f"Failed to create camera handle, error code: {ret}")
                return False
            
            print("Camera handle created successfully")

            print("Opening camera...")
            ret = MvCameraControl.MV_CC_OpenDevice(self.camera_handle, c_uint(2))
            if ret != 0:
                print(f"Failed to open camera, error code: {ret}")
                MvCameraControl.MV_CC_DestroyHandle(self.camera_handle)
                self.camera_handle = c_void_p()
                return False

            print("Camera opened successfully")

            print("Setting trigger mode to continuous...")
            ret = MvCameraControl.MV_CC_SetEnumValue(self.camera_handle, b"TriggerMode", c_uint(0))
            if ret != 0:
                print(f"Failed to set trigger mode, error code: {ret}")
                self.disconnect()
                return False
            print("Trigger mode set to continuous")

            print("Getting image dimensions...")
            width_ptr = MVCC_INTVALUE()
            height_ptr = MVCC_INTVALUE()

            ret = MvCameraControl.MV_CC_GetIntValue(self.camera_handle, b"Width", byref(width_ptr))
            if ret != 0:
                print(f"Failed to get width, error code: {ret}")
                width_ptr.nCurValue = 1920
            else:
                print(f"Width retrieved: {width_ptr.nCurValue}")
            
            ret = MvCameraControl.MV_CC_GetIntValue(self.camera_handle, b"Height", byref(height_ptr))
            if ret != 0:
                print(f"Failed to get height, error code: {ret}")
                height_ptr.nCurValue = 1080
            else:
                print(f"Height retrieved: {height_ptr.nCurValue}")
            
            print(f"Image dimensions: {width_ptr.nCurValue} x {height_ptr.nCurValue}")

            self.buffer_size = width_ptr.nCurValue * height_ptr.nCurValue * 3
            self.image_buffer = (c_ubyte * self.buffer_size)()
            print(f"Image buffer allocated: {self.buffer_size} bytes")

            print("Setting pixel format to RGB8...")
            pixel_format_rgb = 0x02180015
            ret = MvCameraControl.MV_CC_SetEnumValue(self.camera_handle, b"PixelFormat", c_uint(pixel_format_rgb))
            if ret != 0:
                print(f"Failed to set RGB pixel format, error code: {ret}")
                print("Trying to get current pixel format...")
                pixel_type_ptr = c_uint()
                try:
                    ret2 = MvCameraControl.MV_CC_GetEnumValue(self.camera_handle, b"PixelFormat", byref(pixel_type_ptr))
                    if ret2 == 0:
                        self.last_pixel_format = pixel_type_ptr.value
                        print(f"Current pixel format: 0x{self.last_pixel_format:X}")
                    else:
                        print(f"Failed to get pixel format, error code: {ret2}")
                except Exception as e:
                    print(f"Error getting pixel format: {e}")
            else:
                self.last_pixel_format = pixel_format_rgb
                print("Pixel format set to RGB8")

            print("Starting acquisition...")
            ret = MvCameraControl.MV_CC_StartGrabbing(self.camera_handle)
            if ret != 0:
                print(f"Failed to start acquisition, error code: {ret}")
                self.disconnect()
                return False

            print("Setting default exposure to improve image brightness...")
            ret = MvCameraControl.MV_CC_SetEnumValue(self.camera_handle, b"ExposureAuto", c_uint(0))
            if ret != 0:
                print(f"Failed to disable auto exposure, error code: {ret}")
            else:
                print("Auto exposure disabled")
                
            ret = MvCameraControl.MV_CC_SetFloatValue(self.camera_handle, b"ExposureTime", c_float(50000.0))
            if ret == 0:
                print("Exposure set to 50ms")
            else:
                print(f"Failed to set exposure, error code: {ret}")

            print("Setting default gain...")
            ret = MvCameraControl.MV_CC_SetEnumValue(self.camera_handle, b"GainAuto", c_uint(0))
            if ret != 0:
                print(f"Failed to disable auto gain, error code: {ret}")
            else:
                print("Auto gain disabled")
                
            ret = MvCameraControl.MV_CC_SetFloatValue(self.camera_handle, b"Gain", c_float(10.0))
            if ret == 0:
                print("Gain set to 10dB")
            else:
                print(f"Failed to set gain, error code: {ret}")

            print("Camera acquisition started successfully")
            self.is_opened = True
            self.frame_count = 0
            self.failed_frame_count = 0
            return True
        except Exception as e:
            print(f"Error connecting to camera: {e}")
            import traceback
            traceback.print_exc()
            if self.camera_handle.value:
                MvCameraControl.MV_CC_DestroyHandle(self.camera_handle)
                self.camera_handle = c_void_p()
            return False

    def disconnect(self):
        if self.camera_handle.value and self.is_opened:
            MvCameraControl.MV_CC_StopGrabbing(self.camera_handle)
            MvCameraControl.MV_CC_CloseDevice(self.camera_handle)
            MvCameraControl.MV_CC_DestroyHandle(self.camera_handle)
        self.camera_handle = c_void_p()
        self.is_opened = False
        print("Camera disconnected")

    def get_image(self):
        if not self.is_opened or MvCameraControl is None:
            print("[DEBUG] Camera not opened or SDK not loaded")
            return None

        try:
            frame_info_ptr = byref(self.frame_info)

            if self.buffer_size == 0:
                print("[DEBUG] Buffer size is 0, allocating default buffer")
                self.buffer_size = 2448 * 2048 * 3
                self.image_buffer = (c_ubyte * self.buffer_size)()
            
            ret = MvCameraControl.MV_CC_GetOneFrameTimeout(
                self.camera_handle,
                self.image_buffer,
                c_uint(self.buffer_size),
                frame_info_ptr,
                c_int(1000)
            )

            if ret != 0:
                self.failed_frame_count += 1
                print(f"[DEBUG] Frame capture failed, error code: {ret}, failed count: {self.failed_frame_count}")
                if self.failed_frame_count < 5:
                    return self.get_test_image()
                else:
                    print("[DEBUG] Too many failed frames, returning None")
                    return None

            self.frame_count += 1
            if self.frame_count % 30 == 0:
                print(f"[DEBUG] Frame captured successfully, frame #{self.frame_count}")

            width = self.frame_info.nWidth
            height = self.frame_info.nHeight
            pixel_type = self.frame_info.enPixelType
            image_size = self.frame_info.nImageSize
            
            if self.frame_count % 30 == 0:
                print(f"[DEBUG] Image info: {width}x{height}, pixel format: {pixel_type} (0x{pixel_type:X}), size: {image_size}")
            
            if image_size == 0 or width == 0 or height == 0:
                print("[DEBUG] Invalid image dimensions or size")
                return self.get_test_image()
            
            required_size = width * height * 3
            if image_size > self.buffer_size:
                print(f"[DEBUG] Buffer too small ({self.buffer_size}), resizing to {required_size}")
                self.buffer_size = required_size
                self.image_buffer = (c_ubyte * self.buffer_size)()
            
            img_array = None
            
            if pixel_type in [0x01080001, 0x08000001]:
                if self.frame_count % 30 == 0:
                    print("[DEBUG] Pixel format: Mono8 (0x01080001)")
                img_array = np.frombuffer(self.image_buffer, dtype=np.uint8, count=width * height)
                img_array = img_array.reshape((height, width))
                img_array = cv2.cvtColor(img_array, cv2.COLOR_GRAY2BGR)
                
            elif pixel_type in [0x01100003, 0x10000003]:
                if self.frame_count % 30 == 0:
                    print("[DEBUG] Pixel format: Mono16 (0x01100003)")
                raw_data = np.frombuffer(self.image_buffer, dtype=np.uint16, count=width * height)
                raw_data = raw_data.reshape((height, width))
                img_array = (raw_data >> 2).astype(np.uint8)
                img_array = cv2.cvtColor(img_array, cv2.COLOR_GRAY2BGR)
                
            elif pixel_type in [0x01100005, 0x10000005]:
                if self.frame_count % 30 == 0:
                    print("[DEBUG] Pixel format: Mono16 packed (0x01100005)")
                raw_data = np.frombuffer(self.image_buffer, dtype=np.uint16, count=width * height)
                raw_data = raw_data.reshape((height, width))
                img_array = (raw_data >> 4).astype(np.uint8)
                img_array = cv2.cvtColor(img_array, cv2.COLOR_GRAY2BGR)
                
            elif pixel_type in [0x01080008, 0x08000008]:
                if self.frame_count % 30 == 0:
                    print("[DEBUG] Pixel format: BayerGR8 (0x01080008)")
                raw_data = np.frombuffer(self.image_buffer, dtype=np.uint8, count=width * height)
                raw_data = raw_data.reshape((height, width))
                img_array = cv2.cvtColor(raw_data, cv2.COLOR_BayerGR2BGR)
                
            elif pixel_type in [0x01080009, 0x08000009]:
                if self.frame_count % 30 == 0:
                    print("[DEBUG] Pixel format: BayerRG8 (0x01080009)")
                raw_data = np.frombuffer(self.image_buffer, dtype=np.uint8, count=width * height)
                raw_data = raw_data.reshape((height, width))
                img_array = cv2.cvtColor(raw_data, cv2.COLOR_BayerRG2BGR)
                
            elif pixel_type in [0x0108000A, 0x0800000A]:
                if self.frame_count % 30 == 0:
                    print("[DEBUG] Pixel format: BayerGB8 (0x0108000A)")
                raw_data = np.frombuffer(self.image_buffer, dtype=np.uint8, count=width * height)
                raw_data = raw_data.reshape((height, width))
                img_array = cv2.cvtColor(raw_data, cv2.COLOR_BayerGB2BGR)
                
            elif pixel_type in [0x0108000B, 0x0800000B]:
                if self.frame_count % 30 == 0:
                    print("[DEBUG] Pixel format: BayerBG8 (0x0108000B)")
                raw_data = np.frombuffer(self.image_buffer, dtype=np.uint8, count=width * height)
                raw_data = raw_data.reshape((height, width))
                img_array = cv2.cvtColor(raw_data, cv2.COLOR_BayerBG2BGR)
                
            elif pixel_type in [0x02180014, 0x1800014]:
                if self.frame_count % 30 == 0:
                    print("[DEBUG] Pixel format: RGB8 (0x02180014)")
                img_array = np.frombuffer(self.image_buffer, dtype=np.uint8, count=width * height * 3)
                img_array = img_array.reshape((height, width, 3))
                
            elif pixel_type in [0x02180015, 0x1800015]:
                if self.frame_count % 30 == 0:
                    print("[DEBUG] Pixel format: BGR8 (0x02180015)")
                img_array = np.frombuffer(self.image_buffer, dtype=np.uint8, count=width * height * 3)
                img_array = img_array.reshape((height, width, 3))
                
            else:
                print(f"[DEBUG] Unknown pixel format: {pixel_type} (0x{pixel_type:X})")
                if image_size == width * height:
                    print("[DEBUG] Attempting to process as Mono8")
                    img_array = np.frombuffer(self.image_buffer, dtype=np.uint8, count=width * height)
                    img_array = img_array.reshape((height, width))
                    img_array = cv2.cvtColor(img_array, cv2.COLOR_GRAY2BGR)
                elif image_size == width * height * 3:
                    print("[DEBUG] Attempting to process as RGB24")
                    img_array = np.frombuffer(self.image_buffer, dtype=np.uint8, count=width * height * 3)
                    img_array = img_array.reshape((height, width, 3))
                else:
                    print("[DEBUG] Cannot determine pixel format, returning test image")
                    return self.get_test_image()
            
            if img_array is not None:
                if self.frame_count % 30 == 0:
                    print(f"[DEBUG] NumPy array shape: {img_array.shape}, dtype: {img_array.dtype}")
                if img_array.size == 0:
                    print("[DEBUG] Empty array returned")
                    return self.get_test_image()
                return img_array

        except Exception as e:
            print(f"[DEBUG] Exception in get_image: {e}")
            import traceback
            traceback.print_exc()
            return None

        print("[DEBUG] No valid image data")
        return self.get_test_image()

    def get_test_image(self):
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        camera_name = self.device_list[0]['name'] if self.device_list else 'Unknown'
        cv2.putText(img, f"Camera: {camera_name}",
                    (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(img, "Status: Connected (Test Mode)",
                    (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(img, "Press 'Set' buttons to configure",
                    (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

        for i in range(640):
            color = int(255 * i / 640)
            cv2.line(img, (i, 200), (i, 250), (color, color, color), 1)

        for i in range(480):
            color = int(255 * i / 480)
            cv2.line(img, (100, i), (150, i), (color, color, color), 1)

        return img

    def set_exposure(self, exposure):
        if not self.is_opened or MvCameraControl is None:
            print("Camera not connected")
            return False

        try:
            ret = MvCameraControl.MV_CC_SetEnumValue(self.camera_handle, b"ExposureAuto", c_uint(0))
            if ret != 0:
                print(f"Failed to set exposure mode, error code: {ret}")

            exposure_time = exposure * 1000
            ret = MvCameraControl.MV_CC_SetFloatValue(self.camera_handle, b"ExposureTime",
                                                      c_float(exposure_time))
            if ret == 0:
                print(f"Exposure set to {exposure} ms")
                return True
            else:
                print(f"Failed to set exposure, error code: {ret}")
                return False
        except Exception as e:
            print(f"Error setting exposure: {e}")
            return False

    def set_gain(self, gain):
        if not self.is_opened or MvCameraControl is None:
            print("Camera not connected")
            return False

        try:
            ret = MvCameraControl.MV_CC_SetEnumValue(self.camera_handle, b"GainAuto", c_uint(0))
            if ret != 0:
                print(f"Failed to set gain mode, error code: {ret}")

            ret = MvCameraControl.MV_CC_SetFloatValue(self.camera_handle, b"Gain", c_float(gain))
            if ret == 0:
                print(f"Gain set to {gain} dB")
                return True
            else:
                print(f"Failed to set gain, error code: {ret}")
                return False
        except Exception as e:
            print(f"Error setting gain: {e}")
            return False

    def get_exposure(self):
        if not self.is_opened or MvCameraControl is None:
            print("Camera not connected")
            return None

        try:
            exposure_value = MVCC_FLOATVALUE()
            ret = MvCameraControl.MV_CC_GetFloatValue(self.camera_handle, b"ExposureTime", byref(exposure_value))
            if ret == 0:
                exposure_ms = exposure_value.fCurValue / 1000.0
                print(f"Current exposure: {exposure_ms:.2f} ms")
                return exposure_ms
            else:
                print(f"Failed to get exposure, error code: {ret}")
                return None
        except Exception as e:
            print(f"Error getting exposure: {e}")
            return None

    def get_gain(self):
        if not self.is_opened or MvCameraControl is None:
            print("Camera not connected")
            return None

        try:
            gain_value = MVCC_FLOATVALUE()
            ret = MvCameraControl.MV_CC_GetFloatValue(self.camera_handle, b"Gain", byref(gain_value))
            if ret == 0:
                print(f"Current gain: {gain_value.fCurValue:.2f} dB")
                return gain_value.fCurValue
            else:
                print(f"Failed to get gain, error code: {ret}")
                return None
        except Exception as e:
            print(f"Error getting gain: {e}")
            return None

    def set_trigger_mode(self, mode):
        if not self.is_opened or MvCameraControl is None:
            print("Camera not connected")
            return False

        try:
            trigger_mode = 1 if mode == "External Trigger" else 0

            ret = MvCameraControl.MV_CC_SetEnumValue(self.camera_handle, b"TriggerMode", c_uint(trigger_mode))
            if ret == 0:
                print(f"Trigger mode set to: {mode}")
                return True
            else:
                print(f"Failed to set trigger mode, error code: {ret}")
                return False
        except Exception as e:
            print(f"Error setting trigger mode: {e}")
            return False

    def set_trigger_source(self, source):
        if not self.is_opened or MvCameraControl is None:
            print("Camera not connected")
            return False

        try:
            source_map = {
                "Soft Trigger": 7,
                "Line0": 0,
                "Line1": 1,
                "Line2": 2,
                "Line3": 3,
            }
            source_value = source_map.get(source, 7)

            ret = MvCameraControl.MV_CC_SetEnumValue(self.camera_handle, b"TriggerSource", c_uint(source_value))
            if ret == 0:
                print(f"Trigger source set to: {source}")
                return True
            else:
                print(f"Failed to set trigger source, error code: {ret}")
                return False
        except Exception as e:
            print(f"Error setting trigger source: {e}")
            return False

    def soft_trigger(self):
        if not self.is_opened or MvCameraControl is None:
            print("Camera not connected")
            return False

        try:
            ret = MvCameraControl.MV_CC_SetCommandValue(self.camera_handle, b"TriggerSoftware")
            if ret == 0:
                print("Soft trigger executed successfully")
                return True
            else:
                print(f"Soft trigger failed, error code: {ret}")
                return False
        except Exception as e:
            print(f"Error executing soft trigger: {e}")
            return False

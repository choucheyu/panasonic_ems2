"""Panasonic EMS2 API endpoint builders."""

BASE_URL = "https://ems2.panasonic.com.tw/api"


def open_session():
    return f"{BASE_URL}/userlogin1"


def close_session():
    return f"{BASE_URL}/userlogout1"


def refresh_token():
    return f"{BASE_URL}/RefreshToken1"


def get_user_info():
    return f"{BASE_URL}/UserGetInfo"


def get_update_info():
    return "https://ems2.panasonic.com.tw/PSHE_MI/api/S3/UpdateCheck"


def get_user_devices():
    return f"{BASE_URL}/UserGetRegisteredGwList2"


def get_gw_ip():
    return f"{BASE_URL}/UserGetGWIP"


def post_device_get_info():
    return f"{BASE_URL}/DeviceGetInfo"


def get_device_status():
    return f"{BASE_URL}/UserGetDeviceStatus"


def get_plate_mode():
    return f"{BASE_URL}/PlateGetMode"


def set_device():
    return f"{BASE_URL}/DeviceSetCommand"

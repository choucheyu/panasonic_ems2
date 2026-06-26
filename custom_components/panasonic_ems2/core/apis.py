"""Compatibility wrapper for Panasonic EMS2 API endpoints."""

from ..api.endpoints import (
    BASE_URL,
    close_session,
    get_device_status,
    get_gw_ip,
    get_plate_mode,
    get_update_info,
    get_user_devices,
    get_user_info,
    open_session,
    post_device_get_info,
    refresh_token,
    set_device,
)

__all__ = [
    "BASE_URL",
    "open_session",
    "close_session",
    "refresh_token",
    "get_user_info",
    "get_update_info",
    "get_user_devices",
    "get_gw_ip",
    "post_device_get_info",
    "get_device_status",
    "get_plate_mode",
    "set_device",
]

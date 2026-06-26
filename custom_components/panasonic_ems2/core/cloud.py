""" Panasonic Smart Home """
import logging
import asyncio
import json
from datetime import datetime, timedelta
import pytz
from typing import Literal

from homeassistant.components.recorder.models import StatisticData, StatisticMetaData, StatisticMeanType
from homeassistant.components.recorder.statistics import async_add_external_statistics
from homeassistant.helpers.update_coordinator import UpdateFailed
from homeassistant.const import UnitOfEnergy, UnitOfVolume
from homeassistant.util.unit_conversion import EnergyConverter, VolumeConverter

from ..api import endpoints as apis
from ..api.client import PanasonicApiClient
from ..api.errors import (
    Ems2TokenNotFound,
    Ems2LoginFailed,
    Ems2ExceedRateLimit,
    Ems2Expectation,
    Ems2TooManyRequest
)
from ..api.token_store import PanasonicTokenStore
from .capabilities import (
    command_name_override,
    command_range_override,
    range_lookup_models,
    set_command_id,
)
from .cloud_commands import (
    build_light_device_command_types,
    build_polling_command_types,
    filter_supplemental_snapshot,
    get_supplemental_keys,
    merge_supplemental_status,
)
from .cloud_status import (
    build_offline_information,
    normalize_command_status,
    refactor_device_information,
)
from .command_metadata import refactor_command_metadata
from .statistics_builder import build_user_info_external_statistics_rows
from .user_info_requests import build_user_info_statistics_requests
from .user_info_series import parse_user_info_series
from .const import (
    APP_TOKEN,
    DOMAIN,
    CONF_CPTOKEN,
    CONF_TOKEN_TIMEOUT,
    CONF_REFRESH_TOKEN,
    CONF_REFRESH_TOKEN_TIMEOUT,
    CAPABILITY_REGISTRY,
    MODEL_JP_TYPES,
    DEVICE_TYPE_DEHUMIDIFIER,
    DEVICE_TYPE_FRIDGE,
    DEVICE_TYPE_LIGHT,
    DEVICE_TYPE_WASHING_MACHINE,
    DEVICE_TYPE_WEIGHT_PLATE,
    ENTITY_MONTHLY_ENERGY,
    ENTITY_DOOR_OPENS,
    ENTITY_WASH_TIMES,
    ENTITY_WATER_USED,
    ENTITY_UPDATE,
    ENTITY_UPDATE_INFO,
    USER_INFO_SERIES_REFRESH_SECONDS,
    HA_USER_AGENT,
    WASHING_MACHINE_MODELS,
    WASHING_MACHINE_2020_MODELS,
    WASHING_MACHINE_OPERATING_STATUS,
    WASHING_MACHINE_TIMER_REMAINING_TIME,
    WEIGHT_PLATE_FOOD_NAME,
    WEIGHT_PLATE_MANAGEMENT_MODE,
    WEIGHT_PLATE_MANAGEMENT_VALUE,
    WEIGHT_PLATE_AMOUNT_MAX,
    WEIGHT_PLATE_BUY_DATE,
    WEIGHT_PLATE_DUE_DATE,
    WEIGHT_PLATE_COMMUNICATION_MODE,
    WEIGHT_PLATE_COMMUNICATION_TIME,
    WEIGHT_PLATE_TOTAL_WEIGHT,
    WEIGHT_PLATE_RESTORE_WEIGHT,
    WEIGHT_PLATE_LOW_BATTERY,
    USER_INFO_TYPES,
    REQUEST_TIMEOUT
)
local_tz = pytz.timezone('Asia/Taipei')

_LOGGER = logging.getLogger(__name__)

def api_status(func):
    """
    wrapper_call
    """
    async def wrapper_call(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Ems2TokenNotFound:
            await args[0].refresh_token()
            return await func(*args, **kwargs)
        except Ems2LoginFailed:
            await args[0].login()
            return await func(*args, **kwargs)
        except Ems2TooManyRequest:
            await asyncio.sleep(2)
            return await func(*args, **kwargs)
        except Ems2Expectation:
            return args[0]._devices_info
        except (
            Exception,
        ) as e:
            _LOGGER.warning(f"Got exception {e}")
            #return {}
            return args[0]._devices_info
    return wrapper_call


class PanasonicSmartHome(object):
    """
    Panasonic Smart Home Object
    """
    def __init__(self, hass, session, account, password):
        self.hass = hass
        self.email = account
        self.password = password
        self._session = session
        self._api_client = PanasonicApiClient(
            session=session,
            account=account,
            user_agent=HA_USER_AGENT,
            request_timeout=REQUEST_TIMEOUT,
        )
        self._token_store = PanasonicTokenStore(hass, account)
        self._devices = []
        self._select_devices = []
        self._commands = []
        self._devices_info = {}
        self._commands_info = {}
        self._update_info = {}
        self._cp_token = ""
        self._refresh_token = None
        self._expires_in = 0
        self._expire_time = None
        self._token_timeout = None
        self._refresh_token_timeout = None
        self._mversion = None
        self._update_timestamp = None
        self._user_info_series_last_update = None
        self._api_counts = 0
        self._api_counts_per_hour = 0

    async def request(
        self,
        method: Literal["GET", "POST"],
        headers,
        endpoint: str,
        params=None,
        data=None,
    ):
        """Shared request wrapper preserving the PanasonicSmartHome public seam."""
        response = await self._api_client.request(
            method=method,
            headers=headers,
            endpoint=endpoint,
            params=params,
            data=data,
        )
        self._api_counts = self._api_client.api_counts
        self._api_counts_per_hour = self._api_client.api_counts_per_hour
        return response

    @property
    def token(self) -> bool:
        if len(self._cp_token) >= 1:
            return True
        return False

    @property
    def devices_number(self) -> int:
        return len(self._devices)

    async def set_select_devices(self, devices):
        """
        set select devices
        """
        self._select_devices = list(devices.values())

    async def get_user_accounts_number(self):
        """
        get the number of user accounts
        """
        return await self._token_store.active_account_count()

    @api_status
    async def login(self):
        """
        Login to get access token.
        """
        data = {"MemId": self.email, "PW": self.password, "AppToken": APP_TOKEN}
        response = await self.request(
            method="POST", headers={}, data=data, endpoint=apis.open_session()
        )
        self._cp_token = response.get("CPToken", "")
        self._refresh_token = response.get("RefreshToken", "")
        self._token_timeout = response.get("TokenTimeOut", "")
        self._refresh_token_timeout = response.get("RefreshTokenTimeOut", "")
        self._mversion = response.get("MVersion", "")

    @api_status
    async def refresh_token(self):
        """
        refresh access token.
        """
        if self._refresh_token is None:
            raise Ems2LoginFailed

        data = {"RefreshToken": self._refresh_token}
        response = await self.request(
            method="POST", headers={}, data=data, endpoint=apis.refresh_token()
        )
        self._cp_token = response.get("CPToken", "")
        self._refresh_token = response.get("RefreshToken", "")
        self._token_timeout = response.get("TokenTimeOut", "")
        self._refresh_token_timeout = response.get("RefreshTokenTimeOut", "")
        self._mversion = response.get("MVersion", "")

    @api_status
    async def logout(self):
        """
        Logout the account
        """
        data = {}
        await self.request(
            method="POST", headers={}, data=data, endpoint=apis.close_session()
        )

    @api_status
    async def get_user_devices(self):
        """
        List devices that the user has permission
        """

        header = {"CPToken": self._cp_token}
        response = await self.request(
            method="GET", headers=header, endpoint=apis.get_user_devices()
        )
        if isinstance(response, dict):
            self._devices = response.get("GwList", [])
            self._commands = response.get("CommandList", [])

        return self._devices

    @api_status
    async def get_device_ip(self):
        """
        Get the ip of devices
        """
        idx = 0
        header = {"CPToken": self._cp_token}
        for device in self._devices:
            asyncio.sleep(.5)  # avoid to be banned
            gwid = device["GWID"]
            data = {"GWID": gwid}
            response = await self.request(
                method="POST", headers=header, data=data, endpoint=apis.get_gw_ip()
            )
            if isinstance(response, dict):
                self._devices[idx]["GWIP"] = response.get("data", None)
            idx = idx + 1

    def _workaround_info(self, model_type: str, command_type: str, status):
        """Apply known Panasonic cloud value normalizations."""
        return normalize_command_status(model_type, command_type, status)

    def _refactor_info(self, model_type: str, devices_info: list):
        """Refactor raw DeviceGetInfo payloads into status dictionaries."""
        return refactor_device_information(model_type, devices_info)

    @api_status
    async def get_device_with_info(self, device: dict, func: list):
        """
        Get device information
        """
        gwid = device["GWID"]
        if not gwid:
            _LOGGER.warning("GWID is not exist!")
            return {}

        header = {
            "CPToken": self._cp_token,
            "auth": device["Auth"],
            "GWID": gwid
        }
        data = []
        device_func = []
        for dev in device["Devices"]:
            if dev:
                device_id = dev.get("DeviceID", 1)
                device_func = self._get_device_commands(
                                device["DeviceType"],
                                device["ModelType"],
                                device["Model"],
                                device_id
                            )
                device_func.extend(func)
                data.append(
                    {"CommandTypes": device_func, "DeviceID": device_id}
                )
        response = await self.request(
            method="POST", headers=header, data=data, endpoint=apis.post_device_get_info()
        )

        info = []
        if response.get("status", "") == "success":
            info = self._refactor_info(
                self._devices_info[gwid]["ModelType"],
                response["devices"]
            )

        if len(info) >= 1:
            self._devices_info[gwid]["Information"] = info
        return info

    def _get_supplemental_keys(self, device: dict) -> list:
        """Return isolated supplemental command keys for this device/model."""
        return get_supplemental_keys(device, capability_registry=CAPABILITY_REGISTRY)

    @api_status
    async def _fetch_device_command_snapshot(self, device: dict, device_id, keys: list) -> dict:
        if not keys:
            return {}
        gwid = device.get("GWID")
        if not gwid:
            return {}
        header = {"CPToken": self._cp_token, "auth": device.get("Auth", ""), "GWID": gwid}
        data = [{"DeviceID": device_id, "CommandTypes": [{"CommandType": k} for k in keys]}]
        response = await self.request(method="POST", headers=header, data=data, endpoint=apis.post_device_get_info())
        snapshot = {}
        if response.get("status", "") != "success":
            return snapshot
        model_type = device.get("ModelType", "")
        for dev in response.get("devices", []):
            if dev.get("DeviceID") != device_id:
                continue
            for info in dev.get("Info", []):
                cmd_type, status = self._workaround_info(model_type, info.get("CommandType"), info.get("status"))
                if cmd_type in keys:
                    snapshot[cmd_type] = status
        return snapshot

    def _merge_supplemental_status(self, info_list: list, supplemental_by_device_id: dict) -> list:
        return merge_supplemental_status(info_list, supplemental_by_device_id)

    def _get_commands(self, device_type, model_type, model):
        """
        get commands (saa: service code)
        """
        return build_polling_command_types(
            device_type,
            model_type,
            has_remote_commands=bool(self._commands),
            capability_registry=CAPABILITY_REGISTRY,
            model_jp_types=MODEL_JP_TYPES,
        )

    def _get_device_commands(self, device_type, model_type, model, device_id):
        """
        get commands (saa: service code)
        """
        return build_light_device_command_types(device_type, model, device_id)

    def _refactor_cmds_paras(self, commands_list: dict) -> list:
        """
        refactor the status of information for easy use
        """
        self._commands_info = refactor_command_metadata(
            commands_list,
            washing_machine_models=WASHING_MACHINE_MODELS,
            washing_machine_2020_models=WASHING_MACHINE_2020_MODELS,
            washing_machine_operating_status=WASHING_MACHINE_OPERATING_STATUS,
            washing_machine_timer_remaining_time=WASHING_MACHINE_TIMER_REMAINING_TIME,
        )

    def _offline_info(self, device_type, model_type):
        """Return fallback offline Information rows."""
        return build_offline_information(
            device_type,
            model_type,
            capability_registry=CAPABILITY_REGISTRY,
        )

    def is_supported(self, model_type: str):
        """is model type supported

        Args:
            model_type (str): return True if supported
        """

        return True

    def _user_info_statistics_requests(self, now=None):
        """Build UserGetInfo statistics query ranges."""
        return build_user_info_statistics_requests(now)


    def _user_info_external_statistics(self, info_type, range_key, labels, response):
        """Convert UserGetInfo bucket values to recorder external statistics rows."""
        rows = []
        unit_class_map = {
            "energy": EnergyConverter.UNIT_CLASS,
            "volume": VolumeConverter.UNIT_CLASS,
        }
        unit_map = {
            "kWh": UnitOfEnergy.KILO_WATT_HOUR,
            "L": UnitOfVolume.LITERS,
        }

        metrics = parse_user_info_series(
            info_type,
            response,
            self._devices_info,
            washing_machine_device_type=str(DEVICE_TYPE_WASHING_MACHINE),
        )
        for row in build_user_info_external_statistics_rows(
            metrics=metrics,
            labels=labels,
            range_key=range_key,
            devices_info=self._devices_info,
            domain=DOMAIN,
            timezone=local_tz,
        ):
            metadata = row["metadata"]
            rows.append(
                {
                    "metadata": StatisticMetaData(
                        mean_type=StatisticMeanType.NONE,
                        has_sum=metadata["has_sum"],
                        name=metadata["name"],
                        source=metadata["source"],
                        statistic_id=metadata["statistic_id"],
                        unit_class=unit_class_map.get(
                            metadata["unit_class"], metadata["unit_class"]
                        ),
                        unit_of_measurement=unit_map.get(
                            metadata["unit_of_measurement"], metadata["unit_of_measurement"]
                        ),
                    ),
                    "statistics": [StatisticData(**data) for data in row["statistics"]],
                    "range_key": row["range_key"],
                }
            )
        return rows

    async def _update_user_info_statistics(self, header):
        """Fetch low-frequency UserGetInfo series and import them as recorder statistics."""
        now = datetime.today()
        if (
            self._user_info_series_last_update is not None
            and (now - self._user_info_series_last_update).total_seconds() < USER_INFO_SERIES_REFRESH_SECONDS
        ):
            return True

        has_washer = any(
            device.get("DeviceType") == str(DEVICE_TYPE_WASHING_MACHINE)
            for device in self._devices_info.values()
        )
        info_types = ["Power"] + (["Other"] if has_washer else [])

        for request in self._user_info_statistics_requests(now):
            for info_type in info_types:
                data = dict(request["data"])
                data["name"] = info_type
                response = await self.request(
                    method="POST", headers=header, data=data, endpoint=apis.get_user_info()
                )
                if "GwList" not in response:
                    continue
                for row in self._user_info_external_statistics(
                    info_type,
                    request["range_key"],
                    request["labels"],
                    response,
                ):
                    async_add_external_statistics(
                        self.hass,
                        row["metadata"],
                        row["statistics"],
                    )
        self._user_info_series_last_update = now
        return True

    @api_status
    async def get_user_info(self):
        """ get user info

        Returns:
            bool: is user info got
        """
        header = {"CPToken": self._cp_token}
        data = {
            "name": "",
            "from": datetime.today().replace(day=1).strftime("%Y/%m/%d"),
            "unit": "day",
            "max_num": 31,
        }
        for info in USER_INFO_TYPES:
            data["name"] = info
            response = await self.request(
                method="POST", headers=header, data=data, endpoint=apis.get_user_info()
            )

            if "GwList" not in response:
                return False
            for gwinfo in response["GwList"]:
                if not isinstance(gwinfo, dict):
                    continue
                gwid = gwinfo["GwID"]
                if "Information" not in self._devices_info.get(gwid, {}):
                    continue
                device_type = self._devices_info[gwid]["DeviceType"]
                if info == "Other":
                    if device_type == str(DEVICE_TYPE_FRIDGE):
                        self._devices_info[gwid]["Information"][0]["status"][ENTITY_DOOR_OPENS] = gwinfo["Ref_OpenDoor_Total"]
                    if device_type == str(DEVICE_TYPE_WASHING_MACHINE):
                        self._devices_info[gwid]["Information"][0]["status"][ENTITY_WASH_TIMES] = gwinfo["WM_WashTime_Total"]
                        self._devices_info[gwid]["Information"][0]["status"][ENTITY_WATER_USED] = gwinfo["WM_WaterUsed_Total"]
                if info == "Power":
                    if device_type == str(DEVICE_TYPE_DEHUMIDIFIER):
                        self._devices_info[gwid]["Information"][0]["status"][ENTITY_MONTHLY_ENERGY] = float(gwinfo.get("Total_kwh", 0))
                    if device_type == str(DEVICE_TYPE_FRIDGE):
                        self._devices_info[gwid]["Information"][0]["status"][ENTITY_MONTHLY_ENERGY] = float(gwinfo.get("Total_kwh", 0))
                    if device_type == str(DEVICE_TYPE_WASHING_MACHINE):
                        self._devices_info[gwid]["Information"][0]["status"][ENTITY_MONTHLY_ENERGY] = float(gwinfo.get("Total_kwh", 0))

        await self._update_user_info_statistics(header)
        return True

    @api_status
    async def get_update_info(self, check=False):
        """ get udpate info

        Returns:
            bool: is update info got
        """

        if not check:
            for gwid in self._devices_info.keys():
                if "Information" in self._devices_info[gwid]:
                    self._devices_info[gwid]["Information"][0]["status"][ENTITY_UPDATE] = self._update_info.get(gwid, False)
            return False

        for gwid in self._devices_info.keys():
            if len(self._update_info) < 1:
                self._update_info[gwid] = False
            if "Information" in self._devices_info[gwid]:
                self._devices_info[gwid]["Information"][0]["status"][ENTITY_UPDATE] = False

        header = {"CPToken": self._cp_token, "apptype": "Smart"}
        response = await self.request(
            method="GET", headers=header, endpoint=apis.get_update_info()
        )

        if "GwList" in response:
            idx = 0
            for gwinfo in response["GwList"]:
                gwid = gwinfo.get("GwID", None)
                if gwid and "Information" not in self._devices_info[gwid]:
                    continue

                self._update_info[gwid] = True
                self._devices_info[gwid]["Information"][0]["status"][ENTITY_UPDATE] = True
                self._devices_info[gwid]["Information"][0]["status"][ENTITY_UPDATE_INFO] = response["UpdateInfo"][idx].get("updateVersion", "")
                idx = idx + 1
        return True

    @api_status
    async def get_plate_info(self, device, check=False):
        """ get weight plate info

        Returns:
        """

        if not check:
            return
        gwid = device["GWID"]
        header = {
            "CPToken": self._cp_token,
            "auth": device["Auth"],
            "GWID": gwid
        }
        response = await self.request(
            method="GET", headers=header, endpoint=apis.get_plate_mode()
        )
        info = {}
        if isinstance(response, dict):
            if "State" in response and response["State"] == "success":
                info[WEIGHT_PLATE_FOOD_NAME] = response.get("Name", "")
                info[WEIGHT_PLATE_MANAGEMENT_MODE] = response.get("ManagementMode", None)
                info[WEIGHT_PLATE_MANAGEMENT_VALUE] = response.get("ManagementValue", None)
                info[WEIGHT_PLATE_AMOUNT_MAX] = response.get("AmountMax", None)

                dt = response.get("BuyDate", None)
                info[WEIGHT_PLATE_BUY_DATE] = datetime.fromtimestamp(int(dt), local_tz) if isinstance(dt, str) else None
                dt = response.get("DueDate", None)
                info[WEIGHT_PLATE_DUE_DATE] = datetime.fromtimestamp(int(dt), local_tz) if isinstance(dt, str) else None
                info[WEIGHT_PLATE_COMMUNICATION_MODE] = response.get("CommunicationMode", None)
                info[WEIGHT_PLATE_COMMUNICATION_TIME] = response.get("CommunicationTime", None)
                info[WEIGHT_PLATE_TOTAL_WEIGHT] = response.get("TotalWeight", None)
                info[WEIGHT_PLATE_RESTORE_WEIGHT] = response.get("RestoreWeight", None)
                info[WEIGHT_PLATE_LOW_BATTERY] = response.get("LowBattery", None)
            else:
                info[WEIGHT_PLATE_FOOD_NAME] = None
                info[WEIGHT_PLATE_MANAGEMENT_MODE] = None
                info[WEIGHT_PLATE_MANAGEMENT_VALUE] = None
                info[WEIGHT_PLATE_AMOUNT_MAX] = None
                info[WEIGHT_PLATE_BUY_DATE] = None
                info[WEIGHT_PLATE_DUE_DATE] = None
                info[WEIGHT_PLATE_COMMUNICATION_MODE] = None
                info[WEIGHT_PLATE_COMMUNICATION_TIME] = None
                info[WEIGHT_PLATE_TOTAL_WEIGHT] = None
                info[WEIGHT_PLATE_RESTORE_WEIGHT] = None
                info[WEIGHT_PLATE_LOW_BATTERY] = None
            self._devices_info[gwid]["Information"] = [{'DeviceID': 1, 'status': info}]

    @api_status
    async def get_devices_with_info(self):
        """
        Get devices information
        """
        get_update_info = False
        if self._api_counts_per_hour < 5:
            get_update_info = True

        devices = await self.get_user_devices()
        for cmd in self._commands:
            self._commands_info[cmd['ModelType']] = cmd["JSON"]
        self._refactor_cmds_paras(self._commands_info)

        await asyncio.sleep(.5)

        header = {
            "CPToken": self._cp_token,
            "apptype": "Smart"
        }
        response = await self.request(
            method="GET", headers=header, endpoint=apis.get_device_status()
        )

        gwid_status = {}
        if "GwList" in response:
            for dev in response["GwList"]:
                gwid = dev["GWID"]
                status = ""
                for info in dev["List"]:
                    if info.get("CommandType", "") == "0x00":
                        status = info["Status"]
                        break
                    if info.get("CommandType", "") == "0x50": # Washing Machine
                        status = info["Status"]
                        break
                    if info.get("CommandType", "") == "0x65": # Fridge
                        status = info["Status"]
                        break
                    if info.get("CommandType", "") == "0x63": # JP Fridge
                        status = info["Status"]
                        break
                    if info.get("Status", "") != "":
                        status = info["Status"]
                        break
                gwid_status[gwid] = status

        for device in devices:
            gwid = device["GWID"]
            device_type = device["DeviceType"]
            model_type = device["ModelType"]
            model = device["Model"]

            if len(self._select_devices) >= 1:
                if gwid not in self._select_devices:
                    continue

            if gwid not in self._devices_info:
                # _LOGGER.warning(f"gwid not in self._devices_info!")
                self._devices_info[gwid] = device
                gwid_status[gwid] = "force update"

            if device_type == str(DEVICE_TYPE_WEIGHT_PLATE):
                await asyncio.sleep(.1)
                await self.get_plate_info(device, get_update_info)
                continue

            if device_type == str(DEVICE_TYPE_LIGHT):
                gwid_status[gwid] = "force update"

            if len(gwid_status[gwid]) < 1:
                # No status code, it maybe offline or power off of washing machine or network busy
                # _LOGGER.warning(f"gwid {gwid} is offline {self._devices_info[gwid]}!")
                if device_type in [str(DEVICE_TYPE_WASHING_MACHINE)]:
                    # Panasonic cloud 對洗衣機偶發回空 status 時，只能視為 transient unknown。
                    # 保留上一筆有效 Information；沒有上一筆時才設為空，避免把 0x74/0x50 等狀態 fake 成 0。
                    self._devices_info[gwid].setdefault("Information", [])
                continue

            if not self.is_supported(model_type):
                continue
            command_types = self._get_commands(
                device_type,
                model_type,
                model
            )
            await asyncio.sleep(.1)
            await self.get_device_with_info(device, command_types)

            supp_keys = self._get_supplemental_keys(device)
            if supp_keys and "Information" in self._devices_info.get(gwid, {}):
                supplemental_by_device_id = {}
                for dev in device.get("Devices", []):
                    if not dev:
                        continue
                    device_id = dev.get("DeviceID", 1)
                    await asyncio.sleep(.1)
                    snap = await self._fetch_device_command_snapshot(device, device_id, supp_keys)
                    snap = filter_supplemental_snapshot(snap, supp_keys)
                    if snap:
                        supplemental_by_device_id[device_id] = snap
                if supplemental_by_device_id:
                    self._merge_supplemental_status(
                        self._devices_info[gwid]["Information"],
                        supplemental_by_device_id,
                    )
        await self.get_user_info()
        await self.get_update_info(get_update_info)

        return self._devices_info

    @api_status
    async def update_device(self, gwid:str, device_id):
        """
        Update device status
        """
        device = self._devices_info.get(gwid, None)
        if not device:
            return

        command_types = self._get_commands(
            device["DeviceType"],
            device["ModelType"],
            device["Model"]
        )
        await self.get_device_with_info(device, command_types)

        supp_keys = self._get_supplemental_keys(device)
        info_list = self._devices_info.get(gwid, {}).get("Information", [])
        if not supp_keys or not info_list:
            return

        supplemental_by_device_id = {}
        target_ids = {device_id}
        for dev in device.get("Devices", []):
            if dev.get("DeviceID") in target_ids:
                await asyncio.sleep(.1)
                snapshot = await self._fetch_device_command_snapshot(device, dev.get("DeviceID"), supp_keys)
                snapshot = filter_supplemental_snapshot(snapshot, supp_keys)
                if snapshot:
                    supplemental_by_device_id[dev.get("DeviceID")] = snapshot

        if supplemental_by_device_id:
            self._devices_info[gwid]["Information"] = self._merge_supplemental_status(
                self._devices_info[gwid]["Information"],
                supplemental_by_device_id,
            )

    @api_status
    async def set_device(self, gwid: str, device_id, func: str, value):
        """
        Set device status
        """
        auth = ""

        if "Auth" in self._devices_info[gwid]:
            auth = self._devices_info[gwid]["Auth"]
        if len(auth) <= 1:
            _LOGGER.error(f"There is no auth for {gwid}!")
            return
        device_type = self._devices_info[gwid]["DeviceType"]
        cmd = set_command_id(CAPABILITY_REGISTRY, device_type, func)
        if cmd is None:
            _LOGGER.error(f"There is no cmd for {gwid}: {func}!")
            return

        header = {"CPToken": self._cp_token, "auth": auth}
        param = {"DeviceID": device_id, "CommandType": cmd, "Value": value}

        await self.request(
            method="GET", headers=header, endpoint=apis.set_device(), params=param
        )

    def get_command_name(self, device_gwid:str, command: str) -> str:
        """
        Args:
            device_gwid (str): the gwid of device

        Returns:
            str: the name of command
        """
        if device_gwid not in self._devices_info:
            return None

        model_type = self._devices_info[device_gwid]["ModelType"]
        device_type = self._devices_info[device_gwid]["DeviceType"]
        override = command_name_override(CAPABILITY_REGISTRY, device_type, command)
        if override is not None:
            return override

        if model_type not in self._commands_info:
            return None
        cmds_list = self._commands_info[model_type]
        for cmds in cmds_list:
            if device_type == cmds["DeviceType"]:
                cmd_name = cmds.get("CommandName", None)
                if cmd_name:
                    return cmd_name.get(command, None)

        return None

    def get_range(self, device_gwid:str, command: str) -> dict:
        """
        Args:
            device_gwid (str): the gwid of device

        Returns:
            dict: the range dict
        """
        rng = {}
        if device_gwid not in self._devices_info:
            return rng

        model_type = self._devices_info[device_gwid]["ModelType"]
        device_type = self._devices_info[device_gwid]["DeviceType"]
        override = command_range_override(CAPABILITY_REGISTRY, device_type, command)
        if override is not None:
            return override

        candidates = range_lookup_models(
            CAPABILITY_REGISTRY,
            device_type,
            model_type,
            command,
        )

        for candidate in candidates:
            if candidate not in self._commands_info:
                continue
            cmds_list = self._commands_info[candidate]
            for cmds in cmds_list:
                if device_type != cmds["DeviceType"]:
                    continue
                cmd_para = cmds.get("CommandParameters", None)
                if not cmd_para:
                    continue
                found = cmd_para.get(command, {})
                if found:
                    return found
                if not rng:
                    rng = found
                break

        return rng

    async def async_load_tokens(self) -> dict:
        """
        Update tokens in .storage
        """
        tokens = await self._token_store.load_tokens()

        def current_tokens():
            return {
                CONF_CPTOKEN: self._cp_token,
                CONF_TOKEN_TIMEOUT: self._token_timeout,
                CONF_REFRESH_TOKEN: self._refresh_token,
                CONF_REFRESH_TOKEN_TIMEOUT: self._refresh_token_timeout
            }

        self._token_store.async_listen_save_on_stop(current_tokens)
        return tokens

    async def async_store_tokens(self, tokens: dict):
        """
        Update tokens in .storage
        """
        await self._token_store.store_tokens(tokens)

    @api_status
    async def async_check_tokens(self, tokens=None):
        """
        check token is vaild
        """
        if tokens is None:
            tokens = await self.async_load_tokens()
        cptoken = tokens.get(CONF_CPTOKEN, "")
        token_timeout = tokens.get(
            CONF_TOKEN_TIMEOUT, None)
        refresh_token = tokens.get(CONF_REFRESH_TOKEN, "")
        refresh_token_timeout = tokens.get(
            CONF_REFRESH_TOKEN_TIMEOUT, None)

        if token_timeout is None:
            token_timeout = "20200101010100"
        if (refresh_token_timeout is None or
                isinstance(refresh_token_timeout, str) and len(refresh_token_timeout) < 1):
            refresh_token_timeout = "20200101010100"

        now = datetime.now()
        updated_refresh_token = False
        timeout = datetime(
            int(refresh_token_timeout[:4]),
            int(refresh_token_timeout[4:6]),
            int(refresh_token_timeout[6:8]),
            int(refresh_token_timeout[8:10]),
            int(refresh_token_timeout[10:12]),
            int(refresh_token_timeout[12:])
        )

        if (int(timeout.timestamp() - now.timestamp()) < 300):
            # The maximal API access is 10 per hour
            await self.login()

            updated_refresh_token = True
            cptoken = self._cp_token
            token_timeout = self._token_timeout
            refresh_token = self._refresh_token
            refresh_token_timeout = self._refresh_token_timeout
            await self.async_store_tokens({
                CONF_CPTOKEN: cptoken,
                CONF_TOKEN_TIMEOUT: token_timeout,
                CONF_REFRESH_TOKEN: refresh_token,
                CONF_REFRESH_TOKEN_TIMEOUT: refresh_token_timeout,
            })
            self._api_counts_per_hour = 0
            self._api_client.api_counts_per_hour = 0

        timeout = datetime(
            int(token_timeout[:4]),
            int(token_timeout[4:6]),
            int(token_timeout[6:8]),
            int(token_timeout[8:10]),
            int(token_timeout[10:12]),
            int(token_timeout[12:])
        )

        if ((int(timeout.timestamp() - now.timestamp()) < 300) and
                not updated_refresh_token):
            self._refresh_token = refresh_token
            await self.refresh_token()

            cptoken = self._cp_token
            token_timeout = self._token_timeout
            refresh_token = self._refresh_token
            refresh_token_timeout = self._refresh_token_timeout
            await self.async_store_tokens({
                CONF_CPTOKEN: cptoken,
                CONF_TOKEN_TIMEOUT: token_timeout,
                CONF_REFRESH_TOKEN: refresh_token,
                CONF_REFRESH_TOKEN_TIMEOUT: refresh_token_timeout,
            })
            self._api_counts_per_hour = 0
            self._api_client.api_counts_per_hour = 0
        else:
            self._cp_token = cptoken
            self._token_timeout = token_timeout
            self._refresh_token = refresh_token
            self._refresh_token_timeout = refresh_token_timeout

        return {
            CONF_CPTOKEN: cptoken,
            CONF_TOKEN_TIMEOUT: token_timeout,
            CONF_REFRESH_TOKEN: refresh_token,
            CONF_REFRESH_TOKEN_TIMEOUT: refresh_token_timeout,
        }

#    @api_status
    async def async_update_data(self):
        """
        Update data
        """
        now = datetime.now()
        self._update_timestamp = now.timestamp()

        await self.async_check_tokens(
            {
                CONF_CPTOKEN: self._cp_token,
                CONF_TOKEN_TIMEOUT: self._token_timeout,
                CONF_REFRESH_TOKEN: self._refresh_token,
                CONF_REFRESH_TOKEN_TIMEOUT: self._refresh_token_timeout,
            }
        )

        try:
            ret = await self.get_devices_with_info()
            self.hass.data[DOMAIN]["api_counts"] = self._api_counts
            self.hass.data[DOMAIN]["api_counts_per_hour"] = self._api_counts_per_hour
            return ret
        except:
            raise UpdateFailed("Failed while updating device status")

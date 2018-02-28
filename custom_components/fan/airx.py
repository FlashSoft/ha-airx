"""
Airx空气净化器插件
@author: FlashSoft
@created: 2018-02-28
@updated: 2018-02-28
@version: 0.01
@yaml example:
fan:
  - platform: airx
    name: airx
    # 以下信息可通过 https://bbs.hassbian.com/thread-2113-1-1.html 这个帖子里的办法获取
    token: airx000000000000000000000000
    user_id: 000000
    device_id: 000000
"""
import logging
import datetime
import requests
import time

from homeassistant.components.fan import (FanEntity)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = datetime.timedelta(seconds=3)

DEFAULT_NAME = 'airx'

ATTR_PM25 = 'pm25'
ATTR_REMAIN = 'filter_remain'

SPEED_OFF = '关闭'
SPEED_AUTO = '自动'
SPEED_SILENT = '静音'
SPEED_LOW = '低'
SPEED_MEDIUM = '中'
SPEED_HIGH = '高'
SPEED_INTOLERABLE = '最高'

SPEED_MAP = {
    1: SPEED_SILENT,
    2: SPEED_LOW,
    3: SPEED_MEDIUM,
    4: SPEED_HIGH,
    5: SPEED_INTOLERABLE,
}
CONTROL_MAP = {
    SPEED_AUTO: [0, 1],
    SPEED_SILENT: [3, 1],
    SPEED_LOW: [3, 2],
    SPEED_MEDIUM: [3, 3],
    SPEED_HIGH: [3, 4],
    SPEED_INTOLERABLE: [3, 5]
}


def setup_platform(hass, config, add_devices_callback, discovery_info=None):
    name = config.get('name') or DEFAULT_NAME
    token = config.get('token')
    user_id = config.get('user_id')
    device_id = config.get('device_id')
    _LOGGER.info('============= airx setup -> name: %s =============', name)
    add_devices_callback([AirxFan(hass, name, token, user_id, device_id)])


# Airx的静态控制器类
class AirxController:
    lock = None

    @staticmethod
    def open(self):
        _LOGGER.info('============= airx turn on =============')
        AirxController.lock = time.time()
        api = 'http://luxcar.com.cn/airx/airx_iot_reportup/web/equipment/DeviceOnOrDown'
        res = requests.post(
            api,
            data={
                'userId': self._user_id,
                'token': self._token,
                'device_id': self._device_id,
                'standby': 0
            })
        json = res.json()
        _LOGGER.info('open: %s', json)
        if json['success'] is True:
            pass

    @staticmethod
    def close(self):
        _LOGGER.info('============= airx turn off =============')
        AirxController.lock = time.time()
        api = 'http://luxcar.com.cn/airx/airx_iot_reportup/web/equipment/DeviceOnOrDown'
        res = requests.post(
            api,
            data={
                'userId': self._user_id,
                'token': self._token,
                'device_id': self._device_id,
                'standby': 1
            })
        json = res.json()
        _LOGGER.info('close: %s', json)
        if json['success'] is True:
            pass

    @staticmethod
    def set_speed(self, speed):
        _LOGGER.info('============= airx set speed: %s =============', speed)
        AirxController.lock = time.time()

        api = 'http://luxcar.com.cn/airx/airx_iot_reportup/web/equipment/DeviceControl'

        set_mode = CONTROL_MAP[speed][0]
        set_speed = CONTROL_MAP[speed][1]

        res = requests.post(
            api,
            data={
                'userId': self._user_id,
                'token': self._token,
                'device_id': self._device_id,
                'mode': set_mode,
                'speed': set_speed
            })
        json = res.json()
        _LOGGER.info('set_speed: %s, %s, %s', set_mode, set_speed, json)

    @staticmethod
    def status(self):
        global STATE_PM25, STATE_REMAIN
        _LOGGER.info('============= airx update =============')

        # 由于airx的接口写操作完成后获取到新内容有延迟
        # 为避免接口返回的旧数据对界面还原有影响
        # 故增加锁5秒操作
        if (AirxController.lock is
                not None) and (time.time() - AirxController.lock < 5):
            _LOGGER.info('============= airx update: return =============')
            return

        api = 'http://luxcar.com.cn/airx/airx_iot_reportup/web/equipment/loadDeviceData'
        res = requests.post(
            api,
            data={
                'userId': self._user_id,
                'token': self._token,
                'device_id': self._device_id
            })
        json = res.json()
        _LOGGER.info('status: %s', json)
        self._state_remain = json['data']['FilterRemain']
        self._state_pm25 = json['data']['pm25']

        speed = None

        if json['data']['standby'] == 0:
            if json['data']['PuriOperationMode'] == 0:
                speed = SPEED_AUTO
            else:
                speed = SPEED_MAP[json['data']['AirSpeed']]
        elif json['data']['standby'] == 1:
            speed = SPEED_OFF

        self._speed = speed


class AirxFan(FanEntity):
    def __init__(self, hass, name: str, token: str, user_id: str,
                 device_id: str) -> None:
        self._hass = hass
        self._name = name
        self._token = token
        self._user_id = user_id
        self._device_id = device_id
        self._speed = None
        self._state_pm25 = None
        self._state_remain = None

    @property
    def name(self) -> str:
        return self._name

    @property
    def should_poll(self):
        return True

    @property
    def speed(self) -> str:
        return self._speed

    @property
    def speed_list(self) -> list:
        return [
            SPEED_OFF, SPEED_AUTO, SPEED_SILENT, SPEED_LOW, SPEED_MEDIUM,
            SPEED_HIGH, SPEED_INTOLERABLE
        ]

    def turn_on(self, speed: str, **kwargs) -> None:
        if speed == SPEED_OFF:
            self.turn_off()
            return
        if speed is None:
            speed = SPEED_AUTO

        AirxController.open(self)
        AirxController.set_speed(self, speed)
        self._speed = speed
        self.schedule_update_ha_state()

    def turn_off(self, **kwargs) -> None:

        AirxController.close(self)
        self._speed = SPEED_OFF
        self.schedule_update_ha_state()

    @property
    def is_on(self) -> bool:
        return SPEED_OFF != self._speed

    def update(self) -> None:
        AirxController.status(self)

    @property
    def device_state_attributes(self):
        return {ATTR_PM25: self._state_pm25, ATTR_REMAIN: self._state_remain}

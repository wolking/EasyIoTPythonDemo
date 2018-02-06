# encoding: utf-8

import random
import string
import requests
from collections import namedtuple


TestEnv = namedtuple('TestEnv', ['Protocol', 'Host', 'Port', 'CorrectUsername',
                                 'CorrectPassword', 'ServiceName', 'DeviceCategory', 'DeviceType',
                                 'CallbackUrl', 'CmdDevSerial'])


GlTestEnv39_http_domain = TestEnv(
    Protocol='http',
    Host='www.easy-iot.cn',
    Port=80,
    CorrectUsername='jhdevtest',
    CorrectPassword='123456',
    ServiceName='DeveloperDeviceService',
    DeviceCategory='Light',
    DeviceType='FLOOR10',
    CallbackUrl='http://121.14.12.237:28080',
    CmdDevSerial='863301010100001',
)


def currentEnv():
    '''select env'''
    return GlTestEnv39_https_domain


def combine_url(api_url):
    return '%s://%s:%d%s' % (currentEnv().Protocol, currentEnv().Host, currentEnv().Port, api_url)


random_name = lambda length: ''.join(random.choice(string.hexdigits) for _ in range(length))


def iterable(o):
    try:
        iter(o)
        return True
    except TypeError:
        return False


def api(url, method, args):
    login_obj = {
        'serverId': currentEnv().CorrectUsername,
        'password': currentEnv().CorrectPassword
    }
    rsp = requests.request("POST", combine_url('/idev/3rdcap/server/login'), json=login_obj, timeout=30)
    print(rsp.content)
    assert 'optResult' in rsp.json()
    assert rsp.json()['optResult'] == '0'
    assert len(rsp.json()['accessToken']) == 32
    token = rsp.json()['accessToken']
    headers = {
        'serverID': currentEnv().CorrectUsername,
        'accessToken': token
    }
    if method in ['GET', 'DELETE']:
        result = requests.request(method, combine_url(url), params=args, headers=headers, timeout=30)
        print(result.content)
        return result
    elif method in ['PUT', 'POST']:
        result = requests.request(method, combine_url(url), json=args, headers=headers, timeout=30)
        print(result.content)
        return result


def test_login_fail():
    '''
    测试登录失败的情况
    :return:
    '''
    login_obj = {
        'serverId': random_name(12),
        'password': random_name(11)
    }
    rsp = requests.request("POST", combine_url('/idev/3rdcap/server/login'), json=login_obj, timeout=30)
    assert 'optResult' in rsp.json()
    assert rsp.json()['optResult'] == "1007"
    print(rsp.content)


def choosePoint():
    rspobj = get_iot_servers()
    return random.choice(rspobj['iotserverList'])["id"]


def dev_register(devSerial, devName):
    connectPointId = choosePoint()
    obj = {
        'devSerial': devSerial,
        'name': devName,
        'deviceType': currentEnv().DeviceType,
        'connectPointId': connectPointId,
        'endUserName': 'TEST1',
        'endUserInfo': '10617192371927391',
    }
    rsp = api('/idev/3rdcap/devices/reg-device', "POST", obj)
    return rsp


def test_dev_register():
    '''
    测试单设备成功注册.
    '''
    rsp = dev_register('TEST$_%s' % random_name(4), random_name(10))
    assert 'optResult' in rsp.json()
    assert rsp.json()['optResult'] == '0'
    assert 'deviceId' in rsp.json()
    assert rsp.json()['deviceId']


def test_dev_registe_fail1():
    '''
    测试单设备失败注册1.
    '''
    r0 = dev_register('', random_name(10))
    assert 'optResult' in r0.json()
    assert r0.json()['optResult'] == '1014'
    '''
    obj1 = {
        'devSerial': 'TEST$_%s' % random_name(4),
        'deviceType': currentEnv().DeviceType,
    }
    r1 = api('/idev/3rdcap/devices/reg-device', "POST", obj1)
    assert 'optResult' in r1.json()
    assert r1.json()['optResult'] == "0"
    '''


def test_dev_register_min_info():
    '''
    测试单设备注册，主要测试 路由
    '''
    connectPointId = choosePoint()
    obj1 = {
        'devSerial': 'TEST$_%s' % random_name(4),
        'deviceType': currentEnv().DeviceType,
        'connectPointId': connectPointId,
    }
    r1 = api('/idev/3rdcap/devices/reg-device', "POST", obj1)
    assert 'optResult' in r1.json()
    assert r1.json()['optResult'] == "0"
    assert len(r1.json()['deviceId']) > 0


def test_dev_registe_fail_connect_router():
    '''
    测试单设备失败注册2.
    用例已过期，现使用 连接点 路由
    '''
    obj2 = {
        'devSerial': 'TEST$_%s' % random_name(4),
        'deviceType': currentEnv().DeviceType,
    }
    r2 = api('/idev/3rdcap/devices/reg-device', "POST", obj2)
    assert 'optResult' in r2.json()
    assert r2.json()['optResult'] == "1505"


def test_dev_registe_fail3():
    '''
    测试单设备失败注册3.
    '''

    obj3 = {
        'deviceType': currentEnv().DeviceType,
    }
    r3 = api('/idev/3rdcap/devices/reg-device', "POST", obj3)
    assert 'optResult' in r3.json()
    assert r3.json()['optResult'] == "1014"


def update_device_info(devSerial):
    '''
    测试更新单个设备信息
    '''
    obj = {
        'devSerial': devSerial,
        'name': 'temp',
        'endUserName': 'TEST2',
        'endUserInfo': '92371927312391',
    }
    rsp = api('/idev/3rdcap/devices/update-device', "PUT", obj)
    return rsp


def test_update_nondev_fail():
    r1 = update_device_info('hello,worldddddd %s' % random_name(10))
    assert 'optResult' in r1.json()
    assert r1.json()['optResult'] == '1005'


def delete_device(devSerial):
    obj = {'devSerial': devSerial}
    rsp = api('/idev/3rdcap/devices/del-device', "DELETE", obj)
    return rsp


def _test_delete_dev_fail_noperm():
    r1 = delete_device('863703030451517')
    assert 'optResult' in r1.json()


def test_delete_dev_fail():
    r1 = delete_device('hello,worldddddd %s' % random_name(10))
    assert 'optResult' in r1.json()
    assert r1.json()['optResult'] == '1005'


def test_dev_batch_register():
    '''
    测试批量设备注册.
    '''
    connectPointId = choosePoint()
    obj = {
        'devices': [
            {
                'devSerial': 'TEST$_%s' % random_name(4),
                'name': random_name(10),
                'deviceType': currentEnv().DeviceType,
                'connectPointId': connectPointId,
                'endUserName': 'TEST1',
                'endUserInfo': '10617192371927391'
            },
            {
                'devSerial': 'TEST$_%s' % random_name(4),
                'name': random_name(10),
                'deviceType': currentEnv().DeviceType,
                'connectPointId': connectPointId,
                'endUserName': 'TEST1',
                'endUserInfo': '10617192371927391'
            },
            {
                'devSerial': 'TEST$_%s' % random_name(4),
                'name': random_name(10),
                'deviceType': currentEnv().DeviceType,
                'connectPointId': connectPointId,
                'endUserName': 'TEST1',
                'endUserInfo': '10617192371927391'
            }
        ]
    }
    rsp = api('/idev/3rdcap/devices/reg-device-batch', "POST", obj)
    assert 'optResult' in rsp.json()
    assert rsp.json()['optResult'] == '0'
    assert 'taskID' in rsp.json()
    assert rsp.json()['taskID']


def test_list_device():
    '''
    测试列出用户所有设备
    '''
    obj = {'serverID': currentEnv().CorrectUsername}
    rsp = api('/idev/3rdcap/devices/list-devices', "GET", obj)
    assert 'optResult' in rsp.json()
    assert rsp.json()['optResult'] == '0'


def test_list_devtypes():
    '''
    测试列出用户所有设备
    '''
    obj = {'serverID': currentEnv().CorrectUsername}
    rsp = api('/idev/3rdcap/devices/list-devtypes', "GET", obj)
    assert 'optResult' in rsp.json()
    assert rsp.json()['optResult'] == '0'
    assert 'devTypes' in rsp.json()


def device_allinfo(devSerial):
    '''
    测试获取设备详细信息
    :return:
    '''
    obj = {'devSerial': devSerial}
    rsp = api('/idev/3rdcap/devices/query-device-allinfo', "GET", obj)
    assert 'optResult' in rsp.json()
    assert rsp.json()['optResult'] == '0'


def test_get_all_device_allinfo():
    '''
    测试全部设备信息
    '''
    obj = {'serverID': currentEnv().CorrectUsername}
    rsp = api('/idev/3rdcap/devices/list-devices', "GET", obj)
    assert 'optResult' in rsp.json()
    assert rsp.json()['optResult'] == '0'
    devices = rsp.json()['devices']
    for dev in devices:
        device_allinfo(dev['devSerial'])


def test_get_device_allinfo_errdev():
    '''
    测试获取设备详细信息，在设备不存在时，错误码要正确。
    '''
    obj = {'devSerial': 'HELLO,WORLD'}
    rsp = api('/idev/3rdcap/devices/query-device-allinfo', "GET", obj)
    assert 'optResult' in rsp.json()
    assert rsp.json()['optResult'] == '1005'


def test_developer_dev_manage():
    '''
    测试设备管理流程
    '''
    devSer1 = 'TEST$_%s' % random_name(4)
    r1 = dev_register(devSer1, random_name(10))
    assert 'optResult' in r1.json()
    assert r1.json()['optResult'] == '0'
    assert 'deviceId' in r1.json()
    assert r1.json()['deviceId']

    ur1 = update_device_info(devSer1)
    assert 'optResult' in ur1.json()
    assert ur1.json()['optResult'] == '0'

    devSer2 = 'TEST$_%s' % random_name(4)
    r2 = dev_register(devSer2, random_name(10))
    assert 'optResult' in r2.json()
    assert r2.json()['optResult'] == '0'
    assert 'deviceId' in r2.json()
    assert r2.json()['deviceId']

    dr1 = delete_device(devSer1)
    assert 'optResult' in dr1.json()
    assert dr1.json()['optResult'] == '0'
    dr2 = delete_device(devSer2)
    assert 'optResult' in dr2.json()
    assert dr2.json()['optResult'] == '0'


def subscribe_data(cburl):
    url = '/idev/3rdcap/subscribe-service-address'
    obj = {
        'callbackUrl': cburl
    }
    rsp = api(url, "POST", obj)
    rspobj = rsp.json()
    return rspobj


def test_subscribe_url_failed():
    '''
    测试错误的订阅情况
    '''
    rsp1 = subscribe_data('')
    assert 'optResult' in rsp1
    assert rsp1['optResult'] == '1014'
    rsp1 = subscribe_data('ftp://123.1.1.2/path')
    assert 'optResult' in rsp1
    assert rsp1['optResult'] == '1014'


def test_remove_subscribe():
    '''
    测试删除订阅
    '''
    url = '/idev/3rdcap/unsubscribe-service-address'
    obj = {}
    rsp = api(url, "DELETE", obj)
    rspobj = rsp.json()
    assert 'optResult' in rspobj
    assert rspobj['optResult'] == '0'


def query_subscribe():
    url = '/idev/3rdcap/query-subscribe-service-address'
    rsp = api(url, "GET", {})
    return rsp.json()


def test_remove_subscribe_result():
    '''
    测试删除订阅结果
    '''
    url = '/idev/3rdcap/unsubscribe-service-address'
    obj = {}
    rsp = api(url, "DELETE", obj)
    rspobj = rsp.json()
    assert 'optResult' in rspobj
    assert rspobj['optResult'] == '0'
    rspobj = query_subscribe()
    assert 'optResult' in rspobj
    assert rspobj['optResult'] == '1602'


def test_subscribe_data():
    '''
    测试数据订阅与订阅修改
    '''
    cburl1 = 'http://127.0.0.1:12345/cburl'
    cburl2 = currentEnv().CallbackUrl
    rsp1 = subscribe_data(cburl1)
    assert 'optResult' in rsp1 and rsp1['optResult'] == '0'
    rsp2 = subscribe_data(cburl2)
    assert 'optResult' in rsp2 and rsp2['optResult'] == '0'


def test_query_subscribe():
    '''
    测试查询订阅地址
    '''
    cburl2 = currentEnv().CallbackUrl
    rsp1 = subscribe_data(cburl2)
    assert 'optResult' in rsp1 and rsp1['optResult'] == '0'
    rspobj = query_subscribe()
    assert 'optResult' in rspobj
    assert rspobj['optResult'] == '0'
    assert 'callbackUrl' in rspobj
    assert rspobj['callbackUrl'] == cburl2


def urt_command(devSerial, method, params):
    obj = {
        'devSerial': devSerial,
        'method': method,
        'params': params
    }
    rsp = api("/idev/3rdcap/dev-control/urt-command", "POST", obj)
    return rsp


def _test_urt_command():
    rsp = urt_command(currentEnv().CmdDevSerial, 'StatusCon', {
        "Status": "OFF",
    })
    assert 'optResult' in rsp.json()
    assert rsp.json()['optResult'] == '0'
    assert 'commandId' in rsp.json()


def get_iot_servers():
    url = '/idev/3rdcap/service-config/get-iotservers'
    rsp = api(url, "GET", {})
    return rsp.json()


def test_get_iotservers():
    '''
    测试 获取连接的平台列表
    '''
    rspobj = get_iot_servers()
    assert 'optResult' in rspobj
    assert rspobj['optResult'] == '0'
    assert 'iotserverList' in rspobj
    assert rspobj['iotserverList']
    assert iterable(rspobj['iotserverList'])
    assert len(rspobj['iotserverList']) > 0


def remove_created_dev():
    obj = {'serverID': currentEnv().CorrectUsername}
    rsp = api('/idev/3rdcap/devices/list-devices', "GET", obj)
    assert 'optResult' in rsp.json()
    assert rsp.json()['optResult'] == '0'
    if 'devices' not in rsp.json():
        print('no devices found.')
    devs = rsp.json()['devices']
    for item in devs:
        devSerial = item['devSerial']
        if devSerial.startswith('TEST$_') and len(devSerial) == (len('TEST$_') + 4):
            r1 = delete_device(item['devSerial'])
            assert 'optResult' in r1.json()
            assert r1.json()['optResult'] == '0'

"""
@Author: zhang_zhiyi
@Date: 2025/5/9_10:57
@FileName:equipment.py
@LastEditors: zhang_zhiyi
@version: 1.0
@lastEditTime: 
@Description: 设备 - API
"""
import time

import requests
from flask import jsonify, request, Blueprint

from route.status_code.baseHttpStatus import BaseHttpStatus
from route.status_code.configHttpStatus import ConfigHttpStatus
from utils.util_conf import ConfUtils
from utils.util_database import DBUtils

equipment_db = Blueprint('equipment_db', __name__)

# 总控设备
CONTROL_PORT = 7023
CONTROL_SUB_URL = 'api/inner/control_config'

# 采集设备
AVIA_PORT = 9023
AVIA_SUB_URL = 'api/inner/lidar_config'


@equipment_db.route('/startControl', methods=['POST'])
def start_control():
    """
    启动中控设备
        1. 判断 ip 是否在线
        2. 判断中控设备是否初始化
        3. 若已初始化则修改，则调用远端启动脚本
        4. 启动成功则修改设备状态
    TODO：
          1. PC端需要监控中控设备是否在线，若不在线则修改设备状态
          2. 中控在线的情况下，需要检测指定进程是否在运行状态，否不在运行状态，则调用PC相关接口修改设备状态
    """
    try:
        data = request.json
        control_code = data.get('ConEquipCode')
        ip = data.get('IP')
        res = ConfUtils.eq_start(control_code, ip, 'control', CONTROL_PORT, CONTROL_SUB_URL)
        return jsonify(res), 200
    except Exception as e:
        return jsonify(
            {'code': BaseHttpStatus.EXCEPTION.value, 'msg': '启动失败', 'data': {'exception': str(e)}})


@equipment_db.route('/stopControl', methods=['POST'])
def stop_control():
    """
    修改设备状态
    """
    try:
        data = request.json
        control_code = data.get('ConEquipCode')
        ip = data.get('IP')
        res = ConfUtils.eq_stop(control_code, 'control', ip, CONTROL_PORT, CONTROL_SUB_URL)
        return jsonify(res), 200
    except Exception as e:
        return jsonify(
            {'code': BaseHttpStatus.EXCEPTION.value, 'msg': '停止失败', 'data': {'exception': str(e)}}), 200


@equipment_db.route('/initControl', methods=['POST'])
def init_control():
    """
    初始化中控设备配置文件
        1. 判断 ip 是否在线
        2. p判断 control_code 是否存在
        3. 若 ip 在线则向 eq_control_conf 中插入数据
        4. 插入成功后调用 ip 所在设备的接口 在中控设备PC上生成配置文件
        5. 返回插入成功响应后修改 eq_control 中的初始化状态字段
    """
    insert_result_dict = {
        0: {
            'code': BaseHttpStatus.ERROR.value,
            'msg': '添加失败',
            'data': ''
        },
        1: {
            'code': BaseHttpStatus.OK.value,
            'msg': '添加成功',
            'data': ''
        },
        2: {
            'code': ConfigHttpStatus.TOO_MANY_PROJECT.value,
            'msg': '添加了多个配置信息',
            'data': ''
        }
    }
    update_result_dict = {
        0: {
            'code': BaseHttpStatus.ERROR.value,
            'msg': '初始化失败',
            'data': ''
        },
        1: {
            'code': BaseHttpStatus.OK.value,
            'msg': '初始化成功',
            'data': ''
        },
        2: {
            'code': ConfigHttpStatus.TOO_MANY_PROJECT.value,
            'msg': '多条设备状态被修改',
            'data': ''
        }
    }

    try:
        now = str(time.time())
        data = request.json
        tun_code = data.get('TunCode')
        control_code = data.get('ConEquipCode')
        conf_ip = data.get('ConfIP')  # conf_ip总控ip
        ip = data.get('IP')  # PC ip
        consumer_rmq_username = data.get('ConsumerRMQUsername', 'tunnel')
        consumer_rmq_password = data.get('ConsumerRMQPassword', '123456')
        consumer_rmq_host = data.get('ConsumerRMQHost', conf_ip)  # 可修改的
        consumer_rmq_port = data.get('ConsumerRMQPort', '5672')
        consumer_rmq_vhost = data.get('ConsumerRMQVirtualHost', 'tunnel_vh')

        consumer_rmq_qn = data.get('ConsumerRMQQueueName', f'avia.control')  # avia.control + '.dataCode.conCode.queue'
        consumer_rmq_bk = data.get('ConsumerRMQBingingKey', f'avia.control')  # avia,control + '.dataCode.conCode'
        consumer_rmq_en = data.get('ConsumerRMQExchangeName', f'avia.control.{control_code}.topic')
        consumer_rmq_et = data.get('ConsumerRMQExchangeType', 'topic')
        consumer_rmq_fbk = data.get('ConsumerRMQFailedBingingKey', 'test')
        consumer_rmq_fqn = data.get('ConsumerRMQFailedQueueName', 'test')

        failed_exchange_queue = data.get('FailedExchangeErrorQueue', 'True')
        failed_exchange_name = data.get('FailedExchangeName', 'tunnel.error.queue')
        failed_exchange_type = data.get('FailedExchangeType', 'direct')

        advance_advance = data.get('AdvanceAdvance', '10')
        advance_prefetch_count = data.get('AdvancePrefetchCount', '1')

        conn_timer_conn_interval = data.get('ConnTimerConnInterval', '10')

        producer_rmq_username = data.get('ProducerRMQUsername', 'tunnel')
        producer_rmq_password = data.get('ProducerRMQPassword', '123456')
        producer_rmq_host = data.get('ProducerRMQHost', ip)  # 可修改的
        producer_rmq_port = data.get('ProducerRMQPort', '5672')
        producer_rmq_vhost = data.get('ProducerRMQVirtualHost', 'tunnel_vh')
        producer_rmq_qn = data.get('ProducerRMQQueueName', f'control.pc.{control_code}.queue')
        producer_rmq_en = data.get('ProducerRMQExchangeName', f'control.pc.topic')
        producer_rmq_et = data.get('ProducerRMQExchangeType', 'topic')
        producer_rmq_bk = data.get('ProducerRMQBingingKey', f'control.pc.{control_code}')

        producer_rmq_ctc = data.get('ProducerConnTimerConnInterval', '10')

        web_rmq_username = data.get('WebRMQUsername', 'security')
        web_rmq_password = data.get('WebRMQPassword', '123456')
        web_rmq_host = data.get('WebRMQHost', '120.55.165.138')  # 120.55.165.138
        web_rmq_port = data.get('WebRMQPort', '5672')
        web_rmq_vhost = data.get('WebRMQVirtualHost', 'security_vh')
        web_rmq_en = data.get('WebRMQExchangeName', f'control.web.{tun_code}.fanout')
        web_rmq_et = data.get('WebRMQExchangeType', 'fanout')
        web_rmq_bk = data.get('WebRMQBingingKey',
                              f'control.web.{control_code}.{tun_code}')  # control.web + '.control_code.tun_code'
        web_emq_qn = data.get('WebRMQQueueName',
                              f'control.web.{control_code}.{tun_code}.queue')  # control.web + '.control_code.tun_code.queue'

        monitor_qn = data.get('MonitorQueueName', f'avia.control.{control_code}.monitor.queue')

        conf_code = f"control_{control_code}_{now}"
    except Exception as e:
        return jsonify(
            {'code': BaseHttpStatus.EXCEPTION.value, 'msg': '初始化失败', 'data': {'exception': str(e)}}), 200

    if not all(
            [control_code, conf_ip, ip, consumer_rmq_username, consumer_rmq_password, consumer_rmq_host,
             consumer_rmq_port, consumer_rmq_vhost, consumer_rmq_qn, consumer_rmq_bk, consumer_rmq_en, consumer_rmq_et,
             consumer_rmq_fqn, consumer_rmq_fbk, failed_exchange_queue, failed_exchange_name, failed_exchange_type,
             advance_advance, advance_prefetch_count, conn_timer_conn_interval, producer_rmq_username,
             producer_rmq_password, producer_rmq_host, producer_rmq_port, producer_rmq_vhost, producer_rmq_qn,
             producer_rmq_en, producer_rmq_et, producer_rmq_bk, producer_rmq_ctc, conf_code, web_rmq_username,
             web_rmq_password, web_rmq_host, web_rmq_port, web_rmq_vhost, web_rmq_en, web_rmq_et, web_rmq_bk,
             web_emq_qn, tun_code, monitor_qn]):
        return jsonify({'code': BaseHttpStatus.PARAMETER.value, 'msg': '缺少必要的字段', 'data': {}}), 200

    # # 设备 IP 是否在线
    # if not ConfUtils.ip_is_online(ip):
    #     return jsonify({'code': ConfigHttpStatus.NO_EXIST.value, 'msg': '中控设备不在线', 'data': {}}), 200

    # 初始化的设备 conf_ip 是否在线
    if not ConfUtils.ip_is_online(conf_ip, port=CONTROL_PORT):
        return jsonify({'code': ConfigHttpStatus.NO_EXIST.value, 'msg': '中控设备不在线', 'data': {}}), 200

    con = None
    cursor = None
    try:
        dbu = DBUtils()
        con = dbu.connection()
        cursor = con.cursor()
        con.autocommit(False)

        # 验证 设备code 是否存在
        code_sql = "SELECT * From eq_control WHERE ConEquipCode = {}".format(f"'{control_code}'")
        res = DBUtils.project_is_exist(cursor, code_sql, ConfigHttpStatus.NO_FIND_CODE.value, "该设备不存在")
        if res:
            return jsonify(res), 200

        # 配置信息是否存在
        code_sql = "SELECT * From eq_control_conf WHERE ConEquipCode = {}".format(f"'{control_code}'")
        res = DBUtils.project_is_exist(cursor, code_sql, ConfigHttpStatus.NO_FIND_CODE.value, "该设配置不存在")
        if not res:
            return jsonify({'code': ConfigHttpStatus.ERROR.value, 'msg': '该设备的配置信息已经存在', 'data': {}}), 200

        # 插入数据
        insert_sql = """
            INSERT INTO eq_control_conf (
            ConfCode, ConEquipCode, ConsumerRMQUsername, ConsumerRMQPassword, ConsumerRMQHost, 
            ConsumerRMQPort, ConsumerRMQVirtualHost, ConsumerRMQQueueName, ConsumerRMQBingingKey, 
            ConsumerRMQExchangeName, ConsumerRMQExchangeType, ConsumerRMQFailedQueueName, 
            FailedExchangeErrorQueue, FailedExchangeName, FailedExchangeType, AdvanceAdvance, 
            AdvancePrefetchCount, ConnTimerConnInterval, ProducerRMQUsername, ProducerRMQPassword, 
            ProducerRMQHost, ProducerRMQPort, ProducerRMQVirtualHost, ProducerRMQExchangeName, 
            ProducerRMQExchangeType, ProducerRMQBingingKey, ProducerConnTimerConnInterval, WebRMQUsername, 
            WebRMQPassword, WebRMQHost, WebRMQPort, WebRMQVirtualHost, WebRMQExchangeName, WebRMQExchangeType, 
            WebRMQBingingKey, WebRMQQueueName, ConsumerRMQFailedBingingKey, ProducerRMQQueueName, MonitorQueueName) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
             %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        insert_rows = cursor.execute(insert_sql, (
            conf_code, control_code, consumer_rmq_username, consumer_rmq_password, consumer_rmq_host, consumer_rmq_port,
            consumer_rmq_vhost, consumer_rmq_qn, consumer_rmq_bk, consumer_rmq_en, consumer_rmq_et,
            consumer_rmq_fqn, failed_exchange_queue, failed_exchange_name, failed_exchange_type, advance_advance,
            advance_prefetch_count, conn_timer_conn_interval, producer_rmq_username, producer_rmq_password,
            producer_rmq_host, producer_rmq_port, producer_rmq_vhost, producer_rmq_en, producer_rmq_et,
            producer_rmq_bk, producer_rmq_ctc, web_rmq_username, web_rmq_password, web_rmq_host, web_rmq_port,
            web_rmq_vhost, web_rmq_en, web_rmq_et, web_rmq_bk, web_emq_qn, consumer_rmq_fbk, producer_rmq_qn, monitor_qn))

        if DBUtils.kv(insert_rows, insert_result_dict).get('code') != 101:
            return jsonify({'code': ConfigHttpStatus.ERROR.value, 'msg': '插入失败或存在多条相同记录', 'data': {}}), 200

        # 修改 eq_control 设备初始化字段
        update_sql = f"UPDATE eq_control SET Init = 1 WHERE ConEquipCode = {control_code}"
        update_rows = cursor.execute(update_sql)

        # TODO：调用中控设备上的接口修改配置文件
        avia_url = f"http://{conf_ip}:{CONTROL_PORT}/{CONTROL_SUB_URL}/addConfig"
        headers = {
            'Content-Type': 'application/json'
        }
        data = {
            'ConsumerRabbitMQ': {
                'username': consumer_rmq_username,
                'password': consumer_rmq_password,
                'host': consumer_rmq_host,
                'port': consumer_rmq_port,
                'virtualHost': consumer_rmq_vhost,
                'queueName': consumer_rmq_qn,
                'bingingKey': consumer_rmq_bk,
                'exchangeName': consumer_rmq_en,
                'exchangeType': consumer_rmq_et,
                'failedQueueName': consumer_rmq_fqn,
                'failedBingingKey': consumer_rmq_fbk,
                'monitorQueueName': monitor_qn
            },
            'FailedExchange': {
                'errorQueue': failed_exchange_queue,
                'name': failed_exchange_name,
                'type': failed_exchange_type
            },
            'Advance': {
                'advance': advance_advance,
                'prefetchCount': advance_prefetch_count
            },
            'ConnTimer': {
                'connectInterval': conn_timer_conn_interval
            },
            'ProducerRabbitMQ': {
                'username': producer_rmq_username,
                'password': producer_rmq_password,
                'host': producer_rmq_host,
                'port': producer_rmq_port,
                'virtualHost': producer_rmq_vhost,
                'queueName': producer_rmq_qn,
                'bingingKey': producer_rmq_bk,
                'exchangeName': producer_rmq_en,
                'exchangeType': producer_rmq_et
            },
            'ProducerConnTimer': {
                'connectInterval': producer_rmq_ctc
            },
            'WebRabbitMQ': {
                'username': web_rmq_username,
                'password': web_rmq_password,
                'host': web_rmq_host,
                'port': web_rmq_port,
                'virtualHost': web_rmq_vhost,
                'queueName': web_emq_qn,
                'bingingKey': web_rmq_bk,
                'exchangeName': web_rmq_en,
                'exchangeType': web_rmq_et
            }

        }
        response = requests.post(avia_url, json=data, headers=headers)
        if response.json().get('code') != 101:
            return response.json(), 200

        con.commit()
        return jsonify(DBUtils.kv(update_rows, update_result_dict)), 200
    except Exception as e:
        if con:
            con.rollback()
        return jsonify(
            {'code': BaseHttpStatus.EXCEPTION.value, 'msg': '初始化失败', 'data': {'exception': str(e)}}), 200
    finally:
        if cursor:
            cursor.close()
        if con:
            DBUtils.close_connection(con)


@equipment_db.route('/updateControl', methods=['POST'])
def update_control():
    """
    更新中控设备配置文件
        1. 判断 ip 是否在线
        2. 若 ip 在线则修改 eq_control_conf 中的数据
        3. 修改成功后调用 ip 所在设备的接口 在中控设备PC上修改配置文件
        4. 返回修改成功响应后逻辑结束
    TODO：新设备可能处于故障状态，未做判断
    """
    result_dict = {
        0: {
            'code': BaseHttpStatus.ERROR.value,
            'msg': '更新失败',
            'data': ''
        },
        1: {
            'code': BaseHttpStatus.OK.value,
            'msg': '更新成功',
            'data': ''
        },
        2: {
            'code': ConfigHttpStatus.TOO_MANY_PROJECT.value,
            'msg': '更新了多个配置信息',
            'data': ''
        }
    }

    update_result_dict = {
        0: {
            'code': BaseHttpStatus.ERROR.value,
            'msg': '更新失败',
            'data': ''
        },
        1: {
            'code': BaseHttpStatus.OK.value,
            'msg': '更新成功',
            'data': ''
        },
        2: {
            'code': ConfigHttpStatus.TOO_MANY_PROJECT.value,
            'msg': '多条设备状态被修改',
            'data': ''
        }
    }
    try:
        now = str(time.time())
        data = request.json
        # old_control_code 与 control_code 不一致时需要修改 eq_control 表中的 Init 字段
        tun_code = data.get('TunCode')
        old_control_code = data.get('OldConEquipCode')
        control_code = data.get('ConEquipCode')
        old_conf_ip = data.get('OldConfIP')
        conf_ip = data.get('ConfIP')
        ip = data.get('IP')

        consumer_rmq_username = data.get('ConsumerRMQUsername', 'tunnel')
        consumer_rmq_password = data.get('ConsumerRMQPassword', '123456')
        consumer_rmq_host = data.get('ConsumerRMQHost', conf_ip)  # 可修改的
        consumer_rmq_port = data.get('ConsumerRMQPort', '5672')
        consumer_rmq_vhost = data.get('ConsumerRMQVirtualHost', 'tunnel_vh')

        consumer_rmq_qn = data.get('ConsumerRMQQueueName', f'avia.control')  # avia.control + '.dataCode.conCode.queue'
        consumer_rmq_bk = data.get('ConsumerRMQBingingKey', f'avia.control')  # avia,control + '.dataCode.conCode'
        consumer_rmq_en = data.get('ConsumerRMQExchangeName', f'avia.control.{control_code}.topic')
        consumer_rmq_et = data.get('ConsumerRMQExchangeType', 'topic')
        consumer_rmq_fbk = data.get('ConsumerRMQFailedBingingKey', 'test')
        consumer_rmq_fqn = data.get('ConsumerRMQFailedQueueName', 'test')

        failed_exchange_queue = data.get('FailedExchangeErrorQueue', 'True')
        failed_exchange_name = data.get('FailedExchangeName', 'tunnel.error.queue')
        failed_exchange_type = data.get('FailedExchangeType', 'direct')

        advance_advance = data.get('AdvanceAdvance', '10')
        advance_prefetch_count = data.get('AdvancePrefetchCount', '1')

        conn_timer_conn_interval = data.get('ConnTimerConnInterval', '10')

        producer_rmq_username = data.get('ProducerRMQUsername', 'tunnel')
        producer_rmq_password = data.get('ProducerRMQPassword', '123456')
        producer_rmq_host = data.get('ProducerRMQHost', ip)  # 可修改的
        producer_rmq_port = data.get('ProducerRMQPort', '5672')
        producer_rmq_vhost = data.get('ProducerRMQVirtualHost', 'tunnel_vh')
        producer_rmq_qn = data.get('ProducerRMQQueueName', f'control.pc.{control_code}.queue')
        producer_rmq_en = data.get('ProducerRMQExchangeName', f'control.pc.topic')
        producer_rmq_et = data.get('ProducerRMQExchangeType', 'topic')
        producer_rmq_bk = data.get('ProducerRMQBingingKey', f'control.pc.{control_code}')

        producer_rmq_ctc = data.get('ProducerConnTimerConnInterval', '10')

        web_rmq_username = data.get('WebRMQUsername', 'security')
        web_rmq_password = data.get('WebRMQPassword', '123456')
        web_rmq_host = data.get('WebRMQHost', '120.55.165.138')  # 120.55.165.138
        web_rmq_port = data.get('WebRMQPort', '5672')
        web_rmq_vhost = data.get('WebRMQVirtualHost', 'security_vh')

        web_rmq_en = data.get('WebRMQExchangeName', f'control.web.{tun_code}.fanout')
        web_rmq_et = data.get('WebRMQExchangeType', 'fanout')
        web_rmq_bk = data.get('WebRMQBingingKey',
                              f'control.web.{control_code}.{tun_code}')  # control.web + '.control_code.tun_code'
        web_emq_qn = data.get('WebRMQQueueName',
                              f'control.web.{control_code}.{tun_code}.queue')  # control.web + '.control_code.tun_code.queue'

        monitor_qn = data.get('MonitorQueueName', f'avia.control.{control_code}.monitor.queue')

        conf_code = f"control_{control_code}_{now}"
    except Exception as e:
        return jsonify(
            {'code': BaseHttpStatus.EXCEPTION.value, 'msg': '更新失败', 'data': {'exception': str(e)}}), 200

    if not all(
            [control_code, conf_ip, consumer_rmq_username, consumer_rmq_password, consumer_rmq_host, consumer_rmq_port,
             consumer_rmq_vhost, consumer_rmq_qn, consumer_rmq_bk, consumer_rmq_en, consumer_rmq_et,
             consumer_rmq_fqn, consumer_rmq_fbk, failed_exchange_queue, failed_exchange_name, failed_exchange_type,
             advance_advance, advance_prefetch_count, conn_timer_conn_interval, producer_rmq_username,
             producer_rmq_password, producer_rmq_host, producer_rmq_port, producer_rmq_vhost, producer_rmq_en,
             producer_rmq_et, producer_rmq_bk, producer_rmq_ctc, conf_code, web_rmq_username, web_rmq_password,
             web_rmq_host, web_rmq_port, web_rmq_vhost, web_rmq_en, web_rmq_et, web_rmq_bk, web_emq_qn, tun_code,
             old_conf_ip, old_control_code, ip, producer_rmq_qn, monitor_qn]):
        return jsonify({'code': BaseHttpStatus.PARAMETER.value, 'msg': '缺少必要的字段', 'data': {}}), 200

    if not ConfUtils.ip_is_online(old_conf_ip, port=CONTROL_PORT):
        return jsonify({'code': ConfigHttpStatus.NO_EXIST.value, 'msg': '中控设备不在线', 'data': {}}), 200

    con = None
    cursor = None
    # 是否要修改 old_control_code 在 eq_control 表中对应记录的 Init 值
    old_init_modify = False
    try:
        dbu = DBUtils()
        con = dbu.connection()
        cursor = con.cursor()
        con.autocommit(False)

        # 验证 设备old_code 是否存在
        old_con_sql = "SELECT * From eq_control WHERE ConEquipCode = {}".format(f"'{old_control_code}'")
        res = DBUtils.project_is_exist(cursor, old_con_sql, ConfigHttpStatus.NO_FIND_CODE.value, "待更新的设备不存在")
        if res:
            return jsonify(res), 200

        # 配置信息是否存在
        old_conf_sql = "SELECT * From eq_control_conf WHERE ConEquipCode = {}".format(f"'{old_control_code}'")
        res = DBUtils.project_is_exist(cursor, old_conf_sql, ConfigHttpStatus.NO_FIND_CODE.value, "该设配置不存在")
        if res:
            return jsonify(res), 200

        old_conf_sql = "SELECT * From eq_control_conf WHERE ConEquipCode = {}".format(f"'{old_control_code}'")
        res = DBUtils.project_is_exist(cursor, old_conf_sql, ConfigHttpStatus.NO_FIND_CODE.value, "该设配置不存在")
        if not res:
            # 若存在直接删除，重新插入
            delete_sql = f"DELETE FROM eq_control_conf WHERE ConEquipCode = {old_control_code}"
            delete_rows = cursor.execute(delete_sql)
            if DBUtils.kv(delete_rows, result_dict).get('code') != 101:
                return jsonify(
                    {'code': ConfigHttpStatus.ERROR.value, 'msg': '更新失败在删除旧数据时', 'data': {}}), 200
            # return jsonify(
            #     {'code': ConfigHttpStatus.ERROR.value, 'msg': '修改后的配置信息所属的设备已有配置，无需重复创建',
            #      'data': {}}), 200

        # 设备code是否发生变化
        if old_control_code != control_code:
            # 验证 设备code 是否存在
            con_sql = "SELECT * From eq_control WHERE ConEquipCode = {}".format(f"'{control_code}'")
            res = DBUtils.project_is_exist(cursor, con_sql, ConfigHttpStatus.NO_FIND_CODE.value, "修改后的设备不存在")
            if res:
                return jsonify(res), 200

            # 判断 control_code 设备是否已经配置文件
            conf_sql = "SELECT * From eq_control_conf WHERE ConEquipCode = {}".format(f"'{control_code}'")
            res = DBUtils.project_is_exist(cursor, conf_sql, ConfigHttpStatus.NO_FIND_CODE.value, "该设配置不存在")
            if not res:
                return jsonify(
                    {'code': ConfigHttpStatus.CONF_EXIST.value, 'msg': f'{control_code}设备已有配置', 'data': {}}), 200

            old_init_modify = True

            ip_sql = f"SELECT ConEquipIP FROM eq_control WHERE ConEquipCode = {control_code}"
            cursor.execute(ip_sql)
            ip_tuple = cursor.fetchone()
            ip = ip_tuple[0]
            consumer_rmq_host = ip_tuple[0]
            producer_rmq_host = ip_tuple[0]

        # 更新
        # update_conf_sql = """
        #     UPDATE
        #         eq_control_conf
        #     SET
        #         ConfCode=%s, ConEquipCode=%s, ConsumerRMQUsername=%s, ConsumerRMQPassword=%s, ConsumerRMQHost=%s,
        #         ConsumerRMQPort=%s, ConsumerRMQVirtualHost=%s, ConsumerRMQQueueName=%s, ConsumerRMQBingingKey=%s,
        #         ConsumerRMQExchangeName=%s, ConsumerRMQExchangeType=%s, ConsumerRMQFailedQueueName=%s,
        #         FailedExchangeErrorQueue=%s, FailedExchangeName=%s, FailedExchangeType=%s, AdvanceAdvance=%s,
        #         AdvancePrefetchCount=%s, ConnTimerConnInterval=%s, ProducerRMQUsername=%s, ProducerRMQPassword=%s,
        #         ProducerRMQHost=%s, ProducerRMQPort=%s, ProducerRMQVirtualHost=%s, ProducerRMQExchangeName=%s,
        #         ProducerRMQExchangeType=%s, ProducerRMQBingingKey=%s, ProducerConnTimerConnInterval=%s
        #     WHERE
        #         ConEquipCode=%s;
        # """
        # rows = cursor.execute(update_conf_sql, (
        #     conf_code, control_code, consumer_rmq_username, consumer_rmq_password, consumer_rmq_host, consumer_rmq_port,
        #     consumer_rmq_vhost, consumer_rmq_qn, consumer_rmq_bk, consumer_rmq_en, consumer_rmq_et, consumer_rmq_fqn,
        #     failed_exchange_queue, failed_exchange_name, failed_exchange_type, advance_advance, advance_prefetch_count,
        #     conn_timer_conn_interval, producer_rmq_username, producer_rmq_password, producer_rmq_host,
        #     producer_rmq_port, producer_rmq_vhost, producer_rmq_en, producer_rmq_et, producer_rmq_bk, producer_rmq_ctc,
        #     old_control_code))
        # if DBUtils.kv(rows, result_dict).get('code') != 101:
        #     return jsonify({'code': ConfigHttpStatus.ERROR.value, 'msg': '更新失败或存在多条相同记录', 'data': {}}), 200

        # 插入数据
        insert_sql = """
                    INSERT INTO eq_control_conf (
                    ConfCode, ConEquipCode, ConsumerRMQUsername, ConsumerRMQPassword, ConsumerRMQHost, 
                    ConsumerRMQPort, ConsumerRMQVirtualHost, ConsumerRMQQueueName, ConsumerRMQBingingKey, 
                    ConsumerRMQExchangeName, ConsumerRMQExchangeType, ConsumerRMQFailedQueueName, 
                    FailedExchangeErrorQueue, FailedExchangeName, FailedExchangeType, AdvanceAdvance, 
                    AdvancePrefetchCount, ConnTimerConnInterval, ProducerRMQUsername, ProducerRMQPassword, 
                    ProducerRMQHost, ProducerRMQPort, ProducerRMQVirtualHost, ProducerRMQExchangeName, 
                    ProducerRMQExchangeType, ProducerRMQBingingKey, ProducerConnTimerConnInterval, WebRMQUsername, 
                    WebRMQPassword, WebRMQHost, WebRMQPort, WebRMQVirtualHost, WebRMQExchangeName, WebRMQExchangeType, 
                    WebRMQBingingKey, WebRMQQueueName, ConsumerRMQFailedBingingKey, ProducerRMQQueueName, MonitorQueueName) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                     %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        insert_rows = cursor.execute(insert_sql, (
            conf_code, control_code, consumer_rmq_username, consumer_rmq_password, consumer_rmq_host, consumer_rmq_port,
            consumer_rmq_vhost, consumer_rmq_qn, consumer_rmq_bk, consumer_rmq_en, consumer_rmq_et,
            consumer_rmq_fqn, failed_exchange_queue, failed_exchange_name, failed_exchange_type, advance_advance,
            advance_prefetch_count, conn_timer_conn_interval, producer_rmq_username, producer_rmq_password,
            producer_rmq_host, producer_rmq_port, producer_rmq_vhost, producer_rmq_en, producer_rmq_et,
            producer_rmq_bk, producer_rmq_ctc, web_rmq_username, web_rmq_password, web_rmq_host, web_rmq_port,
            web_rmq_vhost, web_rmq_en, web_rmq_et, web_rmq_bk, web_emq_qn, consumer_rmq_fbk, producer_rmq_qn, monitor_qn))

        if DBUtils.kv(insert_rows, update_result_dict).get('code') != 101:
            return jsonify({'code': ConfigHttpStatus.ERROR.value, 'msg': '插入失败或存在多条相同记录', 'data': {}}), 200

        # 更新 Init
        if old_init_modify:
            old_sql = f"UPDATE eq_control SET Init = 0 WHERE ConEquipCode = {old_control_code}"
            old_update_rows = cursor.execute(old_sql)
            if DBUtils.kv(old_update_rows, update_result_dict).get('code') != 101:
                return jsonify(
                    {'code': ConfigHttpStatus.ERROR.value, 'msg': '旧设备状态更新失败或存在多条相同记录',
                     'data': {}}), 200

            sql = f"UPDATE eq_control SET Init = 1 WHERE ConEquipCode = {control_code}"
            update_rows = cursor.execute(sql)
            if DBUtils.kv(update_rows, update_result_dict).get('code') != 101:
                return jsonify(
                    {'code': ConfigHttpStatus.ERROR.value, 'msg': '新设备状态更新失败或存在多条相同记录',
                     'data': {}}), 200

        # TODO：调用中控端接口更新配置文件
        avia_url = f"http://{old_conf_ip}:{CONTROL_PORT}/{CONTROL_SUB_URL}/updateConfig"
        headers = {
            'Content-Type': 'application/json'
        }
        data = {
            'ConsumerRabbitMQ': {
                'username': consumer_rmq_username,
                'password': consumer_rmq_password,
                'host': consumer_rmq_host,
                'port': consumer_rmq_port,
                'virtualHost': consumer_rmq_vhost,
                'queueName': consumer_rmq_qn,
                'bingingKey': consumer_rmq_bk,
                'exchangeName': consumer_rmq_en,
                'exchangeType': consumer_rmq_et,
                'failedQueueName': consumer_rmq_fqn,
                'failedBingingKey': consumer_rmq_bk,
                'monitorQueueName': monitor_qn
            },
            'FailedExchange': {
                'errorQueue': failed_exchange_queue,
                'name': failed_exchange_name,
                'type': failed_exchange_type
            },
            'Advance': {
                'advance': advance_advance,
                'prefetchCount': advance_prefetch_count
            },
            'ConnTimer': {
                'connectInterval': conn_timer_conn_interval
            },
            'ProducerRabbitMQ': {
                'username': producer_rmq_username,
                'password': producer_rmq_password,
                'host': producer_rmq_host,
                'port': producer_rmq_port,
                'virtualHost': producer_rmq_vhost,
                'queueName': producer_rmq_qn,
                'bingingKey': producer_rmq_bk,
                'exchangeName': producer_rmq_en,
                'exchangeType': producer_rmq_et
            },
            'ProducerConnTimer': {
                'connectInterval': producer_rmq_ctc
            },
            'WebRabbitMQ': {
                'username': web_rmq_username,
                'password': web_rmq_password,
                'host': web_rmq_host,
                'port': web_rmq_port,
                'virtualHost': web_rmq_vhost,
                'queueName': web_emq_qn,
                'bingingKey': web_rmq_bk,
                'exchangeName': web_rmq_en,
                'exchangeType': web_rmq_et
            }
        }

        response = requests.post(avia_url, json=data, headers=headers)
        if response.json().get('code') != 101:
            return response.json(), 200

        con.commit()

        return jsonify({'code': ConfigHttpStatus.OK.value, 'msg': '更新成功', 'data': {}}), 200
    except Exception as e:
        if con:
            con.rollback()
        return jsonify(
            {'code': BaseHttpStatus.EXCEPTION.value, 'msg': '更新失败', 'data': {'exception': str(e)}}), 200
    finally:
        if cursor:
            cursor.close()
        if con:
            DBUtils.close_connection(con)


@equipment_db.route('/deleteControl', methods=['POST'])
def delete_control():
    """
    删除配置内容
    """
    try:
        data = request.json
        control_code = data.get('ConEquipCode')
        control_ip = data.get('ConEquipIP')
        res = ConfUtils.delete(control_code, 'eq_control', 'eq_control_conf', 'ConEquipCode', control_ip, CONTROL_PORT,
                               CONTROL_SUB_URL)
        return res, 200
    except Exception as e:
        return jsonify(
            {'code': BaseHttpStatus.EXCEPTION.value, 'msg': '删除失败', 'data': {'exception': str(e)}}), 200


@equipment_db.route('/startData', methods=['POST'])
def start_data():
    """
    启动终端雷达设备
        1. 判断 ip 是否在线
        2. 判断终端雷达设备是否初始化
        3. 若已初始化则修改，则调用远端启动脚本
        4. 启动成功则修改设备状态
    TODO：
          1. PC端需要监控终端设备是否在线，若不在线则修改设备状态
          2. 终端在线的情况下，需要检测指定进程是否在运行状态，否不在运行状态，则调用PC相关接口修改设备状态
    """
    try:
        data = request.json
        data_code = data.get('DataAcqEquipCode')
        ip = data.get('IP')
        res = ConfUtils.eq_start(data_code, ip, 'data', AVIA_PORT, AVIA_SUB_URL)
        return jsonify(res), 200
    except Exception as e:
        return jsonify(
            {'code': BaseHttpStatus.EXCEPTION.value, 'msg': '启动失败', 'data': {'exception': str(e)}})


@equipment_db.route('/stopData', methods=['POST'])
def stop_data():
    """
    修改设备状态
    """
    try:
        data = request.json
        control_code = data.get('DataAcqEquipCode')
        ip = data.get('IP')
        res = ConfUtils.eq_stop(control_code, 'data', ip, AVIA_PORT, AVIA_SUB_URL)
        return jsonify(res), 200
    except Exception as e:
        return jsonify(
            {'code': BaseHttpStatus.EXCEPTION.value, 'msg': '初始化失败', 'data': {'exception': str(e)}}), 200


@equipment_db.route('/initData', methods=['POST'])
def init_data():
    """
    初始化终端设备配置文件
        1. 判断 ip 是否在线
        2. p判断 control_code 是否存在
        3. 若 ip 在线则向 eq_control_conf 中插入数据
        4. 插入成功后调用 ip 所在设备的接口 在中控设备PC上生成配置文件
        5. 返回插入成功响应后修改 eq_control 中的初始化状态字段
    """
    insert_result_dict = {
        0: {
            'code': BaseHttpStatus.ERROR.value,
            'msg': '添加失败',
            'data': ''
        },
        1: {
            'code': BaseHttpStatus.OK.value,
            'msg': '添加成功',
            'data': ''
        },
        2: {
            'code': ConfigHttpStatus.TOO_MANY_PROJECT.value,
            'msg': '添加了多个配置信息',
            'data': ''
        }
    }
    update_result_dict = {
        0: {
            'code': BaseHttpStatus.ERROR.value,
            'msg': '初始化失败',
            'data': ''
        },
        1: {
            'code': BaseHttpStatus.OK.value,
            'msg': '初始化成功',
            'data': ''
        },
        2: {
            'code': ConfigHttpStatus.TOO_MANY_PROJECT.value,
            'msg': '多条设备状态被修改',
            'data': ''
        }
    }

    try:
        now = str(time.time())
        data = request.json
        control_code = data.get('ConEquipCode')
        data_code = data.get('DataAcqEquipCode')
        conf_ip = data.get('ConfIP')  # 在前端控制设备 ip 必须和配置文件内的保持一致
        lp_stw = data.get('LidarParameterSTW', 0.1)
        lp_dur = data.get('LidarParameterDur', 1)
        lp_coll_inter = data.get('LidarParameterCollInter', 10)
        lp_conn_inter = data.get('LidarParameterConnInter', 10)
        lp_computer_ip = data.get('LidarParameterComputerIP', '192.168.1.7')
        lp_sensor_ip = data.get('LidarParameterSensorIP', '192.168.1.104')

        rp_username = data.get('RabbitmqParameterUsername', 'tunnel')
        rp_password = data.get('RabbitmqParameterPassword', '123456')
        rp_host = data.get('RabbitmqParameterHost', conf_ip)
        rp_post = data.get('RabbitmqParameterPort', '5672')
        rp_vhost = data.get('RabbitmqParameterVirtualHost', 'tunnel_vh')
        rp_en = data.get('RabbitmqParameterExchange', f'avia.control.{control_code}.topic')  # 交换机名称 雷达 -> 总控
        rp_et = data.get('RabbitmqParameterExchangeType', 'topic')
        rp_rk = data.get('RabbitmqParameterRoutingKey', f'avia.control.{data_code}.{control_code}')
        rp_conn_inter = data.get('RabbitmqParameterConnInterval', '10')
        rp_qn = data.get('RabbitmqParameterQueueName', f'avia.control.{data_code}.{control_code}.queue')
        conf_code = f"avia_{data_code}_{now}"
    except Exception as e:
        return jsonify(
            {'code': BaseHttpStatus.EXCEPTION.value, 'msg': '初始化失败', 'data': {'exception': str(e)}}), 200

    if not all(
            [data_code, conf_ip, lp_stw, lp_dur, lp_coll_inter, lp_conn_inter,
             rp_username, rp_password, rp_host, rp_post, rp_vhost,
             rp_en, rp_et, rp_conn_inter, conf_code, rp_rk, rp_qn, lp_computer_ip, lp_sensor_ip]):
        return jsonify({'code': BaseHttpStatus.PARAMETER.value, 'msg': '缺少必要的字段', 'data': {}}), 200

    # 初始化的设备 conf_ip 是否在线
    if not ConfUtils.ip_is_online(conf_ip, port=AVIA_PORT):
        return jsonify({'code': ConfigHttpStatus.NO_EXIST.value, 'msg': '终端设备不在线', 'data': {}}), 200

    con = None
    cursor = None
    try:
        dbu = DBUtils()
        con = dbu.connection()
        cursor = con.cursor()
        con.autocommit(False)

        # 验证 设备code 是否存在
        code_sql = "SELECT * From eq_data WHERE DataAcqEquipCode = {}".format(f"'{data_code}'")
        res = DBUtils.project_is_exist(cursor, code_sql, ConfigHttpStatus.NO_FIND_CODE.value, "该设备不存在")
        if res:
            return jsonify(res), 200

        # 配置信息是否存在
        code_sql = "SELECT * From eq_data_conf WHERE DataAcqEquipCode = {}".format(f"'{data_code}'")
        res = DBUtils.project_is_exist(cursor, code_sql, ConfigHttpStatus.NO_FIND_CODE.value, "该设配置不存在")
        if not res:
            # TODO: 删除已有的配置文件？
            return jsonify({'code': ConfigHttpStatus.ERROR.value, 'msg': '该设备的配置信息已经存在', 'data': {}}), 200

        # 插入数据
        insert_sql = """
            INSERT INTO eq_data_conf (
            ConfCode, DataAcqEquipCode, LidarParameterSTW,LidarParameterDur,LidarParameterCollInter,
            LidarParameterConnInter, RabbitmqParameterUsername, RabbitmqParameterPassword, 
            RabbitmqParameterHost, RabbitmqParameterPort, RabbitmqParameterVirtualHost, 
            RabbitmqParameterExchange, RabbitmqParameterExchangeType, RabbitmqParameterConnInterval,
             RabbitmqParameterRoutingKey, RabbitmqParameterQueueName, computerIP, sensorIP) 
            VALUES (%s, %s, %s, %s, %s,  %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        insert_rows = cursor.execute(insert_sql, (
            conf_code, data_code, lp_stw, lp_dur, lp_coll_inter, lp_conn_inter, rp_username, rp_password, rp_host,
            rp_post, rp_vhost, rp_en, rp_et, rp_conn_inter, rp_rk, rp_qn, lp_computer_ip, lp_sensor_ip))

        if DBUtils.kv(insert_rows, insert_result_dict).get('code') != 101:
            return jsonify({'code': ConfigHttpStatus.ERROR.value, 'msg': '插入失败或存在多条相同记录', 'data': {}}), 200

        # 修改 eq_control 设备初始化字段
        update_sql = f"UPDATE eq_data SET Init = 1 WHERE DataAcqEquipCode = {data_code}"
        update_rows = cursor.execute(update_sql)

        # TODO：调用终端设备上的接口添加配置文件
        avia_url = f"http://{conf_ip}:{AVIA_PORT}/{AVIA_SUB_URL}/addConfig"
        headers = {
            'Content-Type': 'application/json'
        }
        data = {
            'LidarParameter': {
                'duration': lp_dur,
                'lidarCollInterval': lp_coll_inter,
                'lidarConnInterval': lp_conn_inter,
                'secsToWait': lp_stw,
                'computerIP': lp_computer_ip,
                'sensorIP': lp_sensor_ip
            },
            'RabbitmqParameter': {
                'username': rp_username,
                'password': rp_password,
                'host': rp_host,
                'port': rp_post,
                'virtualHost': rp_vhost,
                'exchange': rp_en,
                'exchangeType': rp_et,
                'connInterval': rp_conn_inter,
                'queueName': rp_qn,
                'routingKey': rp_rk
            }
        }
        response = requests.post(avia_url, json=data, headers=headers)
        if response.json().get('code') != 101:
            return response.json(), 200

        con.commit()
        return jsonify(DBUtils.kv(update_rows, update_result_dict)), 200
    except Exception as e:
        if con:
            con.rollback()
        return jsonify(
            {'code': BaseHttpStatus.EXCEPTION.value, 'msg': '初始化失败', 'data': {'exception': str(e)}}), 200
    finally:
        if cursor:
            cursor.close()
        if con:
            DBUtils.close_connection(con)


@equipment_db.route('/deleteData', methods=['POST'])
def delete_data():
    """
    删除配置内容
    """
    try:
        data = request.json
        data_code = data.get('DataAcqEquipCode')
        data_ip = data.get('DataAcqEquipIP')
        res = ConfUtils.delete(data_code, 'eq_data', 'eq_data_conf', 'DataAcqEquipCode', data_ip, AVIA_PORT,
                               AVIA_SUB_URL)
        return res, 200
    except Exception as e:
        return jsonify(
            {'code': BaseHttpStatus.EXCEPTION.value, 'msg': '删除失败', 'data': {'exception': str(e)}}), 200

"""
@Author: zhang_zhiyi
@Date: 2025/4/23_17:49
@FileName:util_conf.py
@LastEditors: zhang_zhiyi
@version: 1.0
@lastEditTime: 
@Description: 配置文件相关工具
"""
import socket

import requests
from flask import jsonify
from pymysql.cursors import DictCursor

from route.status_code.baseHttpStatus import BaseHttpStatus
from route.status_code.configHttpStatus import ConfigHttpStatus
from utils.util_database import DBUtils
from utils.util_rabbitmq import send_queue_info2monitor

EQUIPMENT_PARAMETER = {
    'control': {
        'table_name': 'eq_control',
        'table_name_conf': 'eq_control_conf',
        'column_status': 'ConStatus',
        'column_code': 'ConEquipCode',
        'column_queue': 'ProducerRMQQueueName',
        'column_username': 'ProducerRMQUsername',
        'column_password': 'ProducerRMQPassword',
        'column_host': 'ProducerRMQHost',
        'column_port': 'ProducerRMQPort',
        'column_vh': 'ProducerRMQVirtualHost',
        'column_binging_key': 'ProducerRMQBingingKey'
    },
    'data': {
        'table_name': 'eq_data',
        'table_name_conf': 'eq_data_conf',
        'column_status': 'DataAcaEquipStatus',
        'column_code': 'DataAcqEquipCode',
        'column_queue': 'RabbitmqParameterQueueName',
        'column_username': 'RabbitmqParameterUsername',
        'column_password': 'RabbitmqParameterPassword',
        'column_host': 'RabbitmqParameterHost',
        'column_port': 'RabbitmqParameterPort',
        'column_vh': 'RabbitmqParameterVirtualHost',
        'column_binging_key': 'RabbitmqParameterRoutingKey'
    }
}


class ConfUtils(object):
    # AVIA_PORT = 9023
    # AVIA_SUB_URL = 'api/inner/lidar_config'

    @staticmethod
    def ip_is_online(ip, port=3306, timeout=1):
        """
        判断 ip 是否在线
        三种方法：ping / 尝试连接常见端口（如 22/80/5000）/ 批量扫描整个局域网
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            try:
                s.connect((ip, port))
                return True
            except Exception as e:
                return False

    @staticmethod
    def eq_start(eq_code, ip, equipment, port, sub_url):
        """
        启动设备通用方法
        """
        result_dict = {
            0: {
                'code': BaseHttpStatus.INFO_SAME.value,
                'msg': '设备信息和原先一致',
                'data': ''
            },
            1: {
                'code': BaseHttpStatus.OK.value,
                'msg': '启动成功',
                'data': ''
            },
            2: {
                'code': ConfigHttpStatus.TOO_MANY_PROJECT.value,
                'msg': '太多设备记录被修改',
                'data': ''
            }
        }
        if not all([eq_code, ip, equipment, port, sub_url]):
            return {'code': BaseHttpStatus.PARAMETER.value, 'msg': '缺少必要的字段', 'data': {}}

        # 设备 IP 是否在线
        if not ConfUtils.ip_is_online(ip, port=port):
            return {'code': ConfigHttpStatus.NO_EXIST.value, 'msg': '设备不在线', 'data': {}}

        con = None
        cursor = None
        try:
            dbu = DBUtils()
            con = dbu.connection(cursor_class=DictCursor)
            cursor = con.cursor()
            con.autocommit(False)

            parameters = EQUIPMENT_PARAMETER.get(equipment)
            table_name = parameters.get('table_name')
            table_name_conf = parameters.get('table_name_conf')
            column_status = parameters.get('column_status')
            column_code = parameters.get('column_code')
            column_queue = parameters.get('column_queue')
            column_username = parameters.get('column_username')
            column_password = parameters.get('column_password')
            column_host = parameters.get('column_host')
            column_port = parameters.get('column_port')
            column_vh = parameters.get('column_vh')
            column_binging_key = parameters.get('column_binging_key')

            # 验证 设备code 是否存在
            code_sql = f"SELECT * From {table_name} WHERE {column_code} = {eq_code}"
            res = DBUtils.project_is_exist(cursor, code_sql, ConfigHttpStatus.NO_FIND_CODE.value, "该设备不存在")
            if res:
                return jsonify(res)

            # 判断设备是否已经初始化
            init_sql = f"SELECT Init, {column_status} From {table_name} WHERE {column_code} = {eq_code}"
            cursor.execute(init_sql)
            res = cursor.fetchone()
            if res.get('Init') == 0:
                return {'code': ConfigHttpStatus.ERROR.value, 'msg': '设备未进行初始化', 'data': {}}

            # 判断设备是否已经启动
            if res.get('ConStatus') == 1:
                return {'code': ConfigHttpStatus.ERROR.value, 'msg': '设备在线，无需启动', 'data': {}}

            # TODO: 调用远端启动设备脚本
            url = f"http://{ip}:{port}/{sub_url}/start"
            headers = {
                'Content-Type': 'application/json'
            }
            data = {}
            response = requests.post(url, json=data, headers=headers)
            if response.json().get('code') != 101:
                raise Exception(str(response.json()))

            # TODO: 向PC端监听队列发送当前总控设备到PC端的数据传输队列 / 向总控端监听队列发送当前采集设备到总控端的数据传输队列
            # eq_control_conf 中拿到 ProducerRMQQueueName 字段值，即队列名称
            select_queue = f"""
            SELECT 
            {column_queue}, {column_username}, {column_password}, {column_host}, {column_port}, {column_vh}, {column_binging_key}
            FROM {table_name_conf} 
            WHERE {column_code} = %s
            """
            cursor.execute(select_queue, eq_code)
            select_queue_res = cursor.fetchone()
            queue_name = select_queue_res.get(column_queue)
            username = select_queue_res.get(column_username)
            password = select_queue_res.get(column_password)
            host = select_queue_res.get(column_host)
            port = select_queue_res.get(column_port)
            vh = select_queue_res.get(column_vh)
            bk = select_queue_res.get(column_binging_key)

            # 向PC监听队列发送队列
            send_queue_info2monitor(eq_code, queue_name, 'start', equipment, username, password, host, port, vh, bk)

            # 修改设备状态
            status_sql = f"UPDATE {table_name} SET {column_status} = 1 WHERE {column_code} = {eq_code}"
            rows = cursor.execute(status_sql)
            con.commit()
            return DBUtils.kv(rows, result_dict)
        except Exception as e:
            if con:
                con.rollback()
            return {'code': BaseHttpStatus.EXCEPTION.value, 'msg': '启动失败', 'data': {'exception': str(e)}}
        finally:
            if cursor:
                cursor.close()
            if con:
                DBUtils.close_connection(con)

    @staticmethod
    def eq_stop(eq_code, equipment, ip, port, sub_url):
        """
        修改设备状态
        """
        result_dict = {
            0: {
                'code': BaseHttpStatus.ERROR.value,
                'msg': '更新失败',
                'data': {}
            },
            1: {
                'code': BaseHttpStatus.OK.value,
                'msg': '更新成功',
                'data': {}
            },
            2: {
                'code': ConfigHttpStatus.TOO_MANY_PROJECT.value,
                'msg': '多条设备状态被修改',
                'data': {}
            }
        }
        # try:
        #     data = request.json
        #     control_code = data.get('ConEquipCode')
        # except Exception as e:
        #     return jsonify(
        #         {'code': BaseHttpStatus.EXCEPTION.value, 'msg': '初始化失败', 'data': {'exception': str(e)}}), 200

        if not all([eq_code, equipment, ip, sub_url]):
            return {'code': BaseHttpStatus.PARAMETER.value, 'msg': '缺少必要的字段', 'data': {}}

        # 设备 IP 是否在线
        if not ConfUtils.ip_is_online(ip, port=port):
            return {'code': ConfigHttpStatus.NO_EXIST.value, 'msg': '设备不在线', 'data': {}}

        con = None
        cursor = None
        try:
            dbu = DBUtils()
            con = dbu.connection(cursor_class=DictCursor)
            cursor = con.cursor()
            con.autocommit(False)

            parameters = EQUIPMENT_PARAMETER.get(equipment)
            table_name = parameters.get('table_name')
            table_name_conf = parameters.get('table_name_conf')
            column_status = parameters.get('column_status')
            column_code = parameters.get('column_code')
            column_queue = parameters.get('column_queue')
            column_username = parameters.get('column_username')
            column_password = parameters.get('column_password')
            column_host = parameters.get('column_host')
            column_port = parameters.get('column_port')
            column_vh = parameters.get('column_vh')
            column_binging_key = parameters.get('column_binging_key')

            # 验证 设备code 是否存在
            code_sql = f"SELECT * From {table_name} WHERE {column_code} = {eq_code}"
            res = DBUtils.project_is_exist(cursor, code_sql, ConfigHttpStatus.NO_FIND_CODE.value, "该设备不存在")
            if res:
                return res, 200

            # 修改设备状态
            update_sql = f"UPDATE {table_name} SET {column_status} = 0 WHERE {column_code} = {eq_code}"
            rows = cursor.execute(update_sql)

            res = DBUtils.kv(rows, result_dict)
            if res.get('code') != 101:
                return {'code': BaseHttpStatus.EXCEPTION.value, 'msg': '多条记录被修改或未发生改变', 'data': {}}

            # 远程停止设备工作
            url = f"http://{ip}:{port}/{sub_url}/stop"
            headers = {
                'Content-Type': 'application/json'
            }
            data = {}
            response = requests.post(url, json=data, headers=headers)
            if response.json().get('code') != 101:
                raise Exception(str(response.json()))

            # TODO: 停止监听队列
            select_queue = f"""
                        SELECT 
                        {column_queue}, {column_username}, {column_password}, {column_host}, {column_port}, {column_vh}, {column_binging_key}
                        FROM {table_name_conf} 
                        WHERE {column_code} = %s
                        """
            cursor.execute(select_queue, eq_code)
            select_queue_res = cursor.fetchone()
            queue_name = select_queue_res.get(column_queue)
            username = select_queue_res.get(column_username)
            password = select_queue_res.get(column_password)
            host = select_queue_res.get(column_host)
            port = select_queue_res.get(column_port)
            vh = select_queue_res.get(column_vh)
            bk = select_queue_res.get(column_binging_key)

            send_queue_info2monitor(eq_code, queue_name, 'stop', equipment, username, password, host, port, vh, bk)

            con.commit()
            return {'code': BaseHttpStatus.OK.value, 'msg': '停止成功', 'data': {}}
        except Exception as e:
            if con:
                con.rollback()
            return {'code': BaseHttpStatus.EXCEPTION.value, 'msg': '停止失败', 'data': {'exception': str(e)}}
        finally:
            if cursor:
                cursor.close()
            if con:
                DBUtils.close_connection(con)

    @staticmethod
    def delete(eq_code, eq_table_name, conf_table_name, code_column, control_ip, port, sub_url):
        """
        删除配置内容
        """
        result_dict = {
            0: {
                'code': ConfigHttpStatus.NO_FIND_CODE.value,
                'msg': '删除失败，待删除的设备配置项不存在',
                'data': ''
            },
            1: {
                'code': BaseHttpStatus.OK.value,
                'msg': '删除成功',
                'data': ''
            },
            2: {
                'code': ConfigHttpStatus.TOO_MANY_PROJECT.value,
                'msg': '太多设备信息被删除',
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
        # try:
        #     data = request.json
        #     control_code = data.get('ConEquipCode')
        # except Exception as e:
        #     return jsonify(
        #         {'code': BaseHttpStatus.EXCEPTION.value, 'msg': '初始化失败', 'data': {'exception': str(e)}}), 200

        if not all([eq_code, eq_table_name, conf_table_name, code_column, control_ip, port, sub_url]):
            return jsonify({'code': BaseHttpStatus.PARAMETER.value, 'msg': '缺少必要的字段', 'data': {}})

        con = None
        cursor = None
        try:
            dbu = DBUtils()
            con = dbu.connection()
            cursor = con.cursor()
            con.autocommit(False)

            # 验证 设备code 是否存在
            code_sql = f"SELECT * From {eq_table_name} WHERE {code_column} = {eq_code}"
            res = DBUtils.project_is_exist(cursor, code_sql, ConfigHttpStatus.NO_FIND_CODE.value, "该设备不存在")
            if res:
                return jsonify(res)

            delete_sql = f"DELETE FROM {conf_table_name} WHERE {code_column} = {eq_code}"
            rows = cursor.execute(delete_sql)

            res = DBUtils.kv(rows, result_dict)
            if rows != 1:
                print(rows)
                # if res.get('code') != 101:
                return jsonify(
                    {'code': BaseHttpStatus.EXCEPTION.value, 'msg': '多条记录被删除或没有记录被删除', 'data': {}})

            # 修改设备状态
            update_sql = f"UPDATE {eq_table_name} SET Init = 0 WHERE {code_column} = {eq_code}"
            update_rows = cursor.execute(update_sql)
            res = DBUtils.kv(update_rows, update_result_dict)
            if update_rows != 1:
                return jsonify(
                    {'code': BaseHttpStatus.EXCEPTION.value, 'msg': '多条记录被更新或没有记录被更新', 'data': {}})

            # TODO: 远程删除设备配置文件
            avia_url = f"http://{control_ip}:{port}/{sub_url}/deleteConfig"
            headers = {
                'Content-Type': 'application/json'
            }
            data = {}
            response = requests.post(avia_url, json=data, headers=headers)
            if response.json().get('code') != 101:
                return response.json(), 200

            con.commit()
            return jsonify({'code': BaseHttpStatus.OK.value, 'msg': '删除成功', 'data': {}})
        except Exception as e:
            if con:
                con.rollback()
            return jsonify(
                {'code': BaseHttpStatus.EXCEPTION.value, 'msg': '删除失败', 'data': {'exception': str(e)}})
        finally:
            if cursor:
                cursor.close()
            if con:
                DBUtils.close_connection(con)


if __name__ == '__main__':
    # print(ConfUtils.ip_is_online('192.168.1.10'))

    print(ConfUtils.eq_start(1001, '192.168.1.8', 'control', 7023, 'api/inner/control_config'))
    # print(ConfUtils.eq_stop(1001, 'control', '192.168.1.8', 7023, 'api/inner/control_config'))

    # print(ConfUtils.delete('1001', 'eq_data', 'eq_data_conf', 'ConEquipCode', '192.168.1.8', '7023',
    #                        'api/inner/control_config'))

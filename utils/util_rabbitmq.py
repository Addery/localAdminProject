"""
@Author: zhang_zhiyi
@Date: 2024/10/11_10:55
@FileName:util_rabbitmq.py
@LastEditors: zhang_zhiyi
@version: 1.0
@lastEditTime: 
@Description: rabbitmq操作工具类
"""
import json
import os

import numpy as np
import pandas as pd
import pika
from open3d.cpu.pybind.geometry import PointCloud
from pandas import DataFrame


def get_line(path) -> int:
    """
    获得csv文件行数
    :return:
    """
    try:
        data = pd.read_csv(path)
        return len(data)
    except Exception as e:
        print(f"Error reading the file: {e}")
        return 0


def get_all_file_line_length(file_path):
    """
    获取当前路径中所有.csv文件的行数和，不包括列名所在行
    :param file_path:
    :return:
    """
    count = 0  # 记录时序数据的长度
    # 遍历目录构建完整的时序数据
    with os.scandir(file_path) as entries:
        for entry in entries:
            if entry.is_file() and entry.name.endswith('.csv'):
                count += get_line(entry.path)
    return count


def is_init(init_count: int, file_path):
    """
    判断当前是否在初始化阶段
    :param init_count: 时序数据长度，判断是否在初始化阶段
    :param file_path: 时序数据所在路径
    :return: 返回True说明，在初始化阶段
    """
    return True if (get_all_file_line_length(file_path) - init_count) < 0 else False


def pcd2df(pcd: PointCloud) -> DataFrame:
    """
    将PointCloud数据转化为DataFrame格式
    :param pcd: PointCloud
    :return: DataFrame
    """
    points = np.asarray(pcd.points)
    colors = np.asarray(pcd.colors) if pcd.colors else None
    normals = np.asarray(pcd.normals) if pcd.normals else None
    # print(points, colors, normals)
    # print(type(points))  # <class 'numpy.ndarray'>

    data = {
        'X': points[:, 0],
        'Y': points[:, 1],
        'Z': points[:, 2]
    }

    if colors is not None:
        data['R'] = colors[:, 0]
        data['G'] = colors[:, 1]
        data['B'] = colors[:, 2]

    if normals is not None:
        data['NX'] = normals[:, 0]
        data['NY'] = normals[:, 1]
        data['NZ'] = normals[:, 2]

    return pd.DataFrame(data)


def find_max_folder(directory):
    """
    找到文件名称最大的文件
    :param directory:
    :return:
    """
    try:
        filename_list = []
        with os.scandir(directory) as entries:
            for entry in entries:
                if entry.is_file() and entry.name.endswith('.csv'):
                    filename_list.append(entry.name)
        if not filename_list:  # 如果文件列表为空
            return None, None
        max_csv_name = max(filename_list)
        return os.path.join(directory, max_csv_name), max_csv_name
    except Exception as e:
        print(str(e))
        return None, None


def compare_df_len(df1: DataFrame, df2: DataFrame):
    """
    比较两个DataFrame数据的列名
    :param df1: 时序文件中的数据
    :param df2: 新的数据
    :return:
    """
    df1_columns, df2_columns = df1.columns, df2.columns
    df1_columns_len, df2_columns_len = len(df1_columns), len(df2_columns)
    if df1_columns_len != df2_columns_len:
        df2_modify = df2.reindex(columns=df1_columns)
        return df2_modify
    return df2


def send_queue_info2monitor(eq_code, queue_name, status, equipment, username, password, host, port, vh, bing_key):
    """
    向PC监听队列发送队列
    :param eq_code: 设备code
    :param queue_name: 将要操作的队列
    :param status: 将要设置的状态
    :param equipment: 总控设备 or 采集设备
    :param username:
    :param password:
    :param host:
    :param port:
    :param vh:
    :param bing_key:
    :return:
    """
    try:
        monitor_queue_name = 'control.pc.monitor.queue'
        data = {
            'queues': {queue_name: status}
        }
        # monitor_queue_name 根据设备调整，总控对应唯一的PC队列，采集设备根据总控编号对应队列
        if equipment == 'data':
            monitor_queue_name = f'avia.control.{eq_code}.monitor.queue'
            data = {
                'queues': {f'{queue_name}_{bing_key}': status}
            }

        credentials = pika.PlainCredentials(username=username, password=password)
        parameters = pika.ConnectionParameters(host=host, port=port,
                                               virtual_host=vh,
                                               credentials=credentials)
        conn = pika.BlockingConnection(parameters)
        ch = conn.channel()

        # 确保队列存在
        ch.queue_declare(
            queue=monitor_queue_name,
            durable=True,
            arguments={
                'x-queue-mode': 'lazy'  # 设置队列为惰性模式
            }
        )

        ch.basic_publish(
            exchange='',
            routing_key=monitor_queue_name,
            body=json.dumps(data)
        )
        return True
    except Exception as e:
        return False

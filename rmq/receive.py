"""
@Author: zhang_zhiyi
@Date: 2024/7/26_10:04
@FileName:receive.py
@LastEditors: zhang_zhiyi
@version: 1.0
@lastEditTime: 
@Description: 
"""
import base64
import configparser
import json
import os.path
import pickle
import threading

import pika
import requests

from utils.util_database import DBUtils
from utils.util_pcd import write_init, write_single_df, write_single_log, recreate_init_file, write_single_log_db
from construct import Tunnel


def init_process(init: bool, data: Tunnel, init_path, init_name, region_name):
    """
    初始化阶段只保存原始数据，不写入日志，不提供历史数据
    :param init: 是否处于初始化阶段
    :param data: 隧道实例
    :param init_path:
    :param init_name:
    :param region_name:
    :return:
    """
    point_cloud = data.get_data()

    recreate_init_file(init_path)
    print("init pcd save success") if write_init(init_path, init, point_cloud, init_name, region_name) else print(
        "init pcd save error")


# def process(init, time, tunnel: Tunnel, data_path, log_path, init_path):
def process(init, tunnel: Tunnel, data_path, init_path):
    """
    非初始化阶段，某时刻第一个数据记录完整的预处理后的数据，后面的只保存异常数据和日志信息
    解码并反序列化数据 config = [is_init(4), now, merge_clouds]
        is_init(4)表示是否在初始化阶段 bool类型
        now本次数据采集的起始时间 datetime类型

        merge_clouds[Merge对象]
        Merge中包含Tunnel对象
        Tunnel中包含：隧道的实际高度 和 PointCloudData点云数据对象
        PointCloudData中包含：DataFrame点云数据、预处理后的DataFrame点云数据、regions区域点云列表、AnomalyPointCloudData异常点云对象
    """
    print("pcd save success!") if write_single_df(data_path, init_path, init, tunnel) else print(
        "pcd save error!")

    # 记录日志至本地文件
    # print("log save success!") if write_single_log(time, log_path, point_cloud) else print("log save error!")
    # 记录日志至本地数据库
    res = write_single_log_db(tunnel)
    if res is None:
        print('无异常')
    elif res:
        print("log save success!")
    else:
        print("log save error!")


class Queue(object):
    """
    用于监听总控设备状态队列的队列
    """
    CONFIG_PATH = '../config/receive.ini'

    def __init__(self):
        config = configparser.ConfigParser()
        config.read(Queue.CONFIG_PATH)
        self._username = str(config.get("Receive", "username"))
        self._password = str(config.get("Receive", "password"))
        self._host = str(config.get("Receive", "host"))
        self._port = int(config.get("Receive", "port"))
        self._virtual_host = str(config.get("Receive", "virtualHost"))
        self._queue = str(config.get("Receive", "queueName"))

    @property
    def username(self) -> str:
        return self._username

    @property
    def password(self) -> str:
        return self._password

    @property
    def host(self) -> str:
        return self._host

    @property
    def port(self) -> int:
        return self._port

    @property
    def virtual_host(self) -> str:
        return self._virtual_host

    @property
    def queue(self) -> str:
        return self._queue


class ReceiveThread(object):
    """
    数据传输队列
    """
    # PATH = "../../config/history"
    # COMPARE = "../../config/compare"
    # LOG = "../../config/log"
    # INIT_DATA_PATH = "../../config/init"
    INIT_DATA_PATH = "../data"
    INIT_ALL_DATA_NAME = "init.csv"
    INIT_REGIONS_NAME = "regions"

    def __init__(self):
        q = Queue()
        self.username = q.username
        self.password = q.password
        self.host = q.host
        self.port = q.port
        self.virtual_host = q.virtual_host
        self.queue = q.queue
        self.init = ReceiveThread.INIT_DATA_PATH
        self.init_all_data = ReceiveThread.INIT_ALL_DATA_NAME
        self.init_regions_name = ReceiveThread.INIT_REGIONS_NAME

    def run(self, queue_name, stop_event_dict):
        """
        开启对指定消息传输队列的监听操作
        :param queue_name:
        :param stop_event_dict:
        :return:
        """
        # 创建PlainCredentials实例
        credentials = pika.PlainCredentials(username=self.username, password=self.password)
        parameters = pika.ConnectionParameters(host=self.host, port=self.port, virtual_host=self.virtual_host,
                                               credentials=credentials)
        # 连接到RabbitMQ服务器
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        # 声明队列，如果队列不存在则创建队列
        channel.queue_declare(
            queue=queue_name,
            durable=True,
            arguments={
                'x-queue-mode': 'lazy'  # 设置队列为惰性模式
            }
        )

        # 定义回调函数，处理从队列中接收到的消息
        def callback(ch, method, properties, body):
            """
            接收数据进行处理并保存至本地和云端

            初始化阶段只保存原始的完整点云数据，和预处理后的点云区域数据
            非初始化保存异常点云区域数据和日志信息
            :param ch:
            :param method:
            :param properties:
            :param body:
            :return:
            """
            if not body:  # 如果body没有数据关闭channel
                print("no body")
            else:
                print("receive data success!!")
                print("saving data......")
                # 解码并反序列化数据 message_data = [is_init(4), now, merge_clouds]
                decode = base64.b64decode(body)
                message_data = pickle.loads(decode)
                """------------本地部分------------"""
                # TODO: 写入数据库 log表
                # TODO: 向公众号定向推送 log表
                # TODO: 保存本地数据 点云数据文件 再上传云端

                # 获取数据
                init, time, tunnel = message_data

                # 构建项目保存目录
                # project_name, tunnel_name, working_face = tunnel.project_name, tunnel.tunnel_name, tunnel.working_face
                # structure, device_id, mileage = tunnel.structure, tunnel.device_id, tunnel.mileage
                device_id = tunnel.project.get('device_id')
                # init_path = str(
                #     os.path.join(self.init, project_name, tunnel_name, working_face, mileage, device_id, 'data',
                #                  'init'))
                init_path = str(os.path.join(self.init, device_id, 'data', 'init'))
                data_path = str(os.path.join(self.init, device_id, 'data', 'history'))

                # log_path = str(
                #     os.path.join(self.init, project_name, tunnel_name, working_face, mileage, device_id, 'data',
                #                  'log'))

                # init_process(init, tunnel, init_path, self.init_all_data, self.init_regions_name) if message_data[
                #     0] else process(init, time, tunnel, data_path, log_path, init_path)

                init_process(init, tunnel, init_path, self.init_all_data, self.init_regions_name) if message_data[
                    0] else process(init, tunnel, data_path, init_path)

                """------------云端部分------------"""
                """
                Influxdb:
                    organization: project_name
                    bucket: tunnel_name
                    tag: working_face = device_id
                    filed: region_index = z-score
                """
                # TODO：点云数据压缩备份云端
                # TODO：时序数据上传云端

        # 告诉RabbitMQ使用callback来接收消息
        channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

        print(f' [{queue_name}] Waiting for messages. To exit press CTRL+C')

        while not stop_event_dict[queue_name].is_set():
            # 非阻塞地处理消息，每1秒检查一次
            channel.connection.process_data_events(time_limit=1)

        print(f"Stopped consuming from {queue_name}")
        channel.close()
        connection.close()
        # 开始接收消息，并进入阻塞状态
        # channel.start_consuming()


class Receive(object):
    """
    接受主类
    """

    def __init__(self):
        self._queue = Queue()
        self._threads_dict = {}
        self._stop_event_dict = {}

    @property
    def queue(self):
        return self._queue

    @property
    def threads_dict(self):
        return self._threads_dict

    @threads_dict.setter
    def threads_dict(self, value):
        k, v = value
        self._threads_dict[k] = v

    @property
    def stop_event_dict(self):
        return self._stop_event_dict

    @stop_event_dict.setter
    def stop_event_dict(self, value):
        k, v = value
        self._stop_event_dict[k] = v

    def start_or_stop_queue(self, queue_name, status):
        """
        这里对数据传输队列进行线程管理
        TODO：
            1. 判断线程状态 √
            2. 启停线程 √
        :param queue_name:
        :param status:
        :return:
        """
        if status == 'start':
            if queue_name not in self.threads_dict or not self.threads_dict[queue_name].is_alive():
                # 如果队列没有启动，或者线程已停止，启动新的消费者线程
                self.stop_event_dict = queue_name, threading.Event()
                thread = threading.Thread(target=ReceiveThread().run, args=(queue_name, self.stop_event_dict))
                thread.start()
                self.threads_dict = queue_name, thread
                print(f"Started config queue: {queue_name}")
            else:
                print(f"Queue {queue_name} is already running.")

        elif status == 'stop':
            if queue_name in self.stop_event_dict:
                print(f"Requesting stop for config queue: {queue_name}")
                self.stop_event_dict[queue_name].set()  # 设置停止标志
                thread = self.threads_dict.get(queue_name)
                if thread and thread.is_alive():
                    thread.join()  # 等待线程安全退出
                print(f"Data queue {queue_name} has been stopped.")
            else:
                print(f"Queue {queue_name} is not running.")

    def run(self):
        def callback(ch, method, properties, body):
            if not body:
                print("no body")
            else:
                print("receiving queues and status")
                message = json.loads(body)
                queues = message.get('queues', None)
                if queues is not None:
                    print("starting listening to queues in messages")
                    for k, v in queues.items():
                        self.start_or_stop_queue(k, v)
                    print("starting listening to queues in messages, success")

        q = self.queue
        # 创建PlainCredentials实例
        credentials = pika.PlainCredentials(username=q.username, password=q.password)
        parameters = pika.ConnectionParameters(host=q.host, port=q.port, virtual_host=q.virtual_host,
                                               credentials=credentials)
        # 连接到RabbitMQ服务器
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()

        # 声明队列，如果队列不存在则创建队列
        channel.queue_declare(
            queue=q.queue,
            durable=True,
            arguments={
                'x-queue-mode': 'lazy'  # 设置队列为惰性模式
            }
        )

        # 告诉RabbitMQ使用callback来接收消息
        channel.basic_consume(queue=q.queue, on_message_callback=callback, auto_ack=True)

        print(f' [{q.queue}] Waiting for messages. To exit press CTRL+C')

        # 开始接收消息，并进入阻塞状态
        channel.start_consuming()


if __name__ == '__main__':
    receive = Receive()
    receive.run()

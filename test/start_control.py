"""
@Author: zhang_zhiyi
@Date: 2025/5/9_15:40
@FileName:start_control.py
@LastEditors: zhang_zhiyi
@version: 1.0
@lastEditTime: 
@Description: 模拟启动总控设备时向 control.pc.monitor.queue 发送队列信息
"""
import json

import pika

username = 'tunnel'
password = '123456'
host = '192.168.1.8'
port = '5672'
virtual_host = 'tunnel_vh'
queue_name = 'control.pc.monitor.queue'

data = {
    'queues': {
        'queuename': 'start'
    }
}

credentials = pika.PlainCredentials(username=username, password=password)
parameters = pika.ConnectionParameters(host=host, port=port,
                                       virtual_host=virtual_host,
                                       credentials=credentials)
conn = pika.BlockingConnection(parameters)
ch = conn.channel()

# 确保队列存在
ch.queue_declare(
    queue=queue_name,
    durable=True,
    arguments={
        'x-queue-mode': 'lazy'  # 设置队列为惰性模式
    }
)

ch.basic_publish(exchange='', routing_key=queue_name, body=json.dumps(data))

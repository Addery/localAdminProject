"""
@Author: zhang_zhiyi
@Date: 2025/5/13_14:12
@FileName:send_msg.py
@LastEditors: zhang_zhiyi
@version: 1.0
@lastEditTime: 
@Description: 
"""
import json
import pika


def send_msg():
    credentials = pika.PlainCredentials(username='security', password='123456')
    parameters = pika.ConnectionParameters(host='120.55.165.138', port=5672,
                                           virtual_host='security_vh',
                                           credentials=credentials)
    conn = pika.BlockingConnection(parameters)
    ch = conn.channel()

    # 声明交换机
    ch.exchange_declare(exchange='Mxdmo', exchange_type='fanout', durable=True)

    ch.basic_publish(
        exchange='Mxdmo',
        routing_key='',
        body=json.dumps(
            {
                'data': 'hello fanout exchange'
            }
        )
    )
    print('send success')


if __name__ == "__main__":
    send_msg()

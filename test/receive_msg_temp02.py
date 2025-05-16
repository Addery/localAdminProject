"""
@Author: zhang_zhiyi
@Date: 2025/5/13_14:18
@FileName:receive_msg_temp01.py
@LastEditors: zhang_zhiyi
@version: 1.0
@lastEditTime: 
@Description: 
"""
import pika


def receive_msg():
    credentials = pika.PlainCredentials(username='security', password='123456')
    parameters = pika.ConnectionParameters(host='120.55.165.138', port=5672,
                                           virtual_host='security_vh',
                                           credentials=credentials)
    conn = pika.BlockingConnection(parameters)
    ch = conn.channel()

    # 创建临时队列
    result = ch.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue

    # 声明交换机
    ch.exchange_declare(exchange='Mxdmo', exchange_type='fanout', durable=True)
    # ch.exchange_declare(exchange='test.topic', exchange_type='topic', durable=True)

    # 绑定交换机
    ch.queue_bind(exchange='Mxdmo', queue=queue_name)

    print('[*] Waiting for messages. To exit press CTRL+C')

    # 5. 回调函数：接收到消息时执行
    def callback(ch, method, properties, body):
        print(f"[x] Received: {body.decode()}")

    # 6. 开始消费
    ch.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

    ch.start_consuming()


if __name__ == '__main__':
    receive_msg()

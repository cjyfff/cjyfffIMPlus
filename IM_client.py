#! /usr/bin/env python
#coding=utf-8

import pika
import os
import time
import json
from uuid import uuid4

EXCHANGE_NAME = 'CJYFFFIM'


class SendOnlineMsg(object):

    def __init__(self, connection, msg):
        self.connection = connection
        self.msg = msg
        self.user_id = self.msg['user_id']
        self.channel = self.connection.channel()
        self.client_list = None

        #定义接收返回消息的队列
        self.channel.exchange_declare(exchange=EXCHANGE_NAME, type='direct')
        self.channel.queue_declare(queue='user_q')
        self.channel.queue_bind(exchange=EXCHANGE_NAME, queue='user_q', routing_key=self.user_id)
        self.channel.basic_consume(self.on_response,
                                   no_ack=True,
                                   queue='user_q')

    #定义接收到返回消息的处理方法
    def on_response(self, ch, method, props, body):
        self.client_list = body

    def run(self):
        #发送广播信息
        online_msg = self.msg
        online_msg.update({'created_at': time.time()})
        online_msg = json.dumps(online_msg)
        self.channel.exchange_declare(exchange=EXCHANGE_NAME, type='direct')
        self.channel.basic_publish(exchange=EXCHANGE_NAME,
                                   routing_key='server',
                                   properties=pika.BasicProperties(
                                         reply_to=self.user_id,
                                         ),
                                   body=online_msg)
        #接收返回的数据
        while self.client_list is None:
            self.connection.process_data_events()
        return self.client_list

connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
username = os.environ['USER']
user_id = uuid4().hex
online_msg = {
    'type': 'online',
    'from': username,
    'user_id': user_id,
    'from_ip': '192.168.1.101',
    'destination': '',
    'destination_ip': '192.168.1.111',  # server's ip
    'created_at': 0,
    'message': '',
}

send_online_msg = SendOnlineMsg(connection, online_msg)

client_list = send_online_msg.run()
print " [.] Got %s" % client_list

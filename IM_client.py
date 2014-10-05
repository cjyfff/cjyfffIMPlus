#! /usr/bin/env python
#coding=utf-8

import pika
import os
import time
import json
import threading
import copy
from uuid import uuid4

EXCHANGE_NAME = 'CJYFFFIM'


class SendOnlineMsg(object):

    def __init__(self, connection, msg):
        self.connection = connection
        self.msg = copy.deepcopy(msg)
        self.user_id = self.msg['user_id']
        self.channel = self.connection.channel()
        self.client_list = None

        #定义接收上线反馈消息的队列
        self.channel.exchange_declare(exchange=EXCHANGE_NAME, type='direct')
        self.channel.queue_declare(queue='user_q')
        self.channel.queue_bind(exchange=EXCHANGE_NAME, queue='user_q', routing_key=self.user_id)
        self.channel.basic_consume(self.on_response,
                                   no_ack=True,
                                   queue='user_q')

    #定义接收到上线反馈消息的处理方法
    def on_response(self, ch, method, props, body):
        self.client_list = body
        print "client35", self.client_list

    def run(self):
        online_msg = self.msg
        online_msg.update({'created_at': int(time.time())})
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


class SendNormalMsg(object):

    def __init__(self, msg, quit_msg):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        self.msg = copy.deepcopy(msg)
        self.quit_msg = copy.deepcopy(quit_msg)
        self.user_id = self.msg['user_id']
        self.channel = self.connection.channel()

    def send_quit_msg(self):
        # send to server
        self.quit_msg.update({'created_at': int(time.time())})
        self.channel.exchange_declare(exchange=EXCHANGE_NAME, type='direct')
        self.channel.basic_publish(exchange=EXCHANGE_NAME,
                                   routing_key='server',
                                   body=json.dumps(self.quit_msg))

        # send to itself
        self.quit_msg.update({'type': 'self_offline'})
        self.channel.exchange_declare(exchange=EXCHANGE_NAME, type='direct')
        self.channel.basic_publish(exchange=EXCHANGE_NAME,
                                   routing_key=self.user_id,
                                   body=json.dumps(self.quit_msg))
        print "client77, send all quit msg"

    def run(self):
        while 1:
            msg = raw_input("> ")
            if msg in ['quit', 'exit']:
                self.send_quit_msg()
                break
            normal_msg = self.msg
            normal_msg.update({
                'created_at': int(time.time()),
                'message': msg,
            })
            normal_msg = json.dumps(normal_msg)
            self.channel.exchange_declare(exchange=EXCHANGE_NAME, type='direct')
            self.channel.basic_publish(exchange=EXCHANGE_NAME,
                                   routing_key='server',
                                   body=normal_msg)
        print "send quit"


class ReciveMsg(object):

    def __init__(self, msg, connection):
        self.connection = connection
        self.msg = msg
        self.user_id = self.msg['user_id']
        self.channel = self.connection.channel()
        self.channel.exchange_declare(exchange=EXCHANGE_NAME, type='direct')
        self.channel.queue_declare(queue='user_q')
        self.channel.queue_bind(exchange=EXCHANGE_NAME,
                                queue='user_q',
                                routing_key=self.user_id)

    def on_response(self, body):
        print body

    def run(self):
        self.channel.basic_qos(prefetch_count=1)
        for method_frame, properties, body in self.channel.consume('user_q'):
            self.on_response(body)
            self.channel.basic_ack(method_frame.delivery_tag)

            # Escape out of the loop after 10 messages
            print "in receive"
            if 0:
                break
        print "receive quit"


class MyThread(threading.Thread):
    '''Factory of new threads'''

    def __init__(self, func, args, name=''):
        threading.Thread.__init__(self)
        self.name = name
        self.func = func
        self.args = args

    def run(self):
        apply(self.func, self.args)


username = os.environ['USER']
user_id = uuid4().hex
online_msg = {
    'type': 'online',
    'from': username,
    'user_id': user_id,
    'created_at': 0,
    'message': '',
}

normal_msg = {
    'type': 'normal',
    'from': username,
    'user_id': user_id,
    'destination': 'myself',
    'destination_id': 1,
    'created_at': '',
    'message': '',
}

quit_msg = {
    'type': 'offline',
    'from': username,
    'user_id': user_id,
    'created_at': '',
    'message': '',
}


# 发送上线消息
connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
send_online_msg = SendOnlineMsg(connection, online_msg)
send_online_msg.run()


send_normal_msg = SendNormalMsg(normal_msg, quit_msg)
recive_msg = ReciveMsg(normal_msg, connection)
threads = []
t1 = MyThread(send_normal_msg.run, (), )
threads.append(t1)
t2 = MyThread(recive_msg.run, (), )
threads.append(t2)

for t in threads:
    t.setDaemon(True)
    t.start()
t1.join()
connection.close()

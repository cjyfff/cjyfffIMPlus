#! /usr/bin/env python
#coding=utf-8

import pika


class SendOnlineMsg(object):

    def __init__(self, connection):
        self.connection = connection
        self.channel = self.connection.channel()
        self.client_list = None

        #定义接收返回消息的队列
        self.channel.exchange_declare(exchange='test', type='direct')
        self.channel.queue_declare(queue='jackson_q')
        self.channel.queue_bind(exchange='test', queue='jackson_q', routing_key='jackson')
        self.channel.basic_consume(self.on_response,
                                   no_ack=True,
                                   queue='jackson_q')

    #定义接收到返回消息的处理方法
    def on_response(self, ch, method, props, body):
        self.client_list = body

    def run(self):
        #发送计算请求，并声明返回队列
        self.channel.exchange_declare(exchange='test', type='direct')
        self.channel.basic_publish(exchange='test',
                                   routing_key='server',
                                   properties=pika.BasicProperties(
                                         reply_to='jackson',
                                         ),
                                   body='abc')
        #接收返回的数据
        while self.client_list is None:
            self.connection.process_data_events()
        return self.client_list

connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))

send_online_msg = SendOnlineMsg(connection)

client_list = send_online_msg.run()
print " [.] Got %s" % client_list
